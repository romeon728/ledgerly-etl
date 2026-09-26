import re
import unicodedata


def clean_description_for_llm(raw_desc: str) -> str:
    """Strips bank boilerplate, gateway codes, phone numbers, dates,
    and alphanumeric reference tokens to isolate the merchant name for the LLM.
    """
    if not raw_desc:
        return ""

    # 0. NORMALIZE: Clean non-breaking spaces and collapse ALL spaces early.
    text = unicodedata.normalize("NFKC", str(raw_desc)).replace("\xa0", " ").upper()
    text = re.sub(r"\s+", " ", text).strip()

    # 1. DATES/PREFIX NUMBERS: Strip leading digits (glued or space-separated)
    text = re.sub(r"^\d+\s*", "", text)

    # 2. STANDALONE DATES: Strip 6-8 digit dates anywhere in the string
    text = re.sub(r"\b\d{6,8}\b", " ", text)

    # 3. BOILERPLATE: Strip common bank boilerplate & Zelle prefixes
    boilerplate_terms = [
        "VISA DDA PUR AP",
        "INTL DDA PUR AP",
        "DDA WITHDRAW AP",
        "TD ZELLE SENT",
        "ZELLE SENT",
        "ZELLE",
        "ACH RTL",
        "INTL T XN FEE",
        "NONTD",
    ]
    for term in boilerplate_terms:
        text = text.replace(term, " ")

    # 4. BANK HASHES: Strip alphanumeric reference tokens (e.g. 433600N0MA04, CW26339)
    # [A-Za-z0-9]* ensures the lookahead only searches for digits/letters within the current word.
    text = re.sub(r"\b(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{5,}\b", " ", text)

    # 5. PHONE NUMBERS: (e.g., 877 778 1161)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", " ", text)

    # 6. LOCATIONS: Strip state suffixes (* NY, * NJ)
    text = re.sub(r"\s*\*\s*[A-Z]{2}\b", " ", text)

    # 7. GLUED DIGITS: Strip trailing digits glued to words (e.g., DIRECT DEP1 -> DIRECT DEP)
    text = re.sub(r"(?<=[A-Za-z])\d+\b", "", text)

    # 8. STANDALONE NUMBERS: Store IDs, sequence numbers, rogue dates
    text = re.sub(r"\b\d+\b", " ", text)

    # 9. FINAL CLEANUP: Collapse spaces again and trim
    cleaned = re.sub(r"\s+", " ", text).strip()

    return cleaned if cleaned else raw_desc.strip()