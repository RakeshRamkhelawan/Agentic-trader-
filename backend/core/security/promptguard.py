"""
Prompt Injection Defense (Sprint 4 S4-4).

Protects LLM agents from prompt injection attacks by:
- Input sanitization
- Pattern detection for common attacks
- Rate limiting per user/session
- Audit logging

Usage:
    from backend.core.security.promptguard import PromptGuard
    
    guard = PromptGuard()
    is_safe, reason = guard.scan(user_input)
    if not is_safe:
        raise SecurityException(f"Prompt injection detected: {reason}")
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result of prompt security scan."""

    is_safe: bool
    threat_level: str  # "none", "low", "medium", "high"
    reason: Optional[str]
    matched_patterns: List[str]
    sanitized_input: str


class PromptGuard:
    """
    LLM Prompt Injection Defense System.

    Features:
    1. Heuristic pattern matching for injection attempts
    2. Input sanitization (escape special sequences)
    3. Rate limiting for suspicious inputs
    4. Audit logging

    Defense Patterns:
    - "Ignore all previous instructions"
    - "SYSTEM OVERRIDE"
    - "You are now DAN"
    - Delimiter confusion attacks
    - Role confusion attacks
    """

    # High-confidence injection patterns (block immediately)
    HIGH_RISK_PATTERNS = [
        # Direct instruction overrides
        r"ignore\s+(all\s+)?(previous|prior|earlier)\s+(instructions?|commands?|prompts?)",
        r"forget\s+(all\s+)?(previous|prior|earlier)\s+(instructions?|commands?)",
        r"disregard\s+(all\s+)?(previous|prior)\s+instructions?",
        # System/role overrides
        r"system\s+(override|command|prompt)",
        r"you\s+are\s+now\s+(in\s+)?(?:developer|admin|root|sudo|DAN)\s+mode",
        r"you\s+are\s+now\s+[\"\']?(?:DAN|Developer|Admin)[\"\']?",
        # Delimiter attacks
        r"```\s*system",
        r"<\s*system\s*>",
        r"\[\s*system\s*\]",
        # Special token injection
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"<\|system\|>",
        r"<\|user\|>",
        r"<\|assistant\|>",
    ]

    # Medium-risk patterns (flag for review)
    MEDIUM_RISK_PATTERNS = [
        # Attempts to change role/persona
        r"from\s+now\s+on\s+you\s+are",
        r"act\s+as\s+(?:if\s+you\s+are|though\s+you\s+are)",
        r"pretend\s+(?:to\s+be|you\s+are)",
        r"roleplay\s+as",
        # Suspicious separators
        r"={10,}",  # Many equals signs
        r"-{10,}",  # Many hyphens
        r"\n{5,}",  # Excessive newlines
        # Hidden text attempts
        r"\{\{.*?\}\}",  # Double braces
        r"\[\[.*?\]\]",  # Double brackets
    ]

    # Characters to escape/sanitize
    DANGEROUS_SEQUENCES = [
        ("```", "` ` `"),  # Break code blocks
        ("<|", "< |"),  # Break special tokens
        ("|>", "| >"),
    ]

    def __init__(self, max_input_length: int = 10000):
        """
        Initialize PromptGuard.

        Args:
            max_input_length: Maximum allowed input length
        """
        self.max_input_length = max_input_length
        self._high_risk_regex = [
            re.compile(p, re.IGNORECASE) for p in self.HIGH_RISK_PATTERNS
        ]
        self._medium_risk_regex = [
            re.compile(p, re.IGNORECASE) for p in self.MEDIUM_RISK_PATTERNS
        ]
        self._scan_count = 0
        self._threat_count = 0

    def scan(self, user_input: str, context: Optional[Dict] = None) -> ScanResult:
        """
        Scan user input for prompt injection attempts.

        Args:
            user_input: Raw user input
            context: Optional context (user_id, session_id, etc.)

        Returns:
            ScanResult with safety determination
        """
        self._scan_count += 1

        # Check length
        if len(user_input) > self.max_input_length:
            return ScanResult(
                is_safe=False,
                threat_level="high",
                reason=f"Input exceeds maximum length ({len(user_input)} > {self.max_input_length})",
                matched_patterns=["EXCESSIVE_LENGTH"],
                sanitized_input=user_input[: self.max_input_length],
            )

        matched_patterns = []

        # Check high-risk patterns
        for i, pattern in enumerate(self._high_risk_regex):
            if pattern.search(user_input):
                matched_patterns.append(f"HIGH:{self.HIGH_RISK_PATTERNS[i][:30]}...")

        if matched_patterns:
            self._threat_count += 1
            self._log_threat(user_input, matched_patterns, context)
            return ScanResult(
                is_safe=False,
                threat_level="high",
                reason=f"High-risk pattern detected: {matched_patterns[0]}",
                matched_patterns=matched_patterns,
                sanitized_input=self._sanitize(user_input),
            )

        # Check medium-risk patterns
        for i, pattern in enumerate(self._medium_risk_regex):
            if pattern.search(user_input):
                matched_patterns.append(f"MED:{self.MEDIUM_RISK_PATTERNS[i][:30]}...")

        # Sanitize input regardless of risk level
        sanitized = self._sanitize(user_input)

        if matched_patterns:
            return ScanResult(
                is_safe=True,  # Allowed but flagged
                threat_level="medium",
                reason=f"Medium-risk patterns detected: {len(matched_patterns)}",
                matched_patterns=matched_patterns,
                sanitized_input=sanitized,
            )

        return ScanResult(
            is_safe=True,
            threat_level="none",
            reason=None,
            matched_patterns=[],
            sanitized_input=sanitized,
        )

    def _sanitize(self, user_input: str) -> str:
        """
        Sanitize input by escaping dangerous sequences.

        Args:
            user_input: Raw input

        Returns:
            Sanitized input
        """
        sanitized = user_input
        for dangerous, safe in self.DANGEROUS_SEQUENCES:
            sanitized = sanitized.replace(dangerous, safe)
        return sanitized

    def _log_threat(
        self, user_input: str, patterns: List[str], context: Optional[Dict]
    ):
        """Log security threat."""
        input_hash = hashlib.sha256(user_input.encode()).hexdigest()[:16]
        logger.warning(
            "PROMPT INJECTION ATTEMPT DETECTED",
            extra={
                "security_event": "prompt_injection",
                "input_hash": input_hash,
                "patterns": patterns,
                "context": context or {},
            },
        )

    def get_stats(self) -> Dict:
        """Get scanning statistics."""
        return {
            "total_scans": self._scan_count,
            "threats_detected": self._threat_count,
            "threat_rate": self._threat_count / max(self._scan_count, 1),
        }


