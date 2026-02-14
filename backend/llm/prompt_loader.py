import os
from typing import Dict, Any


class PromptLoader:
    def __init__(self, prompts_dir: str = "prompts"):
        # Pad resolven relatief aan de project root
        self.base_path = os.path.join(os.getcwd(), prompts_dir)
        # Fallback voor als we in backend/ draaien
        if not os.path.exists(self.base_path):
            self.base_path = os.path.join(os.getcwd(), "..", prompts_dir)

    def load_prompt(self, prompt_name: str, variables: Dict[str, Any] = None) -> str:
        """
        Laadt een prompt file (bijv. 'sentiment_analysis.md') en vervangt variabelen {{var}}.
        """
        file_path = os.path.join(self.base_path, prompt_name)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simpele template engine (kan vervangen worden door Jinja2)
            if variables:
                for key, value in variables.items():
                    content = content.replace(f"{{{{{key}}}}}", str(value))

            return content
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
