import streamlit as st
import pandas as pd

# -------------------------------
# Matching Score Function (with normalization)
# -------------------------------
def calculate_row_score(row):
    score = 0.0
    weight_strong = 0.6
    weight_moderate = 0.3
    weight_bonus = 0.1
    max_score = 0.0

    # Household Type
    c_house = row.get("clientmts_household_type", "unspecified")
    m_house = row.get("maidmts_household_type", "no_restriction_household_type")
    if c_house != "unspecified":
        max_score += weight_strong
        if (
            (c_house == "baby" and m_house != "refuses_baby") or
            (c_house == "many_kids" and m_house != "refuses_many_kids") or
            (c_house == "baby_and_kids" and m_house != "refuses_baby_and_kids")
        ):
            score += weight_strong

    # Pets
    c_pets = row.get("clientmts_pet_type", "no_pets")
    m_pets = row.get("maidmts_pet_type", "no_restriction_pets")
    if c_pets != "no_pets":
        max_score += weight_strong
        if (
            (c_pets == "cat" and m_pets != "refuses_cat") or
            (c_pets == "dog" and m_pets != "refuses_dog") or
            (c_pets == "both" and m_pets != "refuses_both_pets")
        ):
            score += weight_strong

    # Day-off Policy
    c_dayoff = row.get("clientmts_dayoff_policy", "unspecified")
    m_dayoff = row.get("maidmts_dayoff_policy", "no_restriction_dayoff")
    if c_dayoff != "unspecified":
        max_score += weight_strong
        if c_dayoff not in ["", "unspecified"] and m_dayoff != "refuses_fixed_sunday":
            score += weight_strong

    # Living Arrangement
    c_living = row.get("clientmts_living_arrangement", "unspecified")
    m_living = row.get("maidmts_living_arrangement", "no_restriction_living_arrangement")
    if c_living != "unspecified":
        max_score += weight_strong
        if (
            ("private_room" in c_living and "requires_no_private_room" not in m_living)
            and ("abu_dhabi" in c_living and "refuses_abu_dhabi" not in m_living)
        ):
            score += weight_strong

    # Nationality
    if "maid_nationality" in row and row.get("clientmts_nationality_preference", "any") != "any":
        max_score += weight_moderate
        if row["clientmts_nationality_preference"] in str(row["maid_nationality"]):
            score += weight_moderate

    # Cuisine
    c_cuisine = row.get("clientmts_cuisine_preference", "unspecified")
    m_cooking = str(row.get("cooking_group", "not_specified"))
    if c_cuisine != "unspecified" and m_cooking != "not_specified":
        max_score += weight_moderate
        c_set = set(c_cuisine.split("+"))
        m_set = set(m_cooking.split("+"))
        if c_set & m_set:
            score += weight_moderate

    # Special cases
    c_special = row.get("clientmts_special_cases", "unspecified")
    m_care = row.get("maidpref_caregiving_profile", "unspecified")
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
            (c_house == "baby" and row.get("maidpref_kids_experience") in ["lessthan2", "both"]) or
            (c_house == "many_kids" and row.get("maidpref_kids_experience") in ["above2", "both"]) or
            (c_house == "baby_and_kids" and row.get("maidpref_kids_experience") == "both")
        ):
            score += weight_bonus

    # Pets handling
    if c_pets != "no_pets":
        max_score += weight_bonus
        if (
            (c_pets == "cat" and row.get("maidpref_pet_handling") in ["cats", "both"]) or
            (c_pets == "dog" and row.get("maidpref_pet_handling") in ["dogs", "both"]) or
            (c_pets == "both" and row.get("maidpref_pet_handling") == "both")
        ):
            score += weight_bonus

    # Vegetarian / lifestyle
    if "veg" in c_cuisine:
        max_score += weight_bonus
        if "veg_friendly" in str(row.get("maidpref_personality", "")):
            score += weight_bonus

    # Smoking
    max_score += weight_bonus
    if row.get("maidpref_smoking") == "non_smoker":
        score += weight_bonus

    if max_score > 0:
        return score / max_score
    return 0.0


