import psycopg2
import re
import pandas as pd

from psycopg2.extras import RealDictCursor
from ledgerly.db.connection import get_db_connection, get_db_cursor


def get_all_rules():
    """Fetch all categorization rules ordered by priority."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, pattern, match_type, target_merchant, 
                       target_category, target_subcategory, priority
                FROM categorization_rules
                ORDER BY target_category, target_subcategory, target_merchant, match_type
            """
            )
            return cur.fetchall()


def insert_rule(
    pattern: str,
    target_merchant: str,
    target_category: str,
    target_subcategory: str = None,
    match_type: str = "contains",
    priority: int = 10,
) -> int:
    """Insert a new categorization rule."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO categorization_rules 
                    (pattern, match_type, target_merchant, target_category, target_subcategory, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """,
                (
                    pattern.strip(),
                    match_type,
                    target_merchant.strip(),
                    target_category.strip(),
                    target_subcategory.strip() if target_subcategory else None,
                    priority,
                ),
            )
            rule_id = cur.fetchone()[0]
            conn.commit()
            return rule_id


def delete_rule(rule_id: int):
    """Delete a categorization rule by ID."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM categorization_rules WHERE id = %s;", (rule_id,))
            conn.commit()


def get_categories_tree() -> dict[str, list[str]]:
    """Fetch categories and subcategories grouped and sorted, keeping 'Other' at the bottom."""
    tree: dict[str, list[str]] = {}
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, subcategory FROM categories ORDER BY name, subcategory;")
            for cat, subcat in cur.fetchall():
                if cat not in tree:
                    tree[cat] = []
                if subcat and subcat not in tree[cat]:
                    tree[cat].append(subcat)

    # Sort subcategories alphabetically, but push 'Other' to the very end
    for cat in tree:
        tree[cat] = sorted(
            tree[cat],
            key=lambda x: (x.strip().lower() == "other", x.lower())
        )

    return tree

def add_category_pair(category: str, subcategory: str) -> None:
    """Add a category and subcategory pair, automatically ensuring 'Other' exists for the category."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Insert the primary requested pair
            cur.execute(
                "INSERT INTO categories (name, subcategory) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (category, subcategory),
            )
            # 2. Guarantee 'Other' is added as a default fallback subcategory
            if subcategory.strip().lower() != "other":
                cur.execute(
                    "INSERT INTO categories (name, subcategory) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                    (category, "Other"),
                )
            conn.commit()

def get_allowed_categories() -> list[str]:
    """Fetch unique category names from database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT name FROM categories ORDER BY name;")
            return [row[0] for row in cur.fetchall()]


def get_allowed_subcategories() -> list[str]:
    """Fetch unique subcategory names from database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT subcategory FROM categories ORDER BY subcategory;")
            return [row[0] for row in cur.fetchall()]

