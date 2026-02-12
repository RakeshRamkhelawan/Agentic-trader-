"""
Prompt Guard - Security utilities for Mitigating Prompt Injection.

Provides tools for input sanitization and robust data isolation
to prevent untrusted external data from hijacking LLM instructions.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class PromptGuard:
    """
    Utility class for sanitizing and isolating LLM inputs.
    """

    # Common injection patterns
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(?:all\s+)?previous\s+instructions",
        r"(?i)system:",
        r"(?i)user:",
        r"(?i)assistant:",
        r"(?i)stop\s+reasoning",
        r"(?i)output\s+only\s+the\s+following",
    ]

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize input text by removing or flagging known injection patterns.
        
        Args:
            text: Raw input text
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)

        sanitized = text
        for pattern in PromptGuard.INJECTION_PATTERNS:
            if re.search(pattern, sanitized):
                logger.warning(f"Detection: Potential prompt injection pattern found: {pattern}")
                # We replace with a placeholder instead of just removing to maintain context 
                # but neutralize the command.
                sanitized = re.sub(pattern, "[CLEANED_INJECTION_ATTEMPT]", sanitized)
        
        return sanitized

    @staticmethod
    def wrap_data(label: str, data: Any) -> str:
        """
        Wrap data within XML-style tags to isolate it for the LLM.
        Using distinct delimiters makes it harder for malicious data 
        to "break out" of its context.
        
        Args:
            label: Label for the data block (e.g., 'MARKET_DATA')
            data: The data to wrap
            
        Returns:
            Formatted string with delimiters
        """
        # Ensure label doesn't contain characters that could break the tag
        safe_label = re.sub(r"[^A-Z0-0_]", "", label.upper())
        
        # Sanitize data content if it's a string
        content = data
        if isinstance(data, str):
            content = PromptGuard.sanitize_input(data)
            
        return f"<{safe_label}>\n{content}\n</{safe_label}>"

    @staticmethod
    def guard_prompt(system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """
        Apply global guards to both system and user prompts.
        
        Args:
            system_prompt: Base system instructions
            user_prompt: Specific user request
            
        Returns:
            Tuple of (sanitized_system, sanitized_user)
        """
        # We generally don't sanitize the system prompt as it's dev-controlled,
        # but we sanitize the user prompt which might contain external data.
        return system_prompt, PromptGuard.sanitize_input(user_prompt)
