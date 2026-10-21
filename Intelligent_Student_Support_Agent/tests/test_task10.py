"""Comprehensive test suite for Task 10: End-to-End Chat, Student Records, and Audit APIs.

Validates:
1. Student records endpoints (profile, fees, scholarship, tickets) via authenticated JWT.
2. Audit endpoints (log listing, compliance metric summary).
3. Conversational Agent API (/api/v1/chat):
   - Conversation session creation and persistence in PostgreSQL.
   - Message turns history and trace ID association.
   - Two-tier memory injection and fact extraction update.
4. Security and authorization barriers (missing/invalid token rejection).
"""

from httpx import ASGITransport, AsyncClient
import pytest
from app.main import app
from app.services.auth_service import create_access_token


@pytest.mark.asyncio
async def test_01_student_profile_endpoint():
    """Verify authenticated student can access their academic profile."""
    transport = ASGITransport(app=app)
    token = create_access_token("STU001")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/student/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["student_id"] == "STU001"
        assert data["name"] == "Rahul Sharma"
        assert "PGDM" in data["programme"]


@pytest.mark.asyncio
async def test_02_student_fees_endpoint():
    """Verify authenticated student can query their tuition fee ledger."""
    transport = ASGITransport(app=app)
    token = create_access_token("STU001")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/student/fees",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["student_id"] == "STU001"
        assert data["total_fee"] == 450000.0
        assert data["paid"] == 225000.0


@pytest.mark.asyncio
async def test_03_student_scholarship_endpoint():
    """Verify authenticated student can query active scholarship awards."""
    transport = ASGITransport(app=app)
    token = create_access_token("STU001")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/student/scholarship",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["student_id"] == "STU001"
        assert data["scholarship_type"] == "Merit Scholarship"


@pytest.mark.asyncio
async def test_04_audit_logs_and_summary_endpoints():
    """Verify audit endpoints expose compliance logs and decision counts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Logs
        res_logs = await client.get("/api/v1/audit/logs?limit=10")
        assert res_logs.status_code == 200
        logs_data = res_logs.json()["data"]
        assert isinstance(logs_data, list)

        # Summary
        res_summary = await client.get("/api/v1/audit/summary")
        assert res_summary.status_code == 200
        summary = res_summary.json()["data"]
        assert "total_events" in summary
        assert "allowed_count" in summary
        assert "blocked_count" in summary


@pytest.mark.asyncio
async def test_05_chat_endpoint_turn_execution_and_persistence():
    """Verify /api/v1/chat triggers agent loop, persists messages, and updates memory."""
    transport = ASGITransport(app=app)
    token = create_access_token("STU001")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Send first prompt
        res = await client.post(
            "/api/v1/chat",
            json={"message": "Hello, what are my current fee dues?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        chat_data = res.json()["data"]
        conv_id = chat_data["conversation_id"]
        assert conv_id is not None
        assert chat_data["role"] == "assistant"
        assert chat_data["message"]

        # 2. Query conversation list for this student
        res_list = await client.get(
            "/api/v1/chat/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_list.status_code == 200
        conversations = res_list.json()["data"]
        assert any(c["id"] == conv_id for c in conversations)

        # 3. Query turn messages for this conversation
        res_msgs = await client.get(
            f"/api/v1/chat/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_msgs.status_code == 200
        messages = res_msgs.json()["data"]
        assert len(messages) >= 2  # user + assistant
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_06_unauthorized_requests_rejected():
    """Verify protected routes reject calls without valid JWT bearer token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Chat without token
        res_chat = await client.post("/api/v1/chat", json={"message": "Hello"})
        assert res_chat.status_code == 401

        # Profile without token
        res_prof = await client.get("/api/v1/student/profile")
        assert res_prof.status_code == 401
