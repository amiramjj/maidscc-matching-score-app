import streamlit as st
import pandas as pd

# -------------------------------
# Matching Score Function
# -------------------------------
def calculate_row_score(row):
    score = 0.0
    weight_strong = 0.6
    weight_moderate = 0.3
    weight_bonus = 0.1
    max_score = 0.0

    # Household Type
    c_house = row["clientmts_household_type"]
    m_house = row["maidmts_household_type"]
    if c_house != "unspecified":
        max_score += weight_strong
        if (
            (c_house == "baby" and m_house != "refuses_baby") or
            (c_house == "many_kids" and m_house != "refuses_many_kids") or
            (c_house == "baby_and_kids" and m_house != "refuses_baby_and_kids")
        ):
            score += weight_strong

    # Pets
    c_pets = row["clientmts_pet_type"]
    m_pets = row["maidmts_pet_type"]
    if c_pets != "no_pets":
        max_score += weight_strong
        if (
            (c_pets == "cat" and m_pets != "refuses_cat") or
            (c_pets == "dog" and m_pets != "refuses_dog") or
            (c_pets == "both" and m_pets != "refuses_both_pets")
        ):
            score += weight_strong

    # Day-off Policy
    c_dayoff = row["clientmts_dayoff_policy"]
    m_dayoff = row["maidmts_dayoff_policy"]
    if c_dayoff != "unspecified":
        max_score += weight_strong
        if c_dayoff not in ["", "unspecified"] and m_dayoff != "refuses_fixed_sunday":
            score += weight_strong

    # Living Arrangement
    c_living = row["clientmts_living_arrangement"]
    m_living = row["maidmts_living_arrangement"]
    if c_living != "unspecified":
        max_score += weight_strong
        if (
            ("private_room" in c_living and "requires_no_private_room" not in m_living)
            and ("abu_dhabi" in c_living and "refuses_abu_dhabi" not in m_living)
        ):
            score += weight_strong

    # Nationality
    if "maid_nationality" in row and row["clientmts_nationality_preference"] != "any":
        max_score += weight_moderate
        if row["clientmts_nationality_preference"] in str(row["maid_nationality"]):
            score += weight_moderate

    # Cuisine
    c_cuisine = row["clientmts_cuisine_preference"]
    m_cooking = str(row.get("cooking_group", "not_specified"))
    if c_cuisine != "unspecified" and m_cooking != "not_specified":
        max_score += weight_moderate
        c_set = set(c_cuisine.split("+"))
        m_set = set(m_cooking.split("+"))
        if c_set & m_set:
            score += weight_moderate

    # Special cases
    c_special = row["clientmts_special_cases"]
    m_care = row["maidpref_caregiving_profile"]
    if c_special != "unspecified":
        max_score += weight_bonus
        if (
            (c_special == "elderly" and m_care in ["elderly_experienced", "elderly_and_special"]) or
            (c_special == "special_needs" and m_care in ["special_needs", "elderly_and_special"]) or
            (c_special == "elderly_and_special" and m_care == "elderly_and_special")
        ):
            score += weight_bonus

    # Kids experience
    if c_house in ["baby", "many_kids", "baby_and_kids"]:
        max_score += weight_bonus
        if (
            (c_house == "baby" and row["maidpref_kids_experience"] in ["lessthan2", "both"]) or
            (c_house == "many_kids" and row["maidpref_kids_experience"] in ["above2", "both"]) or
            (c_house == "baby_and_kids" and row["maidpref_kids_experience"] == "both")
        ):
            score += weight_bonus

    # Pets handling
    if c_pets != "no_pets":
        max_score += weight_bonus
        if (
            (c_pets == "cat" and row["maidpref_pet_handling"] in ["cats", "both"]) or
            (c_pets == "dog" and row["maidpref_pet_handling"] in ["dogs", "both"]) or
            (c_pets == "both" and row["maidpref_pet_handling"] == "both")
        ):
            score += weight_bonus

    # Vegetarian / lifestyle
    if "veg" in c_cuisine:
        max_score += weight_bonus
        if "veg_friendly" in str(row["maidpref_personality"]):
            score += weight_bonus

    # Smoking
    max_score += weight_bonus
    if row["maidpref_smoking"] == "non_smoker":
        score += weight_bonus

    if max_score > 0:
        return score / max_score
    return 0.0


