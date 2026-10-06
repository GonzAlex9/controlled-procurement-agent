from __future__ import annotations

from procurement_agent.models import (
    ApprovalRole,
    Budget,
    Decision,
    FindingSeverity,
    PolicyAssessment,
    PolicyFinding,
    PurchaseRequest,
    Vendor,
    VendorRisk,
    VendorStatus,
)


class ProcurementPolicyEngine:
    """Fictional procurement rules used to demonstrate deterministic safety gates."""

    def evaluate(
        self,
        request: PurchaseRequest,
        vendor: Vendor | None,
        budget: Budget | None,
    ) -> PolicyAssessment:
        findings: list[PolicyFinding] = []
        approvals: list[ApprovalRole] = []
        blocking = False

        def require(role: ApprovalRole) -> None:
            if role not in approvals:
                approvals.append(role)

        if vendor is None:
            findings.append(
                PolicyFinding(
                    code="VENDOR_UNKNOWN",
                    message=(
                        "Vendor is not present in the vendor master and requires "
                        "procurement review."
                    ),
                    severity=FindingSeverity.WARNING,
                )
            )
            require(ApprovalRole.PROCUREMENT)
        elif vendor.status == VendorStatus.BLOCKED:
            findings.append(
                PolicyFinding(
                    code="VENDOR_BLOCKED",
                    message="Vendor is blocked by policy.",
                    severity=FindingSeverity.BLOCKING,
                )
            )
            blocking = True
        elif vendor.status == VendorStatus.REVIEW:
            findings.append(
                PolicyFinding(
                    code="VENDOR_REVIEW",
                    message="Vendor requires procurement review before purchase.",
                    severity=FindingSeverity.WARNING,
                )
            )
            require(ApprovalRole.PROCUREMENT)

        if budget is None:
            findings.append(
                PolicyFinding(
                    code="BUDGET_UNKNOWN",
                    message="Department budget could not be resolved.",
                    severity=FindingSeverity.BLOCKING,
                )
            )
            blocking = True
        elif request.amount_eur > budget.remaining_eur:
            findings.append(
                PolicyFinding(
                    code="BUDGET_EXCEEDED",
                    message=(
                        f"Request exceeds remaining department budget of "
                        f"EUR {budget.remaining_eur:,.2f}."
                    ),
                    severity=FindingSeverity.BLOCKING,
                )
            )
            blocking = True

        if request.amount_eur > 1_000:
            require(ApprovalRole.MANAGER)
        if request.amount_eur >= 5_000:
            require(ApprovalRole.FINANCE)
        if request.amount_eur >= 25_000:
            require(ApprovalRole.CIO)

        required_quotes = 1
        if request.amount_eur >= 5_000:
            required_quotes = 2
        if request.amount_eur >= 25_000:
            required_quotes = 3

        if request.quotes_count < required_quotes:
            code = "EMERGENCY_QUOTE_EXCEPTION" if request.emergency else "INSUFFICIENT_QUOTES"
            findings.append(
                PolicyFinding(
                    code=code,
                    message=(
                        f"Request has {request.quotes_count} quote(s); policy expects "
                        f"{required_quotes}. Human review is required."
                    ),
                    severity=FindingSeverity.WARNING,
                )
            )
            require(ApprovalRole.PROCUREMENT)

        category = request.category.strip().lower()
        if (
            category in {"software", "saas", "ai", "ai tool", "cloud"}
            and request.contains_personal_data
        ):
            findings.append(
                PolicyFinding(
                    code="SECURITY_REVIEW",
                    message="Technology handles personal data and requires security review.",
                    severity=FindingSeverity.WARNING,
                )
            )
            require(ApprovalRole.SECURITY)

        if vendor is not None and vendor.risk == VendorRisk.HIGH:
            findings.append(
                PolicyFinding(
                    code="HIGH_RISK_VENDOR",
                    message="High-risk vendor requires finance and security review.",
                    severity=FindingSeverity.WARNING,
                )
            )
            require(ApprovalRole.FINANCE)
            require(ApprovalRole.SECURITY)

        if request.recurring:
            findings.append(
                PolicyFinding(
                    code="RECURRING_SPEND",
                    message="Recurring spend should be reviewed as total contract exposure.",
                    severity=FindingSeverity.INFO,
                )
            )

        if blocking:
            decision = Decision.REJECT
            approvals = []
        elif approvals:
            decision = Decision.HUMAN_REVIEW
        else:
            decision = Decision.AUTO_APPROVE

        return PolicyAssessment(
            decision=decision,
            required_approvals=approvals,
            findings=findings,
        )
