# app/security/secret_scanner.py

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.dev",
    ".env.prod",
    ".npmrc",
    ".pypirc",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

SECRET_EXTENSIONS = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}

ALLOWED_TEXT_EXTENSIONS = {
    ".py",
    ".robot",
    ".ts",
    ".js",
    ".java",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".feature",
    ".html",
    ".css",
}


SECRET_PATTERNS = [
    (
        "aws_access_key",
        re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    ),
    (
        "aws_secret_key",
        re.compile(
            r"(?i)(aws(.{0,20})?(secret|access)?(.{0,20})?key)"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{35,}[\"']?"
        ),
    ),
    (
        "private_key",
        re.compile(
            r"-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"
        ),
    ),
    (
        "jwt_token",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\."
            r"[A-Za-z0-9_-]{10,}\."
            r"[A-Za-z0-9_-]{10,}\b"
        ),
    ),
    (
        "github_token",
        re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b"),
    ),
    (
        "github_fine_grained_token",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    ),
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ),
    (
        "google_api_key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ),
    (
        "session_cookie",
        re.compile(
            r"(?i)(session|cookie|connect.sid|JSESSIONID)"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9._%+/=-]{16,}[\"']?"
        ),
    ),
    (
        "generic_secret_assignment",
        re.compile(
            r"(?i)\b(password|passwd|pwd|token|api[_-]?key|secret|client[_-]?secret)"
            r"\s*[:=]\s*[\"'][^\"']{8,}[\"']"
        ),
    ),
]


@dataclass
class SecretFinding:
    file_path: str
    line_number: int
    secret_type: str
    fingerprint: str


@dataclass
class SecretScanResult:
    safe_files: List[Path]
    blocked_files: List[str]
    findings: List[SecretFinding]

    @property
    def has_secrets(self) -> bool:
        return bool(self.blocked_files or self.findings)


class SecretScanError(Exception):
    def __init__(self, result: SecretScanResult):
        self.result = result
        super().__init__("Secret scanning failed")


def _fingerprint(value: str) -> str:
    """
    Never return or log the actual secret.
    Only return a short hash fingerprint.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _line_number(content: str, position: int) -> int:
    return content.count("\n", 0, position) + 1


def _is_binary_file(path: Path) -> bool:
    try:
        data = path.read_bytes()[:2048]
        return b"\0" in data
    except Exception:
        return True


def _entropy(value: str) -> float:
    if not value:
        return 0.0

    frequencies = {}
    for char in value:
        frequencies[char] = frequencies.get(char, 0) + 1

    entropy = 0.0
    length = len(value)

    for count in frequencies.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy


def _looks_like_high_entropy_secret(value: str) -> bool:
    """
    Catches unknown tokens that regex patterns may miss.
    This is intentionally conservative.
    """
    if len(value) < 24:
        return False

    if " " in value:
        return False

    if not re.fullmatch(r"[A-Za-z0-9_\-+/=.]+", value):
        return False

    return _entropy(value) >= 4.2


def _scan_text(file_path: Path, content: str) -> List[SecretFinding]:
    findings: List[SecretFinding] = []

    for secret_type, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(content):
            matched_value = match.group(0)

            findings.append(
                SecretFinding(
                    file_path=str(file_path),
                    line_number=_line_number(content, match.start()),
                    secret_type=secret_type,
                    fingerprint=_fingerprint(matched_value),
                )
            )

    # Extra high-entropy scan for unknown tokens.
    assignment_pattern = re.compile(
        r"(?i)\b([A-Z0-9_]*(TOKEN|SECRET|KEY|PASSWORD|COOKIE)[A-Z0-9_]*)"
        r"\s*[:=]\s*[\"']?([^\"'\s]{12,})[\"']?"
    )

    for match in assignment_pattern.finditer(content):
        value = match.group(3)

        if _looks_like_high_entropy_secret(value):
            findings.append(
                SecretFinding(
                    file_path=str(file_path),
                    line_number=_line_number(content, match.start()),
                    secret_type="high_entropy_secret",
                    fingerprint=_fingerprint(value),
                )
            )

    return findings


def _is_secret_file(path: Path) -> bool:
    return path.name in SECRET_FILE_NAMES or path.suffix.lower() in SECRET_EXTENSIONS


def _should_skip_path(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def scan_repo_for_secrets(repo_path: str) -> SecretScanResult:
    repo = Path(repo_path).resolve()

    if not repo.exists():
        raise FileNotFoundError(f"Repo path does not exist: {repo}")

    safe_files: List[Path] = []
    blocked_files: List[str] = []
    findings: List[SecretFinding] = []

    for path in repo.rglob("*"):
        if not path.is_file():
            continue

        if _should_skip_path(path):
            continue

        if _is_secret_file(path):
            blocked_files.append(str(path))
            continue

        if path.suffix.lower() not in ALLOWED_TEXT_EXTENSIONS:
            continue

        if _is_binary_file(path):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        file_findings = _scan_text(path, content)

        if file_findings:
            findings.extend(file_findings)
        else:
            safe_files.append(path)

    return SecretScanResult(
        safe_files=safe_files,
        blocked_files=blocked_files,
        findings=findings,
    )


def assert_no_secrets_before_ingest(repo_path: str) -> List[Path]:
    """
    Production-safe default:
    - If secrets are found, fail ingestion.
    - Return only safe files if no secrets are found.
    """
    result = scan_repo_for_secrets(repo_path)

    if result.has_secrets:
        raise SecretScanError(result)

    return result.safe_files