"""Comprehensive test suite for Task 9: Two-Tier Memory System + Security Controls.

Verifies all requirements from Assignment 2 PDF and the Task 9 Master Plan:
- Group A: Student Authentication (JWT, bcrypt, Option A enrollment checks)
- Group B: Two-Tier Memory (Redis cache, PostgreSQL durable store, hybrid extraction, privacy filter)
- Group C: Security Controls (Code-level authorization, cross-student blocking, approval gates, audit logging)
"""

import asyncio
from datetime import timedelta
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, delete

from app.config.database import AsyncSessionLocal
from app.exceptions.custom_exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.main import app
from app.memory import MemoryManager, PostgresMemoryStore, RedisMemoryStore
from app.models.audit_log import AuditLog
from app.models.auth_credentials import AuthCredentials
from app.models.student_records import Student
from app.schemas.approval_schema import ApprovalStatus
from app.schemas.auth_schema import LoginRequest, SignupRequest
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService, log_audit_event
from app.services.auth_service import (
    AuthService,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.tools.fee_tool import get_fee_status
from app.tools.scholarship_tool import check_scholarship
from app.tools.ticket_tool import create_support_ticket
from app.utils.ownership import check_ownership


# ============================================================================
# GROUP A: Authentication & JWT Tests
# ============================================================================

@pytest.mark.asyncio
async def test_01_signup_with_enrolled_student_option_a():
    """Verify signup succeeds for an enrolled student without existing credentials."""
    async with AsyncSessionLocal() as session:
        # Create a temporary student record for test isolation
        test_id = "STU990"
        await session.execute(delete(AuthCredentials).where(AuthCredentials.student_id == test_id))
        await session.execute(delete(Student).where(Student.student_id == test_id))

        new_student = Student(
            student_id=test_id,
            name="Test Student",
            programme="PGDM",
            batch="2025-27",
            status="Enrolled",
        )
        session.add(new_student)
        await session.commit()

        # Run signup
        auth_service = AuthService(session)
        res = await auth_service.signup(SignupRequest(student_id=test_id, password="SecurePassword123!"))
        assert res["student_id"] == test_id
        assert "successfully" in res["message"]


@pytest.mark.asyncio
async def test_02_signup_non_existent_student_rejected():
    """Verify Option A policy: non-enrolled students cannot register."""
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        with pytest.raises(ResourceNotFoundError) as exc:
            await auth_service.signup(SignupRequest(student_id="NON_EXISTENT_ID", password="Password123!"))
        assert "not enrolled" in str(exc.value)


@pytest.mark.asyncio
async def test_03_signup_duplicate_credentials_conflict():
    """Verify attempting to register an already-registered student raises ConflictError (409)."""
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        # STU001 is already seeded
        with pytest.raises(ConflictError) as exc:
            await auth_service.signup(SignupRequest(student_id="STU001", password="NewPassword123!"))
        assert "already exists" in str(exc.value)


@pytest.mark.asyncio
async def test_04_login_valid_credentials():
    """Verify valid credentials return a signed JWT token."""
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        token_res = await auth_service.login(LoginRequest(student_id="STU001", password="Student@123"))
        assert token_res.access_token
        assert token_res.token_type == "bearer"
        assert token_res.expires_in > 0


@pytest.mark.asyncio
async def test_05_login_invalid_password():
    """Verify login with incorrect password raises AuthenticationError (401)."""
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        with pytest.raises(AuthenticationError):
            await auth_service.login(LoginRequest(student_id="STU001", password="WrongPassword!"))


def test_06_jwt_token_encode_decode():
    """Verify JWT encodes and decodes the student_id claim accurately."""
    token = create_access_token("STU002")
    decoded_id = decode_access_token(token)
    assert decoded_id == "STU002"


def test_07_jwt_expired_token_rejected():
    """Verify expired token raises AuthenticationError."""
    expired_token = create_access_token("STU001", expires_delta=timedelta(seconds=-10))
    with pytest.raises(AuthenticationError) as exc:
        decode_access_token(expired_token)
    assert "expired" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_08_protected_endpoints_via_http():
    """Verify protected /api/v1/auth/me behaves properly with missing and valid tokens."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Without token -> 401
        res_no_token = await client.get("/api/v1/auth/me")
        assert res_no_token.status_code == 401

        # With valid token -> 200
        token = create_access_token("STU001")
        res_auth = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res_auth.status_code == 200
        assert res_auth.json()["data"]["student_id"] == "STU001"


# ============================================================================
# GROUP B: Two-Tier Memory & Privacy Tests
# ============================================================================

def test_09_sensitivity_classifier_skips_sensitive():
    """Verify OTP, passwords, PINs, and card tokens are classified as 'skip'."""
    # Test classifier directly
    mgr = MemoryManager(session=None)
    assert mgr.classify_sensitivity("My secret OTP is 987654") == "skip"
    assert mgr.classify_sensitivity("password: myPassword123") == "skip"
    assert mgr.classify_sensitivity("ATM PIN 4321") == "skip"
    assert mgr.classify_sensitivity("Credit card number") == "skip"


def test_10_sensitivity_classifier_stores_academic_facts():
    """Verify safe academic information is classified as 'store'."""
    mgr = MemoryManager(session=None)
    assert mgr.classify_sensitivity("PGDM Big Data Analytics") == "store"
    assert mgr.classify_sensitivity("Batch 2025-27") == "store"
    assert mgr.classify_sensitivity("Interested in Artificial Intelligence") == "store"


def test_11_hybrid_regex_fact_extraction():
    """Verify regex slot matching extracts facts accurately with zero LLM tokens."""
    mgr = MemoryManager(session=None)
    text = "I am studying PGDM AI and DS in the 2025-27 batch. Call me Priya. Interested in Deep Learning."
    facts = mgr.extract_facts(text)
    fact_dict = {f.fact_key: f.fact_value for f in facts}

    assert fact_dict.get("programme") == "PGDM AI and DS"
    assert fact_dict.get("batch") == "2025-27"
    assert fact_dict.get("preferred_name") == "Priya"
    assert fact_dict.get("academic_goal") == "Deep Learning"


@pytest.mark.asyncio
async def test_12_redis_memory_store_roundtrip():
    """Verify RedisMemoryStore can set and retrieve facts."""
    redis_store = RedisMemoryStore()
    test_student = "STU_TEST_REDIS"
    await redis_store.set_facts_bulk(test_student, {"programme": "MBA", "batch": "2025-27"})
    facts = await redis_store.get_facts(test_student)

    assert facts.get("programme") == "MBA"
    assert facts.get("batch") == "2025-27"
    await redis_store.delete_facts(test_student)


@pytest.mark.asyncio
async def test_13_postgres_memory_store_idempotent_upsert():
    """Verify PostgresMemoryStore idempotent upserts (no duplicate rows)."""
    async with AsyncSessionLocal() as session:
        pg_store = PostgresMemoryStore(session)
        test_student = "STU_TEST_PG"

        # First insert
        await pg_store.upsert_fact(test_student, "academic_goal", "Machine Learning")
        facts_1 = await pg_store.get_facts_dict(test_student)
        assert facts_1["academic_goal"] == "Machine Learning"

        # Update same key (idempotent upsert)
        await pg_store.upsert_fact(test_student, "academic_goal", "Generative AI")
        facts_2 = await pg_store.get_facts_dict(test_student)
        assert facts_2["academic_goal"] == "Generative AI"

        # Cleanup
        await pg_store.delete_facts(test_student)


@pytest.mark.asyncio
async def test_14_memory_manager_load_and_warm_cache():
    """Verify load_memory backfills Redis cache from PostgreSQL on cache miss."""
    async with AsyncSessionLocal() as session:
        mgr = MemoryManager(session)
        test_student = "STU_TEST_WARM"

        # Ensure Redis is empty
        await mgr.redis_store.delete_facts(test_student)
        # Put fact in PostgreSQL durable store only
        await mgr.postgres_store.upsert_fact(test_student, "programme", "B.Tech CSE")

        # load_memory should hit PostgreSQL and warm up Redis
        prompt_str = await mgr.load_memory(test_student)
        assert "B.Tech CSE" in prompt_str

        # Redis should now be populated (warmed up)
        cached = await mgr.redis_store.get_facts(test_student)
        assert cached.get("programme") == "B.Tech CSE"

        # Cleanup
        await mgr.redis_store.delete_facts(test_student)
        await mgr.postgres_store.delete_facts(test_student)


@pytest.mark.asyncio
async def test_15_save_memory_filters_sensitive_data():
    """Verify sensitive items like OTP/password in user chat never persist to Redis or PG."""
    async with AsyncSessionLocal() as session:
        mgr = MemoryManager(session)
        test_student = "STU_TEST_FILTER"

        chat_text = (
            "I am studying PGDM AI. My batch is 2025-27. "
            "Please remember my secret OTP is 445566 and my password is secretPass."
        )

        saved = await mgr.save_memory(test_student, chat_text)
        saved_keys = [f.fact_key for f in saved]

        assert "programme" in saved_keys
        assert "batch" in saved_keys
        assert "otp" not in saved_keys
        assert "password" not in saved_keys

        # Check PostgreSQL
        pg_facts = await mgr.postgres_store.get_facts_dict(test_student)
        assert "otp" not in pg_facts
        assert "password" not in pg_facts

        # Check Redis
        redis_facts = await mgr.redis_store.get_facts(test_student)
        assert "otp" not in redis_facts
        assert "password" not in redis_facts

        # Cleanup
        await mgr.redis_store.delete_facts(test_student)
        await mgr.postgres_store.delete_facts(test_student)


# ============================================================================
# GROUP C: Assignment 2 Security Controls & Scenarios
# ============================================================================

def test_16_code_level_ownership_enforcement():
    """Verify check_ownership raises PermissionDeniedError when requesting != target."""
    # Same student -> allowed
    check_ownership("STU001", "STU001")
    check_ownership("stu001", "STU001")  # case-insensitive

    # Different student -> blocked
    with pytest.raises(PermissionDeniedError) as exc:
        check_ownership("STU001", "STU002")
    assert "not authorized" in str(exc.value)


@pytest.mark.asyncio
async def test_17_own_fee_inquiry_allowed_and_audited():
    """Scenario 1 from PDF: Logged-in student asks for own fee -> ALLOWED and audited."""
    res = await get_fee_status(student_id="STU001", requesting_student_id="STU001")
    assert "Rahul Sharma" in res
    assert "Total Tuition Fee" in res

    # Verify audit log recorded ALLOWED
    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            select(AuditLog)
            .where(AuditLog.student_id == "STU001")
            .where(AuditLog.action == "fee_tool")
            .order_by(AuditLog.created_at.desc())
        )
        audit_entry = audit_res.scalars().first()
        assert audit_entry is not None
        assert audit_entry.decision == "ALLOWED"


@pytest.mark.asyncio
async def test_18_cross_student_fee_inquiry_blocked_and_audited():
    """Scenario 2 from PDF: Logged-in student asks for another student's fee -> BLOCKED and audited."""
    res = await get_fee_status(student_id="STU002", requesting_student_id="STU001")
    assert "ACCESS DENIED" in res
    assert "not authorized" in res

    # Verify audit log recorded BLOCKED
    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            select(AuditLog)
            .where(AuditLog.student_id == "STU001")
            .where(AuditLog.action == "fee_tool")
            .where(AuditLog.decision == "BLOCKED")
            .order_by(AuditLog.created_at.desc())
        )
        audit_entry = audit_res.scalars().first()
        assert audit_entry is not None
        assert audit_entry.target_id == "STU002"
        assert audit_entry.decision == "BLOCKED"


