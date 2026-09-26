from pathlib import Path
from ledgerly.inference.schema import ALLOWED_CATEGORIES, ALLOWED_SUBCATEGORIES

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def build_system_prompt() -> str:
    categories_str = "\n".join(f"- {c}" for c in ALLOWED_CATEGORIES)
    subcategories_str = "\n".join(f"- {s}" for s in ALLOWED_SUBCATEGORIES)
    
    template_path = PROMPTS_DIR / "system_prompt.txt"
    template_content = template_path.read_text(encoding="utf-8")
    
    # Simple replacement: 100% immune to curly braces and dollar signs
    return (
        template_content
        .replace("{categories_str}", categories_str)
        .replace("{subcategories_str}", subcategories_str)
    )

def build_user_prompt(description: str, amount: float, account_type: str = "Checking") -> str:
    template_path = PROMPTS_DIR / "user_prompt.txt"
    template_content = template_path.read_text(encoding="utf-8")
    
    return (
        template_content
        .replace("{description}", description)
        .replace("{amount}", str(amount))
        .replace("{account_type}", account_type)
    )