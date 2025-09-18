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
    tab1, tab2, tab3, tab4 = st.tabs([
        "All Match Scores (tagged pairs)", 
        "Best Maid per Client (Global Search)", 
        "Maid Profiles",
        "Summary Metrics"
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
    
        # Deduplicate by maid_id
        maids_df = df.drop_duplicates(subset=["maid_id"]).copy()
        maids_df = maids_df.loc[:, ~maids_df.columns.duplicated()]
    
        # Detect maid-related columns (exclude 'maidmts_at_hiring')
        maid_cols = [
            c for c in maids_df.columns
            if (c.startswith("maidmts_") or c.startswith("maidpref_") or c.startswith("maid_"))
            and c != "maidmts_at_hiring"
        ]
    
        # Detect engineered language columns
        lang_cols = [c for c in maids_df.columns if c.startswith("maidspeaks_")]
    
        # Group Explorer
        st.markdown("### Group Maids by Feature")
    
        feature_choice = st.selectbox(
            "Choose a feature to group by",
            maid_cols + ["maid_speaks_language"]  # add a synthetic option for languages
        )
    
        if feature_choice == "maid_speaks_language":
            # Handle languages separately from other features
            for lang_col in lang_cols:
                lang_name = lang_col.replace("maidspeaks_", "").capitalize()
                maid_ids = maids_df.loc[maids_df[lang_col] == 1, "maid_id"].tolist()
    
                with st.expander(f"maid_speaks_language: {lang_name}"):
                    for mid in sorted(maid_ids):
                        if st.button(f"Maid {mid}", key=f"maid_lang_{lang_name}_{mid}"):
                            maid_row = maids_df[maids_df["maid_id"] == mid].iloc[0]
                            st.markdown(f"### Maid {maid_row['maid_id']}")
                            for col in maid_cols + lang_cols:
                                st.write(f"- **{col}**: {maid_row[col]}")
        else:
            # Normal grouping for all other features
            grouped = maids_df.groupby(feature_choice)["maid_id"].apply(list).reset_index()
    
            for _, row in grouped.iterrows():
                with st.expander(f"{feature_choice}: {row[feature_choice]}"):
                    for mid in sorted(row["maid_id"]):
                        if st.button(f"Maid {mid}", key=f"maid_{feature_choice}_{mid}"):
                            maid_row = maids_df[maids_df["maid_id"] == mid].iloc[0]
                            st.markdown(f"### Maid {maid_row['maid_id']}")
                            for col in maid_cols + lang_cols:
                                st.write(f"- **{col}**: {maid_row[col]}")

    # -------------------------------
    # Tab 4: Summary Metrics
    # -------------------------------
    with tab4:
        st.subheader(" Summary Metrics")
    
        # Compute averages
        avg_tagged = df["match_score_pct"].mean()
        avg_best = best_client_df["match_score_pct"].mean()
        delta = avg_best - avg_tagged
    
        col1, col2, col3 = st.columns(3)
    
        with col1:
            st.metric("Avg Tagged Match Score", f"{avg_tagged:.1f}%")
            st.caption("This is where we stand today — less than one in four tagged placements are truly optimal. Every mismatch carries hidden costs in refunds, churn, and service quality.")
    
        with col2:
            st.metric("Avg Best Match Score", f"{avg_best:.1f}%")
            st.caption("This is the opportunity ceiling — the alignment possible if every client were paired with their strongest-fit maid. It’s the benchmark for what ‘good’ looks like.")
    
        with col3:
            st.metric("Improvement", f"{delta:+.1f}%")
            st.caption("Even a small lift is massive at scale: a 3.7% gain means fewer replacements, higher client satisfaction, and measurable savings across the ERP system.")

        # -------------------------------
        # Distribution Visualization
        # -------------------------------
        st.markdown("### Distribution of Match Scores")

        import plotly.express as px
        import numpy as np

        # Prepare data for plotting
        tagged_scores = df[["match_score_pct"]].copy()
        tagged_scores["type"] = "Tagged"

        best_scores = best_client_df[["match_score_pct"]].copy()
        best_scores["type"] = "Best"

        dist_data = pd.concat([tagged_scores, best_scores], ignore_index=True)

        # Define bins (0–100 in steps of 10)
        bins = np.arange(0, 110, 10)
        dist_data["bin"] = pd.cut(dist_data["match_score_pct"], bins=bins, right=False)

        # Count % per bin
        grouped = (
            dist_data.groupby(["bin", "type"])
            .size()
            .reset_index(name="count")
        )
        grouped["percent"] = grouped.groupby("type")["count"].transform(lambda x: x / x.sum() * 100)

        # Convert Interval objects to string labels for plotting
        grouped["bin"] = grouped["bin"].astype(str)

        # Grouped bar chart
        fig = px.bar(
            grouped,
            x="bin",
            y="percent",
            color="type",
            barmode="group",
            color_discrete_map={
                "Tagged": "#1f77b4",  # darker blue
                "Best": "#6baed6"     # lighter blue
            },
            category_orders={"type": ["Tagged", "Best"]},  # force order
            labels={"bin": "Match Score Range (%)", "percent": "Percentage of Clients", "type": "Group"},
            title="Score Distribution: Tagged vs. Best Matches"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            """
            - Most placements cluster in the **10–20% match range**, but many of these cases come from clients who **provided no preferences or matching types**. In other words, the system had little to work with
            - When preferences are specified and data-driven matching is applied, the distribution shifts significantly to the right. This means fewer clients stuck in low-fit assignments, and more moving into stronger alignment bands.
            - The message is clear: **better input leads to better outcomes**. By capturing and leveraging client preferences systematically, we unlock portfolio-wide improvements in satisfaction, retention, and efficiency.
            """
        )


        # -------------------------------
        # Diagnostic Slice: Compare Tagged vs Best by Feature
        # -------------------------------
        st.markdown("### 🔎 Diagnostic Slice: Compare Tagged vs Best by Feature")

        # Pick a feature dynamically
        client_features = [c for c in df.columns if c.startswith("clientmts_")]
        feature_choice = st.selectbox("Choose a client feature to slice by", client_features)

        if feature_choice:
            # Prepare tagged scores
            diag_df = pd.DataFrame({
                "feature": df[feature_choice],
                "tagged_score": df["match_score_pct"],
                "client_name": df["client_name"]
            })

            # Best scores merged with feature
            diag_best = best_client_df[["client_name", "match_score_pct"]].merge(
                df[["client_name", feature_choice]],
                on="client_name",
                how="left"
            )
            diag_best.rename(columns={"match_score_pct": "best_score"}, inplace=True)

            # Aggregate averages
            agg = (
                diag_df.groupby("feature")["tagged_score"].mean().reset_index()
                .merge(
                    diag_best.groupby(feature_choice)["best_score"].mean().reset_index(),
                    left_on="feature",
                    right_on=feature_choice,
                    how="outer"
                )
            )
            agg = agg.drop(columns=[feature_choice])

            # Melt for plotting
            agg_melted = agg.melt(
                id_vars="feature",
                value_vars=["tagged_score", "best_score"],
                var_name="type",
                value_name="avg_score"
            )
            agg_melted["type"] = agg_melted["type"].map({
                "tagged_score": "Tagged",
                "best_score": "Best"
            })

            # Plot with consistent blue shades # Diagnostic slice chart
            fig3 = px.bar(
                agg_melted,
                x="feature",
                y="avg_score",
                color="type",
                barmode="group",
                color_discrete_map={
                    "Tagged": "#1f77b4",
                    "Best": "#6baed6"
                },
                category_orders={"type": ["Tagged", "Best"]},  # force order
                labels={
                    "feature": feature_choice,
                    "avg_score": "Average Match Score (%)",
                    "type": "Group"
                },
                title=f"Average Match Scores by {feature_choice}"
            )
            fig3.update_yaxes(range=[0, 100])

            st.plotly_chart(fig3, use_container_width=True)

            st.caption(
                f"""
                This diagnostic slice shows how **{feature_choice}** influences outcomes:
                - **Tagged assignments** reveal current gaps.  
                - **Best matches** illustrate how algorithmic matching improves alignment.  
                - When values are 'unspecified' or 'any', scores tend to be lower — reinforcing that **better input yields better matches**.
                """
            )

        # -------------------------------
        # Client Drilldown: Tagged vs Best
        # -------------------------------
        st.markdown("### 👥 Client Drilldown: Tagged vs Best Match")
    
        # Select a client
        drill_client = st.selectbox("Choose a client to compare", df["client_name"].unique())
    
        # Get tagged row for this client
        tagged_row = df[df["client_name"] == drill_client].iloc[0]
    
        # Get best row for this client
        best_row = best_client_df[best_client_df["client_name"] == drill_client].iloc[0]
    
        col1, col2 = st.columns(2)
    
        # --- Tagged Maid ---
        with col1:
            st.subheader("Tagged Maid")
            st.write(f"**Maid:** {tagged_row['maid_id']}")
            st.write(f"**Match Score:** {tagged_row['match_score_pct']:.1f}%")
            explanations_tagged = explain_row_score(tagged_row.to_dict())
    
            with st.expander("Positive Matches"):
                for r in explanations_tagged["positive"]:
                    st.write(f"- {r}")
            with st.expander("Negative Mismatches"):
                for r in explanations_tagged["negative"]:
                    st.write(f"- {r}")
            with st.expander("Neutral Notes"):
                for r in explanations_tagged["neutral"]:
                    st.write(f"- {r}")
    
        # --- Best Maid ---
        with col2:
            st.subheader("Best Maid (Global Search)")
            st.write(f"**Maid:** {best_row['best_maid_id']}")
            st.write(f"**Match Score:** {best_row['match_score_pct']:.1f}%")
            explanations_best = explain_row_score(best_row["combined"])
    
            with st.expander("Positive Matches"):
                for r in explanations_best["positive"]:
                    st.write(f"- {r}")
            with st.expander("Negative Mismatches"):
                for r in explanations_best["negative"]:
                    st.write(f"- {r}")
            with st.expander("Neutral Notes"):
                for r in explanations_best["neutral"]:
                    st.write(f"- {r}")
    
        # Caption for context
        st.caption(
            """
            This drilldown highlights the **efficiency gap at the client level**:
            - **Tagged maid** shows the current placement, often suboptimal.  
            - **Best maid** represents the algorithmic optimum, with higher alignment.  
            - The side-by-side view makes it easy to see *what exactly drives the difference*.
            """
        )
        
        # -------------------------------
        # Portfolio Risk Buckets
        # -------------------------------
        st.markdown("### Portfolio Risk Buckets: Low vs Medium vs High Fit")

        # Create buckets
        def bucket_score(score):
            if score < 20:
                return "Low-fit (<20%)"
            elif score < 50:
                return "Medium-fit (20–50%)"
            else:
                return "High-fit (>50%)"

        tagged_scores["bucket"] = tagged_scores["match_score_pct"].apply(bucket_score)
        best_scores["bucket"] = best_scores["match_score_pct"].apply(bucket_score)

        bucket_data = pd.concat([tagged_scores, best_scores], ignore_index=True)

        # Aggregate % by bucket
        bucket_summary = (
            bucket_data.groupby(["bucket", "type"])
            .size()
            .reset_index(name="count")
        )
        bucket_summary["percent"] = bucket_summary.groupby("type")["count"].transform(lambda x: x / x.sum() * 100)

        # Ensure consistent order
        bucket_order = ["Low-fit (<20%)", "Medium-fit (20–50%)", "High-fit (>50%)"]

        # Stacked bar
        fig_buckets = px.bar(
            bucket_summary,
            x="type",
            y="percent",
            color="bucket",
            category_orders={"bucket": bucket_order, "type": ["Tagged", "Best"]},
            color_discrete_map={
                "Low-fit (<20%)": "#9ecae1",      # light blue
                "Medium-fit (20–50%)": "#9ecae1", # same light blue
                "High-fit (>50%)": "#08519c"      # dark blue
            },
            labels={"type": "Group", "percent": "Percentage of Clients", "bucket": "Risk Bucket"},
            title="Client Distribution Across Risk Buckets"
        )        
        
        st.plotly_chart(fig_buckets, use_container_width=True)
        
        st.caption(
            """
            When we shift from tagged to data-driven matching, the difference is clear:
            - High-fit placements (>50%) climb from 10.9% to 15.0% — a meaningful jump in strong alignments.
            - Medium-fit (20–50%) holds steady, moving slightly from 23.8% to 23.2%.
            - Low-fit placements (<20%) drop from 65.3% to 61.8%, showing fewer clients stuck in mismatched assignments.
                  
            Every percentage point gained in medium-high fit matches translates into fewer costly replacements, stronger satisfaction, and more loyalty secured.
            """
        )

        # -------------------------------
        # Top Drivers of Mismatch
        # -------------------------------
        st.markdown("### ❌ Top Drivers of Mismatch")
        
        # Function to extract mismatch drivers for each row
        def get_mismatch_reasons(row):
            explanations = explain_row_score(row)
            return explanations["negative"]
        
        # Collect mismatches for all tagged placements
        all_mismatches = df.apply(lambda r: get_mismatch_reasons(r.to_dict()), axis=1)
        
        # Flatten list of mismatches
        mismatch_list = [reason for sublist in all_mismatches for reason in sublist]
        
        # Aggregate counts
        mismatch_counts = pd.Series(mismatch_list).value_counts().reset_index()
        mismatch_counts.columns = ["Mismatch Reason", "Count"]
        
        # Convert to percentage of total mismatches
        mismatch_counts["Percent"] = (mismatch_counts["Count"] / mismatch_counts["Count"].sum()) * 100
        
        # Plot
        fig_mismatch = px.bar(
            mismatch_counts.sort_values("Count", ascending=True),
            x="Count",
            y="Mismatch Reason",
            orientation="h",
            text=mismatch_counts["Percent"].apply(lambda x: f"{x:.1f}%"),
            labels={"Count": "Number of Cases", "Mismatch Reason": "Driver"},
            title="Top Drivers of Mismatch Across Tagged Placements",
            color="Count",
            color_continuous_scale="Blues"
        )
        
        st.plotly_chart(fig_mismatch, use_container_width=True)
        
        st.caption(
            """
            This chart highlights the **most common reasons clients and maids misalign** in current placements.  
            By targeting the top mismatch drivers (e.g., pets, household type, caregiving needs), we can unlock 
            disproportionate improvements in fit, retention, and satisfaction.
            """
        )


        # -------------------------------
        # Top Drivers of Match & Mismatch
        # -------------------------------
        st.markdown("### 🔎 Top Drivers of Match vs. Mismatch")
        
        from collections import Counter
        import plotly.express as px
        
        # --- Theme classifier (consistent with score logic) ---
        def classify_theme(reason: str):
            r = reason.lower()
            if "baby" in r or "kids" in r:
                if "refuses" in r:
                    return "Household Type"
                else:
                    return "Kids Experience"
            elif "pet" in r or "cat" in r or "dog" in r:
                return "Pets"
            elif "day-off" in r or "sunday" in r:
                return "Day-off Policy"
            elif "private room" in r or "living" in r or "arrangement" in r:
                return "Living Arrangement"
            elif "nationality" in r:
                return "Nationality"
            elif "cuisine" in r or "cooking" in r:
                return "Cuisine"
            elif "special" in r or "caregiving" in r:
                return "Special Cases"
            elif "veg" in r or "vegetarian" in r:
                return "Vegetarian / Lifestyle"
            elif "smoker" in r:
                return "Smoking"
            else:
                return None  # drop anything uncategorized
        
        # --- Collect reasons across all rows ---
        mismatch_reasons = []
        match_reasons = []
        
        for _, row in df.iterrows():
            exps = explain_row_score(row.to_dict())
            mismatch_reasons.extend([classify_theme(r) for r in exps["negative"]])
            match_reasons.extend([classify_theme(r) for r in exps["positive"]])
        
        # Filter out None (i.e., uncategorized)
        mismatch_reasons = [r for r in mismatch_reasons if r is not None]
        match_reasons = [r for r in match_reasons if r is not None]
        
        # --- Count and normalize ---
        mismatch_counts = Counter(mismatch_reasons)
        match_counts = Counter(match_reasons)
        
        mismatch_df = pd.DataFrame(mismatch_counts.items(), columns=["Theme", "Count"])
        match_df = pd.DataFrame(match_counts.items(), columns=["Theme", "Count"])
        
        # Drop themes with zero
        mismatch_df = mismatch_df[mismatch_df["Count"] > 0]
        match_df = match_df[match_df["Count"] > 0]
        
        mismatch_df["Percent"] = mismatch_df["Count"] / mismatch_df["Count"].sum() * 100
        match_df["Percent"] = match_df["Count"] / match_df["Count"].sum() * 100
        
        # Order by percentage ascending
        mismatch_df = mismatch_df.sort_values("Percent", ascending=True)
        match_df = match_df.sort_values("Percent", ascending=True)
        
        # Use more space for the charts
        col1, col2 = st.columns([1, 1])  # equally wide, but more horizontal space
        
        with col1:
            fig_mismatch = px.bar(
                mismatch_df,
                x="Percent", y="Theme",
                orientation="h",
                color="Percent",
                color_continuous_scale="Blues",
                title="Top Drivers of Mismatch"
            )
            fig_mismatch.update_traces(text=None)  # remove % labels
            fig_mismatch.update_layout(coloraxis_showscale=False)  # remove colorbar
            st.plotly_chart(fig_mismatch, use_container_width=True)
        
        with col2:
            fig_match = px.bar(
                match_df,
                x="Percent",
                orientation="h",
                color="Percent",
                color_continuous_scale="Greens",
                title="Top Drivers of Match"
            )
            fig_match.update_traces(text=None)  # remove % labels
            fig_match.update_layout(coloraxis_showscale=False)  # remove colorbar
            st.plotly_chart(fig_match, use_container_width=True)
        
