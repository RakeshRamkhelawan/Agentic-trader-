"""
Prompt Evolution - LLM past eigen prompts aan

Agents kunnen hun prompts laten evolueren:
- Prompt templates worden geoptimaliseerd
- Few-shot voorbeelden worden bijgewerkt
- Instructies worden verfijnd gebaseerd op success/failure
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.agents.multi_llm_provider import get_multi_llm

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Evolvable prompt template."""

    name: str
    version: int = 1
    template: str = ""
    system_prompt: str = ""
    few_shot_examples: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    # Performance tracking per prompt
    uses: int = 0
    successes: int = 0
    failures: int = 0
    avg_response_quality: float = 0.0

    # Evolution history
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PromptPerformance:
    """Performance metrics for a prompt."""

    prompt_name: str
    total_uses: int
    success_rate: float
    avg_quality: float
    common_errors: List[str]
    improvement_areas: List[str]


class PromptEvolutionEngine:
    """
    Engine voor automatische prompt optimalisatie.
    """

    PROMPT_EVOLUTION_PROMPT = """# Prompt Evolution Task

Je bent een expert prompt engineer. Analyseer de huidige prompt performance en optimaliseer de prompt voor betere resultaten.

## Huidige Prompt (v{version})
```
{current_prompt}
```

## System Prompt
```
{system_prompt}
```

## Few-Shot Examples ({num_examples}):
{few_shot_examples}

## Performance Metrics
- Total Uses: {total_uses}
- Success Rate: {success_rate:.1%}
- Avg Response Quality: {avg_quality:.1f}/10
- Common Errors: {common_errors}

## Recent Failures
{recent_failures}

## Optimization Instructions
1. FIX: Los de common errors op
2. CLARIFY: Maak ambigue instructies expliciet
3. EXAMPLE: Voeg betere few-shot examples toe
4. STRUCTURE: Optimaliseer output format

## Output Format (JSON)
{{
    "analysis": "wat gaat er fout en waarom",
    "new_template": "verbeterde prompt template",
    "new_system_prompt": "optioneel verbeterde system prompt",
    "new_few_shot_examples": [
        {{"input": "...", "output": "..."}}
    ],
    "changes_made": [
        "concrete wijziging 1",
        "concrete wijziging 2"
    ],
    "expected_improvement": "+15% success rate door betere instructies",
    "rationale": "waarom deze wijzigingen werken"
}}

Geef ALLEEN de JSON output, geen markdown."""

    def __init__(self):
        self.multi_llm = get_multi_llm()
        self.prompts: Dict[str, PromptTemplate] = {}
        self.performance_log: List[Dict[str, Any]] = []
        self.feedback_buffer: Dict[str, List[Dict]] = defaultdict(list)

    def register_prompt(
        self,
        name: str,
        template: str,
        system_prompt: str = "",
        few_shot_examples: List[Dict] = None,
    ) -> PromptTemplate:
        """Registreer een prompt voor evolutie."""
        prompt = PromptTemplate(
            name=name,
            template=template,
            system_prompt=system_prompt,
            few_shot_examples=few_shot_examples or [],
        )
        self.prompts[name] = prompt
        logger.info(f"Prompt registered: {name}")
        return prompt

    def record_usage(
        self,
        prompt_name: str,
        input_data: str,
        output_data: str,
        success: bool,
        quality_score: float = 5.0,
        error_message: str = "",
    ) -> None:
        """Record prompt usage performance."""
        if prompt_name not in self.prompts:
            return

        prompt = self.prompts[prompt_name]
        prompt.uses += 1

        if success:
            prompt.successes += 1
        else:
            prompt.failures += 1

        # Update rolling average quality
        prompt.avg_response_quality = (
            prompt.avg_response_quality * (prompt.uses - 1) + quality_score
        ) / prompt.uses

        # Buffer feedback
        self.feedback_buffer[prompt_name].append(
            {
                "timestamp": datetime.now(),
                "input": input_data[:500],  # Truncate
                "output": output_data[:500],
                "success": success,
                "quality_score": quality_score,
                "error_message": error_message,
            }
        )

        # Keep only recent 50
        self.feedback_buffer[prompt_name] = self.feedback_buffer[prompt_name][-50:]

    def get_prompt(self, name: str, **kwargs) -> Tuple[str, str]:
        """Get formatted prompt with optional variables."""
        if name not in self.prompts:
            return "", ""

        prompt = self.prompts[name]
        template = prompt.template

        # Apply variables
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template, prompt.system_prompt

    def get_current_template(self, name: str) -> str:
        """Get current template for a prompt."""
        if name not in self.prompts:
            return ""
        return self.prompts[name].template

    def evolve_prompt(self, prompt_name: str) -> Optional[PromptTemplate]:
        """
        Evolveer een prompt gebaseerd op performance.
        """
        if prompt_name not in self.prompts:
            logger.warning(f"Prompt not found: {prompt_name}")
            return None

        prompt = self.prompts[prompt_name]

        # Get recent failures
        failures = [f for f in self.feedback_buffer[prompt_name] if not f["success"]]
        recent_failures = failures[-5:] if failures else []

        # Analyze common errors
        error_counts = defaultdict(int)
        for f in failures:
            error_msg = f.get("error_message", "unknown")
            error_counts[error_msg] += 1
        common_errors = [err for err, _ in sorted(error_counts.items(), key=lambda x: -x[1])[:3]]

        # Format few-shot examples
        few_shot_str = ""
        for ex in prompt.few_shot_examples[-3:]:
            few_shot_str += f"Input: {ex.get('input', '')[:200]}...\n"
            few_shot_str += f"Output: {ex.get('output', '')[:200]}...\n\n"

        # Format failures
        failures_str = ""
        for f in recent_failures:
            failures_str += f"Error: {f.get('error_message', 'unknown')}\n"
            failures_str += f"Input: {f['input'][:150]}...\n\n"

        success_rate = prompt.successes / prompt.uses if prompt.uses > 0 else 0

        # Build evolution prompt
        evolution_prompt = self.PROMPT_EVOLUTION_PROMPT.format(
            version=prompt.version,
            current_prompt=prompt.template[:2000],  # Limit length
            system_prompt=prompt.system_prompt[:500],
            num_examples=len(prompt.few_shot_examples),
            few_shot_examples=few_shot_str,
            total_uses=prompt.uses,
            success_rate=success_rate,
            avg_quality=prompt.avg_response_quality,
            common_errors=common_errors,
            recent_failures=failures_str if failures_str else "Geen recente failures",
        )

        try:
            response = self.multi_llm.generate(prompt=evolution_prompt, temperature=0.4)

            result = json.loads(response.text)

            # Store old version
            old_version = {
                "version": prompt.version,
                "template": prompt.template,
                "system_prompt": prompt.system_prompt,
                "few_shot_examples": prompt.few_shot_examples.copy(),
            }
            prompt.evolution_history.append(old_version)

            # Apply evolution
            if "new_template" in result:
                prompt.template = result["new_template"]
            if "new_system_prompt" in result:
                prompt.system_prompt = result["new_system_prompt"]
            if "new_few_shot_examples" in result:
                prompt.few_shot_examples = result["new_few_shot_examples"]

            prompt.version += 1

            # Log
            self.performance_log.append(
                {
                    "timestamp": datetime.now(),
                    "prompt_name": prompt_name,
                    "version": prompt.version,
                    "changes": result.get("changes_made", []),
                    "rationale": result.get("rationale", ""),
                }
            )

            logger.info(f"Prompt {prompt_name} evolved to v{prompt.version}")
            logger.info(f"Changes: {result.get('changes_made', [])}")

            return prompt

        except Exception as e:
            logger.error(f"Prompt evolution failed: {e}")
            return None

    def should_evolve(self, prompt_name: str, min_uses: int = 10) -> bool:
        """Check of prompt evolutie nodig is."""
        if prompt_name not in self.prompts:
            return False

        prompt = self.prompts[prompt_name]

        if prompt.uses < min_uses:
            return False

        success_rate = prompt.successes / prompt.uses if prompt.uses > 0 else 1.0

        # Evolve if success rate is low or quality is poor
        return success_rate < 0.7 or prompt.avg_response_quality < 6.0

    def get_evolution_report(self, prompt_name: str) -> Dict[str, Any]:
        """Genereer evolutie report."""
        if prompt_name not in self.prompts:
            return {}

        prompt = self.prompts[prompt_name]

        return {
            "prompt_name": prompt_name,
            "current_version": prompt.version,
            "total_uses": prompt.uses,
            "success_rate": prompt.successes / prompt.uses if prompt.uses > 0 else 0,
            "avg_quality": prompt.avg_response_quality,
            "evolution_count": len(prompt.evolution_history),
            "history": prompt.evolution_history,
            "current_template": (
                prompt.template[:500] + "..." if len(prompt.template) > 500 else prompt.template
            ),
        }

    def export_prompt_library(self) -> Dict[str, Dict]:
        """Export alle prompts als library."""
        return {
            name: {
                "version": p.version,
                "template": p.template,
                "system_prompt": p.system_prompt,
                "few_shot_examples": p.few_shot_examples,
                "performance": {
                    "uses": p.uses,
                    "success_rate": p.successes / p.uses if p.uses > 0 else 0,
                    "avg_quality": p.avg_response_quality,
                },
            }
            for name, p in self.prompts.items()
        }


# Singleton
_prompt_engine = None


def get_prompt_evolution() -> PromptEvolutionEngine:
    """Get singleton prompt evolution engine."""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEvolutionEngine()
    return _prompt_engine