# -------------------------------
# Expanded Explanation Function
# -------------------------------
def explain_row_score(row):
    explanations = {"positive": [], "negative": [], "neutral": []}

    # Household
    c_house = row.get("clientmts_household_type", "unspecified")
    m_house = row.get("maidmts_household_type", "unspecified")
    if c_house != "unspecified":
        if c_house == "baby" and m_house != "refuses_baby":
            explanations["positive"].append("Client wants baby care, maid accepts it.")
        elif c_house == "baby":
            explanations["negative"].append("Client wants baby care, maid refuses it.")
        elif c_house == "many_kids" and m_house != "refuses_many_kids":
            explanations["positive"].append("Client has many kids, maid accepts it.")
        elif c_house == "many_kids":
            explanations["negative"].append("Client has many kids, maid refuses it.")
    else:
        explanations["neutral"].append("Client did not specify household type.")

    # Pets
    c_pets = row.get("clientmts_pet_type", "no_pets")
    m_pets = row.get("maidmts_pet_type", "unspecified")
    if c_pets != "no_pets":
        if c_pets == "cat" and m_pets != "refuses_cat":
            explanations["positive"].append("Client has cats, maid accepts cats.")
        elif c_pets == "cat":
            explanations["negative"].append("Client has cats, maid refuses cats.")
        elif c_pets == "dog" and m_pets != "refuses_dog":
            explanations["positive"].append("Client has dogs, maid accepts dogs.")
        elif c_pets == "dog":
            explanations["negative"].append("Client has dogs, maid refuses dogs.")
    else:
        explanations["neutral"].append("Client did not specify pets.")

    # Day-off
    c_dayoff = row.get("clientmts_dayoff_policy", "unspecified")
    m_dayoff = row.get("maidmts_dayoff_policy", "unspecified")
    if c_dayoff != "unspecified":
        if m_dayoff != "refuses_fixed_sunday":
            explanations["positive"].append("Client specified day-off, maid accepts flexible policy.")
        else:
            explanations["negative"].append("Client specified day-off, maid refuses fixed Sunday.")
    else:
        explanations["neutral"].append("Client did not specify day-off policy.")

    # Living arrangement
    c_living = row.get("clientmts_living_arrangement", "unspecified")
    m_living = row.get("maidmts_living_arrangement", "unspecified")
    if c_living != "unspecified":
        if ("private_room" in str(c_living) and "requires_no_private_room" not in str(m_living)):
            explanations["positive"].append("Client requires private room, maid accepts it.")
        else:
            explanations["negative"].append("Client requires private room, maid refuses it.")
    else:
        explanations["neutral"].append("Client did not specify living arrangement.")

    # Nationality
    c_nat = row.get("clientmts_nationality_preference", "any")
    m_nat = str(row.get("maid_nationality", "unspecified"))
    if c_nat != "any":
        if c_nat in m_nat:
            explanations["positive"].append(f"Client prefers {c_nat}, maid matches it.")
        else:
            explanations["negative"].append(f"Client prefers {c_nat}, maid does not match.")
    else:
        explanations["neutral"].append("Client did not specify nationality preference.")

    # Cuisine
    c_cuisine = row.get("clientmts_cuisine_preference", "unspecified")
    m_cooking = str(row.get("cooking_group", "not_specified"))
    if c_cuisine != "unspecified" and m_cooking != "not_specified":
        c_set = set(str(c_cuisine).split("+"))
        m_set = set(m_cooking.split("+"))
        if c_set & m_set:
            explanations["positive"].append("Client cuisine preference matches maid cooking skills.")
        else:
            explanations["negative"].append("Client cuisine preference does not match maid cooking skills.")
    else:
        explanations["neutral"].append("Client did not specify cuisine preference.")

    # Special cases
    c_special = row.get("clientmts_special_cases", "unspecified")
    m_care = row.get("maidpref_caregiving_profile", "unspecified")
    if c_special != "unspecified":
        if (
            (c_special == "elderly" and m_care in ["elderly_experienced", "elderly_and_special"]) or
            (c_special == "special_needs" and m_care in ["special_needs", "elderly_and_special"]) or
            (c_special == "elderly_and_special" and m_care == "elderly_and_special")
        ):
            explanations["positive"].append("Client requires caregiving, maid has relevant experience.")
        else:
            explanations["negative"].append("Client requires caregiving, maid lacks the required experience.")
    else:
        explanations["neutral"].append("Client did not specify caregiving needs.")

    # Smoking
    m_smoke = row.get("maidpref_smoking", "unspecified")
    if m_smoke == "non_smoker":
        explanations["positive"].append("Maid is a non-smoker.")
    else:
        explanations["neutral"].append("Maid profile indicates smoking tolerance or unspecified.")

    return explanations
# -------------------------------
# Streamlit UI
# -------------------------------
st.title("Maids.cc Matching Score App")

