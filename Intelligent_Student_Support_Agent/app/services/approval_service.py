"""Human-in-the-loop approval service for sensitive student record modifications.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively manages detection of sensitive actions
  and validation of student confirmation decisions.
- Open/Closed (OCP): List of sensitive action keywords is dynamically configured in settings.
"""

from typing import Any, Dict
from app.config.settings import settings
from app.schemas.approval_schema import ApprovalRequest, ApprovalStatus
from app.utils.logger import logger


class ApprovalService:
    """Service governing human-in-the-loop approval gates for sensitive actions."""

    def __init__(self) -> None:
        self.sensitive_actions = settings.sensitive_actions

    def is_sensitive_action(self, action_name: str) -> bool:
        """Determines whether a proposed action requires explicit student confirmation."""
        clean_action = action_name.strip().lower()
        return clean_action in self.sensitive_actions

    def create_approval_request(
        self, action: str, student_id: str, details: Dict[str, Any]
    ) -> ApprovalRequest:
        """Constructs an approval request contract for an unconfirmed sensitive action."""
        logger.info(
            f"Approval gate triggered for student '{student_id}' on sensitive action '{action}'"
        )
        return ApprovalRequest(
            action=action,
            student_id=student_id,
            details=details,
            status=ApprovalStatus.PENDING,
        )

    def evaluate_confirmation(self, response_text: str) -> ApprovalStatus:
        """Evaluates student's confirmation message to determine approval outcome.

        Args:
            response_text: Text message provided by the user (e.g. 'YES', 'NO', 'cancel').

        Returns:
            ApprovalStatus.APPROVED if confirmation is affirmative.
            ApprovalStatus.REJECTED otherwise.
        """
        clean_text = response_text.strip().upper()
        if clean_text in {"YES", "Y", "CONFIRM", "APPROVE", "CONFIRMED"}:
            logger.info(f"Student confirmation evaluation: APPROVED ('{clean_text}')")
            return ApprovalStatus.APPROVED

        logger.info(f"Student confirmation evaluation: REJECTED ('{clean_text}')")
        return ApprovalStatus.REJECTED