@pytest.mark.asyncio
async def test_19_cross_student_scholarship_inquiry_blocked_and_audited():
    """Scenario 2 from PDF: Logged-in student asks for another student's scholarship -> BLOCKED and audited."""
    res = await check_scholarship(student_id="STU003", requesting_student_id="STU001")
    assert "ACCESS DENIED" in res
    assert "not authorized" in res

    # Verify audit log recorded BLOCKED
    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            select(AuditLog)
            .where(AuditLog.student_id == "STU001")
            .where(AuditLog.action == "scholarship_tool")
            .where(AuditLog.decision == "BLOCKED")
            .order_by(AuditLog.created_at.desc())
        )
        audit_entry = audit_res.scalars().first()
        assert audit_entry is not None
        assert audit_entry.target_id == "STU003"
        assert audit_entry.decision == "BLOCKED"


def test_20_sensitive_action_detection():
    """Scenario 3 from PDF: Verify sensitive actions are detected and non-sensitive actions pass."""
    approval_svc = ApprovalService()
    assert approval_svc.is_sensitive_action("update_contact") is True
    assert approval_svc.is_sensitive_action("request_fee_waiver") is True
    assert approval_svc.is_sensitive_action("get_fee_status") is False
    assert approval_svc.is_sensitive_action("search_student_handbook") is False


def test_21_approval_confirmation_outcomes():
    """Scenario 4 from PDF: Affirmative confirmation approved, rejection blocks action."""
    approval_svc = ApprovalService()
    assert approval_svc.evaluate_confirmation("YES") == ApprovalStatus.APPROVED
    assert approval_svc.evaluate_confirmation("confirm") == ApprovalStatus.APPROVED
    assert approval_svc.evaluate_confirmation("NO") == ApprovalStatus.REJECTED
    assert approval_svc.evaluate_confirmation("I changed my mind") == ApprovalStatus.REJECTED


@pytest.mark.asyncio
async def test_22_support_ticket_audited():
    """Verify administrative ticket creation generates an audit record in PostgreSQL."""
    res = await create_support_ticket(
        student_id="STU001",
        category="Fee Installment",
        description="Requesting installment plan for remaining fees.",
        priority="high",
    )
    assert "Support Ticket Created Successfully" in res

    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            select(AuditLog)
            .where(AuditLog.student_id == "STU001")
            .where(AuditLog.action == "ticket_tool")
            .order_by(AuditLog.created_at.desc())
        )
        audit_entry = audit_res.scalars().first()
        assert audit_entry is not None
        assert audit_entry.decision == "ALLOWED"
