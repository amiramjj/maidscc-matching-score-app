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
# Streamlit UI
# -------------------------------
st.title("Maids.cc Matching Score App")

uploaded_file = st.file_uploader("Upload dataset (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Compute scores for tagged pairs (Tab 1)
    df["match_score"] = df.apply(calculate_row_score, axis=1)
    df["match_score_pct"] = df["match_score"] * 100

    # Tabs
    tab1, tab2 = st.tabs(["All Match Scores (tagged pairs)", "Best Maid per Client (Global Search)"])
    # Tabs
    tab1, tab2 = st.tabs(["All Match Scores (tagged pairs)", "Best Maid per Client (Global Search)"])
    
    # -------------------------------
    # Tab 1: Tagged pairs
    # -------------------------------
    with tab1:
        st.subheader("All Match Scores (tagged pairs)")
        st.dataframe(df[["client_name", "maid_id", "match_score_pct"]])
    
    # -------------------------------
    # Tab 2: Best Maid per Client (Global Search Across All Maids)
    # -------------------------------
    with tab2:
        st.subheader("Best Maid per Client (Global Search Across All Maids)")
    
        @st.cache_data
        def compute_global_matches(df):
            # Unique profiles
            clients_df = df.drop_duplicates(subset=["client_name"]).copy()
            maids_df = df.drop_duplicates(subset=["maid_id"]).copy()
    
            # Add key for cross join
            clients_df["key"] = 1
            maids_df["key"] = 1
    
            # Cross join (client × maid)
            cross = clients_df.merge(maids_df, on="key", suffixes=("_client", "_maid")).drop("key", axis=1)
    
            # Compute scores
            all_pairs = []
            for _, row in cross.iterrows():
                combined = {}
                # take all client features with "clientmts_" prefix
                for col in df.columns:
                    if col.startswith("clientmts_"):
                        combined[col] = row[f"{col}_client"] if f"{col}_client" in row else row[col]
                # take all maid features with "maidmts_" or "maidpref_" prefix
                for col in df.columns:
                    if col.startswith("maidmts_") or col.startswith("maidpref_") or col.startswith("maid_"):
                        combined[col] = row[f"{col}_maid"] if f"{col}_maid" in row else row[col]
    
                score = calculate_row_score(combined)
                all_pairs.append({
                    "client_name": row["client_name_client"],
                    "maid_id": row["maid_id_maid"],
                    "match_score": score,
                    "match_score_pct": score * 100,
                    "combined": combined
                })
    
            return pd.DataFrame(all_pairs)
    
        pairwise_df = compute_global_matches(df)
    
        # Best maid per client
        best_client_df = pairwise_df.loc[pairwise_df.groupby("client_name")["match_score"].idxmax()]
        st.dataframe(best_client_df[["client_name", "maid_id", "match_score_pct"]])
    
        # -------------------------------
        # Explanation for best matches
        # -------------------------------
        st.subheader("Explain a Best Match (Global Search)")
    
        client_sel = st.selectbox("Choose Client", best_client_df["client_name"].unique())
        best_row = best_client_df[best_client_df["client_name"] == client_sel].iloc[0]
    
        st.write(f"**Best Maid:** {best_row['maid_id']}  \n**Match Score:** {best_row['match_score_pct']:.1f}%")
    
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
