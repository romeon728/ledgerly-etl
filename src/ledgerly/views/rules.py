import pandas as pd
import streamlit as st
from ledgerly.db.rules import (
    add_category_pair,
    delete_category_pair,
    delete_rule,
    get_all_rules,
    get_categories_tree,
    insert_rule,
    update_rule,
)


def sort_subcategories(subcats: list[str]) -> list[str]:
    """Sort subcategories alphabetically with 'Other' pinned to the bottom."""
    return sorted(
        subcats,
        key=lambda x: (x.strip().lower() == "other", x.lower()),
    )


def render():
    st.title("📋 Category Management")

    if "rule_form_version" not in st.session_state:
        st.session_state["rule_form_version"] = 0

    form_ver = st.session_state["rule_form_version"]

    tab_rules, tab_categories = st.tabs(["Categorization Rules", "Category Taxonomy"])

    # ------------------------------------------------------------------
    # TAB 1: Rules Editor
    # ------------------------------------------------------------------
    with tab_rules:
        st.subheader("Add New Rule")

        categories_tree = get_categories_tree()
        cat_options = list(categories_tree.keys()) if categories_tree else ["Uncategorized"]

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            pattern = st.text_input(
                "Raw Description Contains/Matches",
                placeholder="e.g., Dunkin, Wawa, Chevron",
                key=f"rule_pattern_{form_ver}",
            )
        with col2:
            match_type = st.selectbox(
                "Match Type",
                ["contains", "exact", "regex"],
                key=f"rule_match_type_{form_ver}",
            )
        with col3:
            priority = st.number_input(
                "Priority",
                min_value=1,
                max_value=100,
                value=10,
                key=f"rule_priority_{form_ver}",
            )

        col4, col5, col6 = st.columns(3)
        with col4:
            target_merchant = st.text_input(
                "Target Merchant Name",
                placeholder="e.g., Dunkin' Donuts",
                key=f"rule_merchant_{form_ver}",
            )
        with col5:
            target_category = st.selectbox(
                "Target Category",
                options=cat_options,
                key=f"rule_target_category_{form_ver}",
            )
        with col6:
            raw_subcats = categories_tree.get(target_category, [])
            subcat_options = sort_subcategories(raw_subcats) if raw_subcats else ["Other"]

            target_subcategory = st.selectbox(
                "Target Subcategory",
                options=subcat_options,
                key=f"rule_target_subcategory_{target_category}_{form_ver}",
            )

        if st.button("Save Rule", type="primary"):
            if not pattern or not target_merchant:
                st.error("Pattern and Target Merchant are required.")
            else:
                rule_id, updated_count = insert_rule(
                    pattern=pattern,
                    match_type=match_type,
                    target_merchant=target_merchant,
                    target_category=target_category,
                    target_subcategory=target_subcategory,
                    priority=priority,
                    apply_to_existing=True,
                )
                st.session_state["rule_form_version"] += 1
                st.toast(f"Rule #{rule_id} created! Updated {updated_count} transaction(s).")
                st.rerun()

        st.divider()
        st.subheader("Existing Rules")

        rules = get_all_rules()
        if not rules:
            st.info("No rules defined yet.")
        else:
            df_rules = pd.DataFrame(rules)

            for _, row in df_rules.iterrows():
                rule_id = row["id"]
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6, r_col7 = st.columns([0.3, 2.2, 1.8, 2.2, 1, 1.2, 1])
                
                r_col2.write(f"`{row['pattern']}` ({row['match_type']})")
                r_col3.write(row["target_merchant"])
                r_col4.write(f"{row['target_category']} > {row['target_subcategory'] or 'N/A'}")
                r_col5.write(f"Prio: {row['priority']}")

                # EDIT POPOVER
                with r_col6:
                    with st.popover("✏️ Edit", use_container_width=True):
                        st.caption(f"Edit Rule #{rule_id}")

                        edit_pattern = st.text_input(
                            "Pattern",
                            value=row["pattern"],
                            key=f"edit_pattern_{rule_id}",
                        )
                        edit_match_type = st.selectbox(
                            "Match Type",
                            options=["contains", "exact", "regex"],
                            index=["contains", "exact", "regex"].index(row["match_type"])
                            if row["match_type"] in ["contains", "exact", "regex"]
                            else 0,
                            key=f"edit_match_type_{rule_id}",
                        )
                        edit_priority = st.number_input(
                            "Priority",
                            min_value=1,
                            max_value=100,
                            value=int(row["priority"]),
                            key=f"edit_priority_{rule_id}",
                        )
                        edit_merchant = st.text_input(
                            "Merchant Name",
                            value=row["target_merchant"],
                            key=f"edit_merchant_{rule_id}",
                        )

                        cat_idx = (
                            cat_options.index(row["target_category"])
                            if row["target_category"] in cat_options
                            else 0
                        )
                        edit_category = st.selectbox(
                            "Target Category",
                            options=cat_options,
                            index=cat_idx,
                            key=f"edit_category_{rule_id}",
                        )

                        edit_raw_subcats = categories_tree.get(edit_category, [])
                        edit_subcat_options = (
                            sort_subcategories(edit_raw_subcats)
                            if edit_raw_subcats
                            else ["Other"]
                        )
                        subcat_idx = (
                            edit_subcat_options.index(row["target_subcategory"])
                            if row["target_subcategory"] in edit_subcat_options
                            else 0
                        )

                        edit_subcategory = st.selectbox(
                            "Target Subcategory",
                            options=edit_subcat_options,
                            index=subcat_idx,
                            key=f"edit_subcategory_{rule_id}_{edit_category}",
                        )

                        if st.button("Save Changes", key=f"save_rule_{rule_id}", type="primary"):
                            updated_count = update_rule(
                                rule_id=rule_id,
                                pattern=edit_pattern,
                                match_type=edit_match_type,
                                target_merchant=edit_merchant,
                                target_category=edit_category,
                                target_subcategory=edit_subcategory,
                                priority=edit_priority,
                                apply_to_existing=True,
                            )
                            st.toast(f"Rule #{rule_id} updated! Updated {updated_count} transaction(s).")
                            st.rerun()

                # DELETE BUTTON
                with r_col7:
                    if st.button("Delete", key=f"del_rule_{rule_id}"):
                        delete_rule(rule_id)
                        st.toast(f"Deleted rule #{rule_id}")
                        st.rerun()

    # ------------------------------------------------------------------
    # TAB 2: Category Taxonomy
    # ------------------------------------------------------------------
    with tab_categories:
        st.subheader("Add Category & Subcategory Pair")
        with st.form("add_category_form", clear_on_submit=True):
            col_cat, col_subcat = st.columns(2)
            with col_cat:
                new_cat = st.text_input("Category Name", placeholder="e.g., Transportation")
            with col_subcat:
                new_subcat = st.text_input("Subcategory Name", placeholder="e.g., Fuel")

            if st.form_submit_button("Add Category Pair"):
                if new_cat and new_subcat:
                    add_category_pair(new_cat, new_subcat)
                    st.success(f"Added {new_cat} > {new_subcat} (and default 'Other')")
                    st.rerun()
                else:
                    st.error("Both Category and Subcategory are required.")

        st.divider()
        st.subheader("Current Taxonomy")
        categories_tree = get_categories_tree()

        for cat, subcats in categories_tree.items():
            sorted_subs = sort_subcategories(subcats)
            with st.expander(f"**{cat}** ({len(sorted_subs)} subcategories)"):
                col_info, col_del_cat = st.columns([3, 1])
                with col_del_cat:
                    with st.popover("🗑️ Delete Category", use_container_width=True):
                        st.caption(f"Delete **{cat}** and all {len(sorted_subs)} subcategories?")
                        if st.button("Confirm Delete", key=f"confirm_del_cat_{cat}", type="primary"):
                            delete_category_pair(cat)
                            st.toast(f"Deleted category '{cat}'")
                            st.rerun()

                st.markdown("---")

                for sub in sorted_subs:
                    sub_col1, sub_col2 = st.columns([4, 1])
                    sub_col1.write(f"• {sub}")

                    if sub.strip().lower() != "other":
                        if sub_col2.button("🗑️", key=f"del_subcat_{cat}_{sub}", help=f"Delete {sub}"):
                            delete_category_pair(cat, sub)
                            st.toast(f"Deleted {cat} > {sub}")
                            st.rerun()