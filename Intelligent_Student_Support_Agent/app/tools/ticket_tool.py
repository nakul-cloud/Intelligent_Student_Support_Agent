"""Student administrative support escalation and ticketing tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively handles the validation, generation, and creation
  of support and grievance escalation tickets in the PostgreSQL database.
- Separation of Concerns: Contains only Python execution logic; schemas are decoupled
  in the app/schemas/ layer.
"""

import random
import string
from sqlalchemy import select
from app.config.constants import TicketPriority, TicketStatus
from app.config.database import AsyncSessionLocal
from app.config.settings import settings
from app.models.student_records import Student, SupportTicket
from app.utils.logger import logger


async def create_support_ticket(
    student_id: str,
    category: str,
    description: str,
    priority: str = "medium",
) -> str:
    """Escalate a student grievance, fee query, or academic issue by creating a support ticket.

    Generates a unique tracking ticket number and records the ticket in PostgreSQL
    for administrative review and staff resolution.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').
        category: Ticket classification (e.g. 'Fee Installment', 'Attendance Condonation', 'Grade Appeal', 'General').
        description: A clear explanation of the student's issue or escalation request.
        priority: Urgency level ('low', 'medium', 'high', 'urgent'). Defaults to 'medium'.

    Returns:
        A human-readable confirmation string containing the new Ticket ID and status.
    """
    clean_id = student_id.strip().upper()
    logger.info(f"TicketTool: Creating support ticket for student '{clean_id}' (Category: '{category}')...")

    try:
        async with AsyncSessionLocal() as session:
            # 1. Verify student exists before creating ticket
            student_stmt = select(Student).where(Student.student_id == clean_id)
            student_result = await session.execute(student_stmt)
            student = student_result.scalar_one_or_none()

            if not student:
                return f"Cannot create ticket: No student found with ID '{clean_id}'."

            # 2. Validate priority or fallback to standard medium
            clean_priority = priority.strip().lower()
            valid_priorities = {p.value for p in TicketPriority}
            if clean_priority not in valid_priorities:
                clean_priority = TicketPriority.MEDIUM.value

            # 3. Generate a unique ticket tracking code using configured prefix
            random_digits = "".join(random.choices(string.digits, k=5))
            ticket_code = f"{settings.ticket_prefix}{random_digits}"

            # 4. Insert ticket record into PostgreSQL
            ticket = SupportTicket(
                ticket_id=ticket_code,
                student_id=clean_id,
                category=category.strip(),
                description=description.strip(),
                priority=clean_priority,
                status=TicketStatus.OPEN.value,
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)

            logger.info(f"TicketTool: Successfully created ticket '{ticket_code}' for student '{clean_id}'.")

            # 5. Record audit trail for ticket generation
            from app.services.audit_service import log_audit_event
            await log_audit_event(
                student_id=clean_id,
                action="ticket_tool",
                target_id=clean_id,
                decision="ALLOWED",
                result=f"Support ticket {ticket_code} created (Priority: {clean_priority})",
            )

            confirmation = (
                f"Support Ticket Created Successfully!\n"
                f"Ticket ID: {ticket_code}\n"
                f"Student: {student.name} (ID: {clean_id})\n"
                f"Category: {category}\n"
                f"Priority: {clean_priority.upper()}\n"
                f"Current Status: OPEN\n"
                f"Details: {description}\n"
                f"Note: University administration will review this ticket within 2 business days."
            )
            return confirmation

    except Exception as exc:
        logger.error(f"TicketTool: Error creating support ticket for '{clean_id}': {exc}")
        return f"Database error while creating support ticket for student '{clean_id}': {str(exc)}"


async def get_ticket_status(
    ticket_id: str,
    student_id: str,
) -> str:
    """Retrieve the current processing status, priority, and updates for an existing support ticket.

    Args:
        ticket_id: The tracking reference code for the ticket (e.g. 'TICK-96628').
        student_id: The unique student identification code (e.g. 'STU001').

    Returns:
        A formatted status report of the ticket from the university database.
    """
    clean_ticket = ticket_id.strip().upper()
    clean_student = student_id.strip().upper()
    logger.info(f"TicketTool: Querying status of ticket '{clean_ticket}' for student '{clean_student}'...")

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(SupportTicket).where(
                SupportTicket.ticket_id == clean_ticket,
                SupportTicket.student_id == clean_student,
            )
            result = await session.execute(stmt)
            ticket = result.scalar_one_or_none()

            if not ticket:
                # Security check: verify if the ticket exists for another student
                other_stmt = select(SupportTicket).where(SupportTicket.ticket_id == clean_ticket)
                other_res = await session.execute(other_stmt)
                if other_res.scalar_one_or_none():
                    logger.warning(
                        f"TicketTool: Student '{clean_student}' attempted to inspect ticket '{clean_ticket}' owned by another student."
                    )
                    return f"Access Denied: Ticket '{clean_ticket}' belongs to another student account."
                return f"No support ticket found with reference code '{clean_ticket}' under your account."

            created_str = (
                ticket.created_at.strftime("%b %d, %Y, %H:%M UTC")
                if ticket.created_at
                else "Recent"
            )

            # Audit lookup event
            from app.services.audit_service import log_audit_event
            await log_audit_event(
                student_id=clean_student,
                action="ticket_status_inquiry",
                target_id=clean_ticket,
                decision="ALLOWED",
                result=f"Ticket {clean_ticket} status: {ticket.status.upper()}",
            )

            return (
                f"Support Ticket Status Report:\n"
                f"- Ticket ID: {ticket.ticket_id}\n"
                f"- Category: {ticket.category}\n"
                f"- Priority: {ticket.priority.upper()}\n"
                f"- Current Status: {ticket.status.upper()}\n"
                f"- Date Submitted: {created_str}\n"
                f"- Description: {ticket.description}\n"
                f"- Current Update: The ticket is actively logged in the university system under status '{ticket.status.upper()}'."
            )

    except Exception as exc:
        logger.error(f"TicketTool: Error querying ticket status '{clean_ticket}': {exc}")
        return f"Database error while querying ticket status: {str(exc)}"


async def list_student_tickets(
    student_id: str,
) -> str:
    """Retrieve all support tickets logged by the authenticated student.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').

    Returns:
        A formatted list of all open and closed tickets belonging to the student.
    """
    clean_student = student_id.strip().upper()
    logger.info(f"TicketTool: Listing all support tickets for student '{clean_student}'...")

    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(SupportTicket)
                .where(SupportTicket.student_id == clean_student)
                .order_by(SupportTicket.created_at.desc())
            )
            result = await session.execute(stmt)
            tickets = result.scalars().all()

            if not tickets:
                return f"No support tickets have been filed for student '{clean_student}'."

            lines = [f"Support Tickets on Record for Student {clean_student} ({len(tickets)} total):"]
            for idx, t in enumerate(tickets[:10], start=1):
                created_str = t.created_at.strftime("%b %d, %Y") if t.created_at else "Recent"
                lines.append(
                    f"{idx}. [{t.ticket_id}] Status: {t.status.upper()} | Priority: {t.priority.upper()} | "
                    f"Category: {t.category}\n"
                    f"   Details: {t.description[:80]}... (Submitted: {created_str})"
                )

            return "\n".join(lines)

    except Exception as exc:
        logger.error(f"TicketTool: Error listing tickets for '{clean_student}': {exc}")
        return f"Database error while listing tickets: {str(exc)}"

