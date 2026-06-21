# app/security/prompt_guard.py

import re
from dataclasses import dataclass, field
from typing import Literal


RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass
class PromptGuardResult:
    allowed: bool
    reason: str
    risk_level: RiskLevel
    categories: list[str] = field(default_factory=list)
    requires_approval: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "categories": self.categories,
            "requires_approval": self.requires_approval,
        }


class PromptGuard:
    """
    Validates user prompts before sending them to RAG or LLM.

    Blocks or requires approval for:
    - destructive actions
    - credential extraction
    - security bypass
    - production impact
    - data exfiltration
    - malicious instructions
    """

    def __init__(self) -> None:
        self.rules = [
            {
                "category": "destructive_action",
                "risk_level": "high",
                "requires_approval": False,
                "reason": "Prompt asks for destructive action.",
                "patterns": [
                    r"\bdelete\b.*\b(all|tenant|tenants|customer|customers|users|records|database|db)\b",
                    r"\bremove\b.*\b(all|tenant|tenants|customer|customers|users|records|database|db)\b",
                    r"\bdrop\b.*\b(database|db|table|collection|tenant|tenants)\b",
                    r"\bwipe\b.*\b(all|data|tenant|tenants|database|db)\b",
                    r"\bdestroy\b.*\b(tenant|tenants|environment|database|db)\b",
                    r"\bpurge\b.*\b(all|data|tenant|tenants|records)\b",
                ],
            },
            {
                "category": "credential_extraction",
                "risk_level": "critical",
                "requires_approval": False,
                "reason": "Prompt asks to extract or expose credentials.",
                "patterns": [
                    r"\b(extract|show|print|dump|export|reveal|get)\b.*\b(password|passwords|secret|secrets|token|tokens|api key|api keys|apikey|credentials)\b",
                    r"\b(password|passwords|secret|secrets|token|tokens|api key|api keys|apikey|credentials)\b.*\b(extract|show|print|dump|export|reveal)\b",
                    r"\bsteal\b.*\b(password|passwords|secret|secrets|token|tokens|credentials)\b",
                ],
            },
            {
                "category": "security_bypass",
                "risk_level": "critical",
                "requires_approval": False,
                "reason": "Prompt asks to bypass or disable security controls.",
                "patterns": [
                    r"\bbypass\b.*\b(login|authentication|auth|authorization|rbac|security|mfa|2fa)\b",
                    r"\bdisable\b.*\b(security|auth|authentication|authorization|rbac|validation|guardrails|checks)\b",
                    r"\bskip\b.*\b(login|auth|authentication|authorization|security|validation|guardrails|checks)\b",
                    r"\bignore\b.*\b(security|policy|guardrails|validation|permissions)\b",
                    r"\bremove\b.*\b(auth|authentication|authorization|rbac|security checks)\b",
                ],
            },
            {
                "category": "production_impact",
                "risk_level": "high",
                "requires_approval": True,
                "reason": "Prompt may impact production and requires human approval.",
                "patterns": [
                    r"\brun\b.*\b(on production|in production|prod environment|production environment|prod)\b",
                    r"\bexecute\b.*\b(on production|in production|prod environment|production environment|prod)\b",
                    r"\bdeploy\b.*\b(to production|in production|prod)\b",
                    r"\bmodify\b.*\b(production|prod)\b",
                    r"\bdelete\b.*\b(production|prod)\b",
                ],
            },
            {
                "category": "data_exfiltration",
                "risk_level": "critical",
                "requires_approval": False,
                "reason": "Prompt asks to export or exfiltrate sensitive customer data.",
                "patterns": [
                    r"\b(export|dump|download|copy|extract)\b.*\b(all customer data|customer data|tenant data|user data|pii|personal data)\b",
                    r"\bexport\b.*\b(all|entire)\b.*\b(database|db|customers|users|tenants)\b",
                    r"\bdump\b.*\b(database|db|customer|customers|tenant|tenants|users)\b",
                    r"\bsend\b.*\b(customer data|tenant data|user data|pii|personal data)\b",
                ],
            },
            {
                "category": "malicious_instruction",
                "risk_level": "critical",
                "requires_approval": False,
                "reason": "Prompt contains malicious or unsafe instructions.",
                "patterns": [
                    r"\bhack\b",
                    r"\bexploit\b.*\b(system|server|api|login|auth|vulnerability)\b",
                    r"\breverse shell\b",
                    r"\bmalware\b",
                    r"\bransomware\b",
                    r"\bkeylogger\b",
                    r"\bprivilege escalation\b",
                    r"\bescalate privileges\b",
                ],
            },
        ]

    def validate(self, prompt: str) -> dict:
        if not prompt or not prompt.strip():
            return PromptGuardResult(
                allowed=False,
                reason="Prompt is empty.",
                risk_level="medium",
                categories=["empty_prompt"],
            ).to_dict()

        normalized_prompt = self._normalize(prompt)

        matched_categories: list[str] = []
        matched_reasons: list[str] = []
        matched_risk_levels: list[str] = []
        approval_required = False

        for rule in self.rules:
            for pattern in rule["patterns"]:
                if re.search(pattern, normalized_prompt, flags=re.IGNORECASE):
                    matched_categories.append(rule["category"])
                    matched_reasons.append(rule["reason"])
                    matched_risk_levels.append(rule["risk_level"])

                    if rule["requires_approval"]:
                        approval_required = True

                    break

        if matched_categories:
            highest_risk = self._highest_risk(matched_risk_levels)

            return PromptGuardResult(
                allowed=False,
                reason=self._merge_reasons(matched_reasons),
                risk_level=highest_risk,
                categories=sorted(set(matched_categories)),
                requires_approval=approval_required,
            ).to_dict()

        return PromptGuardResult(
            allowed=True,
            reason="Prompt is safe.",
            risk_level="low",
            categories=[],
            requires_approval=False,
        ).to_dict()

    def _normalize(self, prompt: str) -> str:
        prompt = prompt.lower().strip()
        prompt = re.sub(r"\s+", " ", prompt)
        return prompt

    def _highest_risk(self, risks: list[str]) -> RiskLevel:
        priority = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }

        highest = max(risks, key=lambda risk: priority.get(risk, 1))
        return highest  # type: ignore

    def _merge_reasons(self, reasons: list[str]) -> str:
        unique_reasons = list(dict.fromkeys(reasons))
        return " ".join(unique_reasons)


prompt_guard = PromptGuard()


def validate_prompt(prompt: str) -> dict:
    return prompt_guard.validate(prompt)