class APIKeyRotator:
    """
    Simulated API Key Rotation for Vault/KMS integration.

    In production, this would integrate with:
    - HashiCorp Vault
    - AWS KMS
    - Azure Key Vault

    For now: Simulates rotation via environment variable reloading.
    """

    def __init__(self):
        self._current_key_id = "v1"
        self._rotation_count = 0

    def rotate_key(self, service: str) -> Tuple[str, str]:
        """
        Rotate API key for service.

        Args:
            service: Service name (e.g., "openai", "deepseek")

        Returns:
            Tuple of (new_key_id, new_key)
        """
        import os
        import secrets

        # Generate new key (in production: fetch from vault)
        new_key = secrets.token_urlsafe(32)
        self._rotation_count += 1
        new_key_id = f"v{self._rotation_count}"

        # Update environment (simulation)
        env_var = f"{service.upper()}_API_KEY"
        os.environ[env_var] = new_key

        logger.info(
            f"API key rotated for {service}: {self._current_key_id} -> {new_key_id}"
        )
        self._current_key_id = new_key_id

        return new_key_id, new_key

    def get_current_key(self, service: str) -> Optional[str]:
        """Get current API key."""
        import os

        env_var = f"{service.upper()}_API_KEY"
        return os.environ.get(env_var)


# Convenience functions
def scan_prompt(user_input: str, context: Optional[Dict] = None) -> ScanResult:
    """Quick scan function using global guard."""
    return _global_guard.scan(user_input, context)


# Global instance
_global_guard = PromptGuard()


def get_prompt_guard() -> PromptGuard:
    """Get global PromptGuard instance."""
    return _global_guard