uploaded_file = st.file_uploader("Upload dataset (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Compute scores for tagged pairs
    df["match_score"] = df.apply(calculate_row_score, axis=1)
    df["match_score_pct"] = df["match_score"] * 100

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "All Match Scores (tagged pairs)", 
        "Best Maid per Client (Global Search)", 
        "Maid Profiles"
    ])

    # -------------------------------
    # Tab 1: Tagged pairs
    # -------------------------------
    with tab1:
        st.subheader("All Match Scores (tagged pairs)")
        st.dataframe(df[["client_name", "maid_id", "match_score_pct"]])

        # --- Explanation block for tagged pairs ---
        st.subheader("Explain a Tagged Pair Match")
        sel_idx = st.selectbox("Choose a row", df.index, format_func=lambda i: f"{df.loc[i,'client_name']} ↔ {df.loc[i,'maid_id']}")
        sel_row = df.loc[sel_idx].to_dict()

        st.write(f"**Client:** {sel_row['client_name']}  \n**Maid:** {sel_row['maid_id']}  \n**Score:** {sel_row['match_score_pct']:.1f}%")

        explanations = explain_row_score(sel_row)

        with st.expander("Positive Matches"):
            for r in explanations["positive"]:
                st.write(f"- {r}")

        with st.expander("Negative Mismatches"):
            for r in explanations["negative"]:
                st.write(f"- {r}")

        with st.expander("Neutral Notes"):
            for r in explanations["neutral"]:
                st.write(f"- {r}")


    # -------------------------------
    # Tab 2: Best Maid per Client (Global Search)
    # -------------------------------
    with tab2:
        st.subheader("Best Maid per Client (Global Search Across All Maids)")

        @st.cache_data
        def compute_best_matches(df):
            clients_df = df.drop_duplicates(subset=["client_name"]).copy()
            maids_df = df.drop_duplicates(subset=["maid_id"]).copy()
        
            best_matches = []
        
            for _, client_row in clients_df.iterrows():
                best_score = -1
                best_maid = None
                best_combined = None
        
                for _, maid_row in maids_df.iterrows():
                    # Build a combined row: clientmts_* from client, maidmts_/maidpref_ from maid
                    combined = {}
                    for col in df.columns:
                        if col.startswith("clientmts_"):
                            combined[col] = client_row[col]
                        elif col.startswith("maidmts_") or col.startswith("maidpref_") or col.startswith("maid_"):
                            combined[col] = maid_row[col]
        
                    score = calculate_row_score(combined)
                    if score > best_score:
                        best_score = score
                        best_maid = maid_row["maid_id"]
                        best_combined = combined
        
                best_matches.append({
                    "client_name": client_row["client_name"],
                    "best_maid_id": best_maid,
                    "match_score_pct": best_score * 100,
                    "combined": best_combined
                })
        
            return pd.DataFrame(best_matches)


        best_client_df = compute_best_matches(df)
        st.dataframe(best_client_df[["client_name", "best_maid_id", "match_score_pct"]])

        # Explanation
        st.subheader("Explain a Best Match (Global Search)")
        client_sel = st.selectbox("Choose Client", best_client_df["client_name"].unique())
        best_row = best_client_df[best_client_df["client_name"] == client_sel].iloc[0]

        st.write(f"**Best Maid:** {best_row['best_maid_id']}  \n**Match Score:** {best_row['match_score_pct']:.1f}%")

        explanations = explain_row_score(best_row["combined"])
        with st.expander("Positive Matches"):
            for r in explanations["positive"]:
                st.write(f"- {r}")
        with st.expander("Negative Mismatches"):
            for r in explanations["negative"]:
                st.write(f"- {r}")
        with st.expander("Neutral Notes"):
            for r in explanations["neutral"]:
                st.write(f"- {r}")

    # -------------------------------
    # Tab 3: Maid Profile Explorer
    # -------------------------------
    with tab3:
        st.subheader("Maid Profile Explorer")
    
        # Keep only maid-specific columns
        maid_cols = [col for col in df.columns if col.startswith("maidmts_") or 
                     col.startswith("maidpref_") or col.startswith("maid_")]
    
        # Build maid profiles dataframe
        maids_df = df[["maid_id"] + maid_cols].drop_duplicates(subset=["maid_id"]).reset_index(drop=True)
    
        # Dropdown of unique maid IDs
        maid_options = maids_df["maid_id"].dropna().astype(str).unique().tolist()
        selected_maid = st.selectbox("Choose a Maid ID", maid_options)
    
        # Display selected maid profile
        maid_profile = maids_df[maids_df["maid_id"].astype(str) == selected_maid].iloc[0]
    
        st.markdown(f"### Maid ID: {selected_maid}")
        for col in maid_cols:
            st.write(f"**{col}:** {maid_profile[col]}")