# -------------------------------
# Explanation Function (full coverage)
# -------------------------------
def explain_row_score(row):
    explanations = {"positive": [], "negative": []}

    # Household
    c_house = row.get("clientmts_household_type", "unspecified")
    m_house = row.get("maidmts_household_type", "no_restriction_household_type")
    if c_house == "baby":
        if m_house == "refuses_baby":
            explanations["negative"].append("Client has a baby, maid refuses baby households.")
        else:
            explanations["positive"].append("Client has a baby, maid accepts.")
    elif c_house == "many_kids":
        if m_house == "refuses_many_kids":
            explanations["negative"].append("Client has many kids, maid refuses large households.")
        else:
            explanations["positive"].append("Client has many kids, maid accepts.")
    elif c_house == "baby_and_kids":
        if m_house == "refuses_baby_and_kids":
            explanations["negative"].append("Client has baby and kids, maid refuses.")
        else:
            explanations["positive"].append("Client has baby and kids, maid accepts.")

    # Pets
    c_pets = row.get("clientmts_pet_type", "no_pets")
    m_pets = row.get("maidmts_pet_type", "no_restriction_pets")
    if c_pets == "cat":
        explanations["positive" if m_pets != "refuses_cat" else "negative"].append(
            "Client has cats, " + ("maid accepts cats." if m_pets != "refuses_cat" else "maid refuses cats.")
        )
    if c_pets == "dog":
        explanations["positive" if m_pets != "refuses_dog" else "negative"].append(
            "Client has dogs, " + ("maid accepts dogs." if m_pets != "refuses_dog" else "maid refuses dogs.")
        )
    if c_pets == "both":
        explanations["positive" if m_pets != "refuses_both_pets" else "negative"].append(
            "Client has both cat and dog, " + ("maid accepts both." if m_pets != "refuses_both_pets" else "maid refuses both.")
        )

    # Day-off
    if row.get("clientmts_dayoff_policy", "unspecified") != "unspecified":
        if row.get("maidmts_dayoff_policy", "no_restriction_dayoff") == "refuses_fixed_sunday":
            explanations["negative"].append("Client offers flexible day-off, maid only accepts Sunday.")
        else:
            explanations["positive"].append("Day-off policy is compatible.")

    # Living
    c_living = row.get("clientmts_living_arrangement", "unspecified")
    m_living = row.get("maidmts_living_arrangement", "no_restriction_living_arrangement")
    if "private_room" in c_living:
        explanations["positive" if "requires_no_private_room" not in m_living else "negative"].append(
            "Client provides private room, " + ("maid accepts." if "requires_no_private_room" not in m_living else "maid refuses private rooms.")
        )
    if "abu_dhabi" in c_living:
        explanations["positive" if "refuses_abu_dhabi" not in m_living else "negative"].append(
            "Client is in Abu Dhabi, " + ("maid accepts." if "refuses_abu_dhabi" not in m_living else "maid refuses Abu Dhabi placements.")
        )

    # Nationality
    if row.get("clientmts_nationality_preference", "any") != "any":
        if row["clientmts_nationality_preference"] in str(row.get("maid_nationality", "")):
            explanations["positive"].append(f"Client prefers {row['clientmts_nationality_preference']}, maid matches.")
        else:
            explanations["negative"].append(f"Client prefers {row['clientmts_nationality_preference']}, maid does not match.")

    # Cuisine
    c_cuisine = row.get("clientmts_cuisine_preference", "unspecified")
    m_cooking = str(row.get("cooking_group", "not_specified"))
    if c_cuisine != "unspecified" and m_cooking != "not_specified":
        c_set, m_set = set(c_cuisine.split("+")), set(m_cooking.split("+"))
        if c_set & m_set:
            explanations["positive"].append(f"Client prefers {c_cuisine}, maid can cook it.")
        else:
            explanations["negative"].append(f"Client prefers {c_cuisine}, maid cannot cook it.")

    # Special cases
    c_special = row.get("clientmts_special_cases", "unspecified")
    m_care = row.get("maidpref_caregiving_profile", "unspecified")
    if c_special != "unspecified":
        if (
            (c_special == "elderly" and m_care in ["elderly_experienced", "elderly_and_special"]) or
            (c_special == "special_needs" and m_care in ["special_needs", "elderly_and_special"]) or
            (c_special == "elderly_and_special" and m_care == "elderly_and_special")
        ):
            explanations["positive"].append(f"Client requires {c_special}, maid matches.")
        else:
            explanations["negative"].append(f"Client requires {c_special}, maid does not match.")

    # Kids experience
    if c_house in ["baby", "many_kids", "baby_and_kids"]:
        if (
            (c_house == "baby" and row.get("maidpref_kids_experience") in ["lessthan2", "both"]) or
            (c_house == "many_kids" and row.get("maidpref_kids_experience") in ["above2", "both"]) or
            (c_house == "baby_and_kids" and row.get("maidpref_kids_experience") == "both")
        ):
            explanations["positive"].append("Maid has the required kids experience.")
        else:
            explanations["negative"].append("Maid lacks the required kids experience.")

    # Pets handling
    if c_pets != "no_pets":
        if (
            (c_pets == "cat" and row.get("maidpref_pet_handling") in ["cats", "both"]) or
            (c_pets == "dog" and row.get("maidpref_pet_handling") in ["dogs", "both"]) or
            (c_pets == "both" and row.get("maidpref_pet_handling") == "both")
        ):
            explanations["positive"].append("Maid has the required pet handling skills.")
        else:
            explanations["negative"].append("Maid lacks the required pet handling skills.")

    # Vegetarian
    if "veg" in c_cuisine:
        if "veg_friendly" in str(row.get("maidpref_personality", "")):
            explanations["positive"].append("Client is vegetarian, maid is veg-friendly.")
        else:
            explanations["negative"].append("Client is vegetarian, maid is not veg-friendly.")

    # Smoking
    if row.get("maidpref_smoking") == "non_smoker":
        explanations["positive"].append("Maid is a non-smoker, suitable for client.")
    else:
        explanations["negative"].append("Maid's smoking status not compatible.")

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

    st.subheader("All Match Scores (click a row for details)")
    display_df = df[["client_name", "maid_id", "match_score_pct"]].reset_index()
    selected_row = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        key="score_table",
    )
    
    # If a row is selected
    if isinstance(selected_row, pd.DataFrame) and not selected_row.empty:
        selected_index = selected_row.iloc[0]["index"]  # original row index
        full_row = df.loc[selected_index]  # full row with all features
    
        st.subheader("Detailed Explanation")
        explanations = explain_row_score(full_row)
    
        st.write(f"**Match Score:** {full_row['match_score_pct']:.1f}%")
    
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