def apply_rule_to_existing_transactions(
    pattern: str,
    match_type: str,
    target_merchant: str,
    target_category: str,
    target_subcategory: str = None,
) -> int:
    """Retroactively update all existing transactions that match this rule."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if match_type == "exact":
                where_clause = "description ILIKE %s"
                match_val = pattern.strip()
            elif match_type == "regex":
                where_clause = "description ~* %s"
                match_val = pattern.strip()
            else:  # default 'contains'
                where_clause = "description ILIKE %s"
                match_val = f"%{pattern.strip()}%"

            query = f"""
                UPDATE transactions
                SET merchant = %s,
                    category = %s,
                    subcategory = %s,
                    source = 'rule_match'
                WHERE {where_clause};
            """
            cur.execute(
                query,
                (
                    target_merchant.strip(),
                    target_category.strip(),
                    target_subcategory.strip() if target_subcategory else None,
                    match_val,
                ),
            )
            updated_count = cur.rowcount
            conn.commit()
            return updated_count


def insert_rule(
    pattern: str,
    target_merchant: str,
    target_category: str,
    target_subcategory: str = None,
    match_type: str = "contains",
    priority: int = 10,
    apply_to_existing: bool = True,
) -> tuple[int, int]:
    """Insert rule and optionally apply it to existing matching transactions."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO categorization_rules 
                    (pattern, match_type, target_merchant, target_category, target_subcategory, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """,
                (
                    pattern.strip(),
                    match_type,
                    target_merchant.strip(),
                    target_category.strip(),
                    target_subcategory.strip() if target_subcategory else None,
                    priority,
                ),
            )
            rule_id = cur.fetchone()[0]
            conn.commit()

    updated_count = 0
    if apply_to_existing:
        updated_count = apply_rule_to_existing_transactions(
            pattern=pattern,
            match_type=match_type,
            target_merchant=target_merchant,
            target_category=target_category,
            target_subcategory=target_subcategory,
        )

    return rule_id, updated_count

def get_category_taxonomy() -> dict[str, list[str]]:
    """Fetch category to subcategory mapping dynamically from PostgreSQL."""
    taxonomy: dict[str, list[str]] = {}
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, subcategory FROM categories ORDER BY name, subcategory;")
            for cat, subcat in cur.fetchall():
                if cat not in taxonomy:
                    taxonomy[cat] = []
                if subcat and subcat not in taxonomy[cat]:
                    taxonomy[cat].append(subcat)
    return taxonomy

def get_rules_df() -> pd.DataFrame:
    query = """
        SELECT
            id,
            pattern,
            match_type,
            target_merchant,
            target_category,
            target_subcategory,
            priority,
            created_at
        FROM categorization_rules
        ORDER BY target_category DESC;
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(query)
        return pd.DataFrame(
            cur.fetchall(), 
            columns=[desc[0] for desc in cur.description])

def delete_category_pair(category: str, subcategory: str | None = None) -> int:
    """Delete a specific subcategory pair or an entire category from PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if subcategory:
                cur.execute(
                    "DELETE FROM categories WHERE name = %s AND subcategory = %s;",
                    (category, subcategory),
                )
            else:
                cur.execute(
                    "DELETE FROM categories WHERE name = %s;",
                    (category,),
                )
            count = cur.rowcount
            conn.commit()
            return count

def apply_rules_to_all_transactions() -> int:
    """Re-evaluate all active rules against transactions in priority order."""
    rules = get_all_rules()  # Assumes get_all_rules() returns rules sorted by priority
    if not rules:
        return 0

    updated_total = 0
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT transaction_id, description FROM transactions;")
            transactions = cur.fetchall()

            for tx_id, raw_desc in transactions:
                if not raw_desc:
                    continue

                for rule in rules:
                    pattern = rule["pattern"]
                    match_type = rule["match_type"]
                    matched = False

                    if match_type == "contains" and pattern.lower() in raw_desc.lower():
                        matched = True
                    elif match_type == "exact" and pattern.lower() == raw_desc.strip().lower():
                        matched = True
                    elif match_type == "regex":
                        try:
                            if re.search(pattern, raw_desc, re.IGNORECASE):
                                matched = True
                        except re.error:
                            pass

                    if matched:
                        cur.execute(
                            """
                            UPDATE transactions
                            SET merchant = %s,
                                category = %s,
                                subcategory = %s
                            WHERE transaction_id = %s;
                            """,
                            (
                                rule["target_merchant"],
                                rule["target_category"],
                                rule["target_subcategory"],
                                tx_id,
                            ),
                        )
                        updated_total += cur.rowcount
                        break  # Stop checking rules once highest priority match is applied

        conn.commit()

    return updated_total


def update_rule(
    rule_id: int,
    pattern: str,
    match_type: str,
    target_merchant: str,
    target_category: str,
    target_subcategory: str,
    priority: int,
    apply_to_existing: bool = True,
) -> int:
    """Update an existing rule in PostgreSQL and optionally re-apply all rules."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE categorization_rules
                SET pattern = %s,
                    match_type = %s,
                    target_merchant = %s,
                    target_category = %s,
                    target_subcategory = %s,
                    priority = %s
                WHERE id = %s;
                """,
                (
                    pattern,
                    match_type,
                    target_merchant,
                    target_category,
                    target_subcategory,
                    priority,
                    rule_id,
                ),
            )
            conn.commit()

    updated_count = 0
    if apply_to_existing:
        updated_count = apply_rules_to_all_transactions()

    return updated_count