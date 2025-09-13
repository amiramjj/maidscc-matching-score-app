import streamlit as st
import pandas as pd

# ----------------------------
# Matching Score Function
# ----------------------------
def calculate_row_score_with_reasons(row):
    score, max_score = 0, 0
    reasons = {}

    # Household
    if row.get("clientmts_household_type") and row["clientmts_household_type"] != "unspecified":
        max_score += 0.6
        if row["maidmts_household_type"] == "no_restriction_household_type":
            score += 0.6
            reasons["Household"] = "Maid has no restriction → ✅"
        elif row["maidmts_household_type"].replace("refuses_", "") == row["clientmts_household_type"]:
            reasons["Household"] = "Maid refuses → ❌"
        else:
            score += 0.6
            reasons["Household"] = "Compatible household → ✅"
    else:
        reasons["Household"] = "No preference → ⚪"

    # Pets
    if row.get("clientmts_pet_type") and row["clientmts_pet_type"] != "no_pets":
        max_score += 0.6
        if row["maidmts_pet_type"] == "no_restriction_pets":
            score += 0.6
            reasons["Pets"] = "Maid has no restriction → ✅"
        elif ("refuses_cat" in row["maidmts_pet_type"] and "cat" in row["clientmts_pet_type"]) or \
             ("refuses_dog" in row["maidmts_pet_type"] and "dog" in row["clientmts_pet_type"]):
            reasons["Pets"] = "Maid refuses → ❌"
        else:
            score += 0.6
            reasons["Pets"] = "Compatible pets → ✅"
    else:
        reasons["Pets"] = "No pets specified → ⚪"

    # Living Arrangement
    if row.get("clientmts_living_arrangement") and row["clientmts_living_arrangement"] != "unspecified":
        max_score += 0.6
        if row["maidmts_living_arrangement"] == "no_restriction_living_arrangement":
            score += 0.6
            reasons["Living Arrangement"] = "Maid has no restriction → ✅"
        elif "refuses_abu_dhabi" in row["maidmts_living_arrangement"] and "abu_dhabi" in row["clientmts_living_arrangement"]:
            reasons["Living Arrangement"] = "Maid refuses Abu Dhabi → ❌"
        elif "requires_no_private_room" in row["maidmts_living_arrangement"] and "private_room" not in row["clientmts_living_arrangement"]:
            score += 0.6
            reasons["Living Arrangement"] = "Maid requires no private room, client doesn’t provide one → ✅"
        else:
            score += 0.6
            reasons["Living Arrangement"] = "Arrangement acceptable → ✅"
    else:
        reasons["Living Arrangement"] = "No preference → ⚪"

    # Cuisine
    if row.get("clientmts_cuisine_preference") and row["clientmts_cuisine_preference"] != "unspecified":
        max_score += 0.6
        if any(cuisine in row.get("cooking_group", "") for cuisine in row["clientmts_cuisine_preference"].split("+")):
            score += 0.6
            reasons["Cuisine"] = "Maid can cook requested cuisine → ✅"
        else:
            reasons["Cuisine"] = "Maid cannot cook requested cuisine → ❌"
    else:
        reasons["Cuisine"] = "No cuisine specified → ⚪"

    # Example: we add more features here (special cases, kids, smoking, etc.)

    final_score = score / max_score if max_score > 0 else 0
    return final_score, reasons


# ----------------------------
# Streamlit Interface
# ----------------------------
st.set_page_config(page_title="MaidsCC Matching Score", layout="wide")

st.title("🤝 MaidsCC Matching Score App")
st.markdown("Upload your dataset and analyze **Client ↔ Maid matching scores** interactively.")

# File uploader
uploaded_file = st.file_uploader("Upload Excel/CSV file", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("✅ File uploaded successfully!")

    # Compute scores
    st.subheader("🔎 Calculating Matching Scores...")
    df[["matching_score", "reasons"]] = df.apply(lambda row: pd.Series(calculate_row_score_with_reasons(row)), axis=1)

    # Show first 20
    st.write("### Preview of Results")
    st.dataframe(df[["client_name", "maid_id", "matching_score"]].head(20))

    # Expanders for explanations
    st.write("### Detailed Explanations")
    for i, row in df.head(10).iterrows():
        with st.expander(f"Client: {row['client_name']} | Maid: {row['maid_id']} | Score: {row['matching_score']:.2f}"):
            for k, v in row["reasons"].items():
                st.write(f"**{k}** → {v}")

    # Score distribution
    st.subheader("📊 Score Distribution")
    st.bar_chart(df["matching_score"])

    # Download button
    st.download_button(
        "📥 Download Results",
        df.to_csv(index=False).encode("utf-8"),
        "matching_scores.csv",
        "text/csv"
    )

