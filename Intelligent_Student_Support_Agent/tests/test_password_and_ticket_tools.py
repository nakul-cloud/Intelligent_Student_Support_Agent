"""Tests for immediate password change and support ticket tracking tools."""

import pytest
import pytest_asyncio
from app.config.database import AsyncSessionLocal
from app.models.auth_credentials import AuthCredentials
from app.models.student_records import SupportTicket
from app.services.auth_service import verify_password
from app.tools.auth_tool import update_student_password
from app.tools.ticket_tool import create_support_ticket, get_ticket_status, list_student_tickets
from sqlalchemy import select


@pytest.mark.asyncio
async def test_update_student_password_immediate_db_update():
    """Verify that update_student_password hashes password and immediately updates auth_credentials."""
    student_id = "STU001"
    new_test_password = "NewlyUpdatedPassword2026!"

    result = await update_student_password(student_id=student_id, new_password=new_test_password)
    assert "Password Updated Successfully" in result
    assert "Immediately" in result

    # Check database directly
    async with AsyncSessionLocal() as session:
        stmt = select(AuthCredentials).where(AuthCredentials.student_id == student_id)
        res = await session.execute(stmt)
        cred = res.scalar_one_or_none()
        assert cred is not None
        assert verify_password(new_test_password, cred.hashed_password) is True

    # Revert password back to original standard for other test suites
    await update_student_password(student_id=student_id, new_password="Student@123")



@pytest.mark.asyncio
async def test_update_student_password_length_validation():
    """Verify short password is rejected."""
    result = await update_student_password(student_id="STU001", new_password="123")
    assert "Password change rejected" in result


@pytest.mark.asyncio
async def test_ticket_status_lookup_and_listing():
    """Verify ticket creation followed by immediate status lookup and student ticket listing."""
    student_id = "STU001"
    # Create ticket
    create_res = await create_support_ticket(
        student_id=student_id,
        category="IT Facilities",
        description="Testing ticket lookup tool",
        priority="high",
    )
    assert "Support Ticket Created Successfully" in create_res

    # Extract ticket ID (TICK-XXXXX)
    import re
    match = re.search(r"TICK-\d+", create_res)
    assert match is not None
    ticket_id = match.group(0)

    # Test get_ticket_status
    status_res = await get_ticket_status(ticket_id=ticket_id, student_id=student_id)
    assert ticket_id in status_res
    assert "OPEN" in status_res
    assert "IT Facilities" in status_res
    assert "HIGH" in status_res

    # Test cross-student protection
    blocked_res = await get_ticket_status(ticket_id=ticket_id, student_id="STU002")
    assert "Access Denied" in blocked_res

    # Test list_student_tickets
    list_res = await list_student_tickets(student_id=student_id)
    assert ticket_id in list_res


@pytest.mark.asyncio
async def test_update_student_profile():
    """Verify update_student_profile immediately updates phone, email, and address in database."""
    from app.tools.profile_tool import update_student_profile
    from app.models.student_records import Student

    student_id = "STU001"
    new_phone = "+91 91234 56789"
    new_email = "rahul.updated@university.edu"
    new_address = "Hostel Block-C, Suite 305, Main Campus"

    result = await update_student_profile(
        student_id=student_id,
        phone=new_phone,
        email=new_email,
        address=new_address,
    )
    assert "Student Profile Updated Successfully" in result
    assert "Immediately" in result
    assert new_phone in result

    # Check database directly
    async with AsyncSessionLocal() as session:
        stmt = select(Student).where(Student.student_id == student_id)
        res = await session.execute(stmt)
        stu = res.scalar_one_or_none()
        assert stu is not None
        assert stu.phone == new_phone
        assert stu.email == new_email
        assert stu.address == new_address

