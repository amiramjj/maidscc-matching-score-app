import streamlit as st
import pandas as pd

# -------------------------------
# Matching Score Function (same as before)
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
# Explanation Function (expandable later for all features)
# -------------------------------
def explain_row_score(row):
    explanations = {"positive": [], "negative": []}

    # Household
    if row["clientmts_household_type"] == "baby" and row["maidmts_household_type"] != "refuses_baby":
        explanations["positive"].append("Client requires baby care, maid accepts baby households.")
    elif row["clientmts_household_type"] == "baby":
        explanations["negative"].append("Client requires baby care, maid refuses baby households.")

    if row["clientmts_household_type"] == "many_kids" and row["maidmts_household_type"] != "refuses_many_kids":
        explanations["positive"].append("Client has many kids, maid accepts large households.")
    elif row["clientmts_household_type"] == "many_kids":
        explanations["negative"].append("Client has many kids, maid refuses large households.")

    # Pets
    if row["clientmts_pet_type"] == "cat" and row["maidmts_pet_type"] != "refuses_cat":
        explanations["positive"].append("Client has cats, maid accepts cats.")
    elif row["clientmts_pet_type"] == "cat":
        explanations["negative"].append("Client has cats, maid refuses cats.")

    if row["clientmts_pet_type"] == "dog" and row["maidmts_pet_type"] != "refuses_dog":
        explanations["positive"].append("Client has dogs, maid accepts dogs.")
    elif row["clientmts_pet_type"] == "dog":
        explanations["negative"].append("Client has dogs, maid refuses dogs.")

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

    # Compute scores
    df["match_score"] = df.apply(calculate_row_score, axis=1)
    df["match_score_pct"] = df["match_score"] * 100

    # Show all scores
    st.subheader("All Match Scores")
    st.dataframe(df[["client_name", "maid_id", "match_score_pct"]])

    # Filters for explanation
    st.subheader("Detailed Explanation")
    client_choice = st.selectbox("Select Client", df["client_name"].unique())
    maid_choice = st.selectbox("Select Maid", df[df["client_name"] == client_choice]["maid_id"].unique())

    selected_row = df[(df["client_name"] == client_choice) & (df["maid_id"] == maid_choice)].iloc[0]
    explanations = explain_row_score(selected_row)

    st.write(f"**Match Score:** {selected_row['match_score_pct']:.1f}%")

    with st.expander("Positive Matches"):
        if explanations["positive"]:
            for r in explanations["positive"]:
                st.write(f"- {r}")
        else:
            st.write("No strong positive matches found.")

    with st.expander("Negative Mismatches"):
        if explanations["negative"]:
            for r in explanations["negative"]:
                st.write(f"- {r}")
        else:
            st.write("No critical mismatches found.")
