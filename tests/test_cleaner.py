import pytest
from ledgerly.pipeline.cleaner import clean_description_for_llm


@pytest.mark.parametrize(
    "raw_input, expected_output",
    [
        # --- Debit & Credit Purchases with Noise ---
        (
            "VISA DDA PUR AP 403629   SPOTIFY     877 778 1161 * NY",
            "SPOTIFY",
        ),
        (
            "INTL DDA PUR AP 414361    UBER   TRIP   HELP UBER COM N LD",
            "UBER TRIP HELP UBER COM N LD",
        ),
        (
            "DDA WITHDRAW AP CW26339   TASTE BUENA RDGS          BUENA        * NJ",
            "TASTE BUENA RDGS BUENA",
        ),
        (
            "DDA WITHDRAW AP TW04B137   3850 SOUTH DELSEA DRIVE   VINELAND     * NJ",
            "SOUTH DELSEA DRIVE VINELAND",
        ),
        # --- Glued Dates & Payroll ---
        (
            "121824AGILE DECISION DIRECT DEP1",
            "AGILE DECISION DIRECT DEP",
        ),
        (
            "121624AGILE DECISION SPAYROLL   1",
            "AGILE DECISION SPAYROLL",
        ),
        (
            "AGILE DECISION DIRECT DEP",
            "AGILE DECISION DIRECT DEP",
        ),
        # --- Zelle Transfers & Alphanumeric Reference Tokens ---
        (
            "TD ZELLE SENT 433600N0MA04 Zelle JOSEPH ROMEO",
            "JOSEPH ROMEO",
        ),
        (
            "TD ZELLE SENT 433100H0J01Y Zelle NICHOLAS GIORDANO",
            "NICHOLAS GIORDANO",
        ),
        # --- Loan & Auto Payments with Dates/Codes ---
        (
            "TOYOTA ACH RTL 12202024",
            "TOYOTA",
        ),
        # --- ATM Fees & Bank Actions ---
        (
            "NONTD ATM FEE 55512341234",
            "ATM FEE",
        ),
        (
            "CAPITAL ONE MOBILE PMT",
            "CAPITAL ONE MOBILE PMT",
        ),
        (
            "DISCOVER E-PAYMENT",
            "DISCOVER E-PAYMENT",
        ),
        # --- Standard Clean Inputs ---
        (
            "Spotify",
            "SPOTIFY",
        ),
        (
            "FIRSTMARK PAYMENTS",
            "FIRSTMARK PAYMENTS",
        ),
        # --- Empty / Null / Edge Cases ---
        (
            "",
            "",
        ),
        (
            None,
            "",
        ),
    ],
)
def test_clean_description_for_llm(raw_input, expected_output):
    cleaned = clean_description_for_llm(raw_input)
    assert cleaned == expected_output


def test_clean_description_preserves_fallback():
    """Ensures that if cleaning strips all text, it falls back gracefully to original raw text."""
    weird_string = "12345678"
    cleaned = clean_description_for_llm(weird_string)
    assert cleaned == "12345678"