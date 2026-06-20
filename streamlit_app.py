# ============================================================
# Project   : Local Food Wastage Management System
# File      : app.py
# Purpose   : Streamlit app - filters, query outputs, charts,
#             and CRUD operations on all 4 tables
# Author    : Shahid Bashir Dar
# Run with  : streamlit run app.py
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from db_utils import run_query, execute_action

# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Local Food Wastage Management System",
    page_icon="🍽️",
    layout="wide"
)

# ------------------------------------------------------------
# Custom CSS polish - card shadows, tab styling, spacing
# ------------------------------------------------------------
st.markdown("""
<style>
    /* Tighter top padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* KPI metric cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E5DE;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #4A6358;
    }
    div[data-testid="stMetricValue"] {
        color: #2E7D32;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F0F4EF;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E7D32 !important;
        color: white !important;
    }

    /* Dataframe rounded corners */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E0E5DE;
    }

    /* Buttons */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍽️ Local Food Wastage Management System")
st.caption("Connecting surplus food providers with receivers to reduce food wastage.")

# ------------------------------------------------------------
# KPI Overview Cards
# ------------------------------------------------------------
kpi_df = run_query("""
    SELECT
        (SELECT COUNT(*) FROM providers)                              AS total_providers,
        (SELECT COUNT(*) FROM receivers)                              AS total_receivers,
        (SELECT SUM(Quantity) FROM food_listings)                     AS total_quantity,
        (SELECT COUNT(*) FROM claims WHERE Status = 'Completed')      AS completed_claims
""")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🏪 Total Providers", int(kpi_df["total_providers"][0]))
k2.metric("🤝 Total Receivers", int(kpi_df["total_receivers"][0]))
k3.metric("📦 Total Food Quantity", int(kpi_df["total_quantity"][0]))
k4.metric("✅ Completed Claims", int(kpi_df["completed_claims"][0]))

st.divider()

# ------------------------------------------------------------
# Main navigation tabs
# ------------------------------------------------------------
tab_filters, tab_queries, tab_charts, tab_crud = st.tabs(
    ["🔍 Filters & Listings", "📊 SQL Query Outputs", "📈 Charts", "🛠️ Manage Data (CRUD)"]
)

# ------------------------------------------------------------
# TAB 1: Filters & Listings
# ------------------------------------------------------------
with tab_filters:
    st.header("Filter Food Listings")

    # Load distinct filter options from the database
    cities_df   = run_query("SELECT DISTINCT Location FROM food_listings ORDER BY Location")
    providers_df = run_query("SELECT DISTINCT Provider_ID, Name FROM providers ORDER BY Name")
    food_types_df = run_query("SELECT DISTINCT Food_Type FROM food_listings ORDER BY Food_Type")
    meal_types_df = run_query("SELECT DISTINCT Meal_Type FROM food_listings ORDER BY Meal_Type")

    # Filter widgets laid out in 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_city = st.selectbox(
            "City", ["All"] + cities_df["Location"].tolist()
        )
    with col2:
        provider_options = ["All"] + providers_df["Name"].tolist()
        selected_provider = st.selectbox("Provider", provider_options)
    with col3:
        selected_food_type = st.selectbox(
            "Food Type", ["All"] + food_types_df["Food_Type"].tolist()
        )
    with col4:
        selected_meal_type = st.selectbox(
            "Meal Type", ["All"] + meal_types_df["Meal_Type"].tolist()
        )

    # Build dynamic query based on selected filters
    query = """
        SELECT
            fl.Food_ID, fl.Food_Name, fl.Quantity, fl.Expiry_Date,
            fl.Food_Type, fl.Meal_Type, fl.Location,
            p.Name AS Provider_Name, p.Type AS Provider_Type,
            p.Contact AS Provider_Contact
        FROM food_listings fl
        JOIN providers p ON fl.Provider_ID = p.Provider_ID
        WHERE 1=1
    """
    params = []

    if selected_city != "All":
        query += " AND fl.Location = %s"
        params.append(selected_city)
    if selected_provider != "All":
        query += " AND p.Name = %s"
        params.append(selected_provider)
    if selected_food_type != "All":
        query += " AND fl.Food_Type = %s"
        params.append(selected_food_type)
    if selected_meal_type != "All":
        query += " AND fl.Meal_Type = %s"
        params.append(selected_meal_type)

    query += " ORDER BY fl.Food_ID"

    results_df = run_query(query, params=params)

    st.subheader(f"Matching Listings ({len(results_df)} found)")
    st.dataframe(results_df, use_container_width=True)

    # Allow downloading filtered results
    if not results_df.empty:
        csv = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Results as CSV",
            data=csv,
            file_name="filtered_food_listings.csv",
            mime="text/csv"
        )

# ------------------------------------------------------------
# TAB 2: SQL Query Outputs
# ------------------------------------------------------------
with tab_queries:
    st.header("15 SQL Analysis Queries")
    st.caption("Select a question below to view the SQL query output.")

    # Dictionary mapping a readable question to its SQL query.
    # Matches the 15 queries from 03_analysis_queries.sql
    QUERIES = {
        "1. Providers & Receivers count by city": """
            SELECT
                p.City,
                COUNT(DISTINCT p.Provider_ID) AS Total_Providers,
                COUNT(DISTINCT r.Receiver_ID) AS Total_Receivers
            FROM providers p
            LEFT JOIN receivers r ON p.City = r.City
            GROUP BY p.City
            ORDER BY Total_Providers DESC;
        """,
        "2. Provider type contributing the most food": """
            SELECT
                Provider_Type,
                COUNT(Food_ID) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity,
                ROUND(AVG(Quantity), 2) AS Avg_Quantity_Per_Listing
            FROM food_listings
            GROUP BY Provider_Type
            ORDER BY Total_Quantity DESC;
        """,
        "3. Provider contact info by city": """
            SELECT Provider_ID, Name, Type, Address, City, Contact
            FROM providers
            WHERE City = %s
            ORDER BY Name;
        """,
        "4. Top 10 receivers by number of claims": """
            SELECT
                r.Receiver_ID, r.Name, r.Type, r.City,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM receivers r
            JOIN claims c ON r.Receiver_ID = c.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name, r.Type, r.City
            ORDER BY Total_Claims DESC
            LIMIT 10;
        """,
        "5. Total quantity of food available": """
            SELECT
                COUNT(Food_ID) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity_Available,
                ROUND(AVG(Quantity), 2) AS Avg_Quantity_Per_Listing,
                MIN(Quantity) AS Min_Quantity,
                MAX(Quantity) AS Max_Quantity
            FROM food_listings;
        """,
        "6. Top 10 cities by number of food listings": """
            SELECT
                Location AS City,
                COUNT(Food_ID) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity
            FROM food_listings
            GROUP BY Location
            ORDER BY Total_Listings DESC
            LIMIT 10;
        """,
        "7. Most commonly available food types": """
            SELECT
                Food_Type,
                COUNT(Food_ID) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity,
                ROUND(AVG(Quantity), 2) AS Avg_Quantity
            FROM food_listings
            GROUP BY Food_Type
            ORDER BY Total_Listings DESC;
        """,
        "8. Top 10 food items by number of claims": """
            SELECT
                fl.Food_ID, fl.Food_Name, fl.Food_Type, fl.Meal_Type, fl.Quantity,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM food_listings fl
            JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Food_ID, fl.Food_Name, fl.Food_Type, fl.Meal_Type, fl.Quantity
            ORDER BY Total_Claims DESC
            LIMIT 10;
        """,
        "9. Top 10 providers by completed claims": """
            SELECT
                p.Provider_ID, p.Name AS Provider_Name, p.Type AS Provider_Type, p.City,
                COUNT(c.Claim_ID) AS Completed_Claims
            FROM providers p
            JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
            JOIN claims c ON fl.Food_ID = c.Food_ID
            WHERE c.Status = 'Completed'
            GROUP BY p.Provider_ID, p.Name, p.Type, p.City
            ORDER BY Completed_Claims DESC
            LIMIT 10;
        """,
        "10. Claim status percentage breakdown": """
            SELECT
                Status,
                COUNT(Claim_ID) AS Total_Claims,
                ROUND(COUNT(Claim_ID) * 100.0 / SUM(COUNT(Claim_ID)) OVER(), 2) AS Percentage
            FROM claims
            GROUP BY Status
            ORDER BY Total_Claims DESC;
        """,
        "11. Top 10 receivers by avg quantity claimed": """
            SELECT
                r.Receiver_ID, r.Name AS Receiver_Name, r.Type AS Receiver_Type,
                COUNT(c.Claim_ID) AS Total_Claims,
                SUM(fl.Quantity) AS Total_Quantity_Claimed,
                ROUND(AVG(fl.Quantity), 2) AS Avg_Quantity_Per_Claim
            FROM receivers r
            JOIN claims c ON r.Receiver_ID = c.Receiver_ID
            JOIN food_listings fl ON c.Food_ID = fl.Food_ID
            GROUP BY r.Receiver_ID, r.Name, r.Type
            ORDER BY Avg_Quantity_Per_Claim DESC
            LIMIT 10;
        """,
        "12. Most claimed meal type": """
            SELECT
                fl.Meal_Type,
                COUNT(c.Claim_ID) AS Total_Claims,
                SUM(fl.Quantity) AS Total_Quantity_Claimed,
                ROUND(AVG(fl.Quantity), 2) AS Avg_Quantity_Per_Claim
            FROM food_listings fl
            JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Meal_Type
            ORDER BY Total_Claims DESC;
        """,
        "13. Top 10 providers by total quantity donated": """
            SELECT
                p.Provider_ID, p.Name AS Provider_Name, p.Type AS Provider_Type, p.City,
                COUNT(fl.Food_ID) AS Total_Listings,
                SUM(fl.Quantity) AS Total_Quantity_Donated
            FROM providers p
            JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
            GROUP BY p.Provider_ID, p.Name, p.Type, p.City
            ORDER BY Total_Quantity_Donated DESC
            LIMIT 10;
        """,
        "14. Top 10 cities by food demand (claims)": """
            SELECT
                fl.Location AS City,
                COUNT(c.Claim_ID) AS Total_Claims,
                SUM(fl.Quantity) AS Total_Quantity_Claimed
            FROM food_listings fl
            JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Location
            ORDER BY Total_Claims DESC
            LIMIT 10;
        """,
        "15. Meal type with highest unclaimed quantity (wastage)": """
            SELECT
                fl.Meal_Type,
                COUNT(fl.Food_ID) AS Total_Listings,
                SUM(fl.Quantity) AS Total_Quantity_Listed,
                COUNT(c.Claim_ID) AS Total_Claims,
                SUM(CASE WHEN c.Claim_ID IS NULL THEN fl.Quantity ELSE 0 END) AS Unclaimed_Quantity
            FROM food_listings fl
            LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Meal_Type
            ORDER BY Unclaimed_Quantity DESC;
        """,
    }

    selected_question = st.selectbox("Choose a question", list(QUERIES.keys()))
    sql_text = QUERIES[selected_question]

    # Query 3 needs a city parameter from the user
    if selected_question.startswith("3."):
        city_list_df = run_query("SELECT DISTINCT City FROM providers ORDER BY City")
        city_param = st.selectbox("Select City", city_list_df["City"].tolist())
        output_df = run_query(sql_text, params=[city_param])
    else:
        output_df = run_query(sql_text)

    with st.expander("View SQL Query"):
        st.code(sql_text, language="sql")

    st.subheader("Query Result")
    st.dataframe(output_df, use_container_width=True)
    st.caption(f"{len(output_df)} row(s) returned")

# ------------------------------------------------------------
# TAB 3: Charts
# ------------------------------------------------------------
with tab_charts:
    st.header("Visual Insights")

    # ---- Row 1: Distribution charts (univariate) ----
    col1, col2 = st.columns(2)

    with col1:
        df = run_query("""
            SELECT Provider_Type, COUNT(*) AS Count
            FROM food_listings GROUP BY Provider_Type ORDER BY Count DESC
        """)
        fig = px.bar(df, x="Provider_Type", y="Count", text="Count",
                     title="Provider Type Distribution", color="Provider_Type")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        df = run_query("""
            SELECT Food_Type, COUNT(*) AS Count
            FROM food_listings GROUP BY Food_Type ORDER BY Count DESC
        """)
        fig = px.pie(df, names="Food_Type", values="Count",
                     title="Food Type Distribution", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    # ---- Row 2: Quantity by category ----
    col3, col4 = st.columns(2)

    with col3:
        df = run_query("""
            SELECT Meal_Type, SUM(Quantity) AS Total_Quantity
            FROM food_listings GROUP BY Meal_Type ORDER BY Total_Quantity DESC
        """)
        fig = px.bar(df, x="Meal_Type", y="Total_Quantity", text="Total_Quantity",
                     title="Total Quantity by Meal Type", color="Meal_Type")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        df = run_query("""
            SELECT Location AS City, COUNT(*) AS Listings
            FROM food_listings GROUP BY Location
            ORDER BY Listings DESC LIMIT 10
        """)
        fig = px.bar(df, x="Listings", y="City", orientation="h", text="Listings",
                     title="Top 10 Cities by Number of Listings")
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    # ---- Row 3: Claims analysis ----
    col5, col6 = st.columns(2)

    with col5:
        df = run_query("""
            SELECT Status, COUNT(*) AS Total_Claims
            FROM claims GROUP BY Status
        """)
        fig = px.pie(df, names="Status", values="Total_Claims",
                     title="Claim Status Distribution", hole=0.4,
                     color="Status",
                     color_discrete_map={"Completed": "green", "Pending": "orange", "Cancelled": "red"})
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        df = run_query("""
            SELECT p.Name AS Provider, SUM(fl.Quantity) AS Total_Quantity_Claimed
            FROM claims c
            JOIN food_listings fl ON c.Food_ID = fl.Food_ID
            JOIN providers p ON fl.Provider_ID = p.Provider_ID
            GROUP BY p.Name
            ORDER BY Total_Quantity_Claimed DESC
            LIMIT 10
        """)
        fig = px.bar(df, x="Total_Quantity_Claimed", y="Provider", orientation="h",
                     text="Total_Quantity_Claimed", title="Top 10 Providers by Quantity Claimed")
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    # ---- Row 4: Multivariate heatmap ----
    df = run_query("""
        SELECT Food_Type, Meal_Type, SUM(Quantity) AS Total_Quantity
        FROM food_listings
        GROUP BY Food_Type, Meal_Type
    """)
    pivot = df.pivot(index="Food_Type", columns="Meal_Type", values="Total_Quantity").fillna(0)
    fig = px.imshow(pivot, text_auto=True, color_continuous_scale="YlGnBu",
                     title="Total Quantity by Food Type and Meal Type")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: Manage Data (CRUD)
# ------------------------------------------------------------
with tab_crud:
    st.header("Manage Data")
    st.caption("Add, update, or delete records in any of the 4 tables.")

    table_choice = st.selectbox(
        "Select Table",
        ["Food Listings", "Providers", "Receivers", "Claims"]
    )

    crud_action = st.radio("Action", ["View / Delete", "Add New", "Update Existing"], horizontal=True)

    # ============================================================
    # FOOD LISTINGS
    # ============================================================
    if table_choice == "Food Listings":

        if crud_action == "View / Delete":
            df = run_query("SELECT * FROM food_listings ORDER BY Food_ID")
            st.dataframe(df, use_container_width=True)

            delete_id = st.number_input("Food_ID to delete", min_value=0, step=1)
            if st.button("🗑️ Delete Food Listing"):
                affected = execute_action("DELETE FROM food_listings WHERE Food_ID = %s", (delete_id,))
                if affected:
                    st.success(f"Deleted Food_ID {delete_id}")
                else:
                    st.warning("No matching Food_ID found.")

        elif crud_action == "Add New":
            with st.form("add_food_form"):
                food_id = st.number_input("Food_ID", min_value=1, step=1)
                food_name = st.text_input("Food Name")
                quantity = st.number_input("Quantity", min_value=1, step=1)
                expiry_date = st.date_input("Expiry Date")
                provider_id = st.number_input("Provider_ID", min_value=1, step=1)
                provider_type = st.text_input("Provider Type")
                location = st.text_input("Location (City)")
                food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
                meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

                submitted = st.form_submit_button("➕ Add Food Listing")
                if submitted:
                    query = """
                        INSERT INTO food_listings
                        (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID,
                         Provider_Type, Location, Food_Type, Meal_Type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    try:
                        execute_action(query, (food_id, food_name, quantity, expiry_date,
                                                provider_id, provider_type, location,
                                                food_type, meal_type))
                        st.success(f"Added Food_ID {food_id}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif crud_action == "Update Existing":
            update_id = st.number_input("Food_ID to update", min_value=1, step=1)
            existing = run_query("SELECT * FROM food_listings WHERE Food_ID = %s", (update_id,))

            if not existing.empty:
                row = existing.iloc[0]
                with st.form("update_food_form"):
                    food_name = st.text_input("Food Name", value=row["Food_Name"])
                    quantity = st.number_input("Quantity", min_value=1, step=1, value=int(row["Quantity"]))
                    food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"],
                                              index=["Vegetarian", "Non-Vegetarian", "Vegan"].index(row["Food_Type"]))
                    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"],
                                              index=["Breakfast", "Lunch", "Dinner", "Snacks"].index(row["Meal_Type"]))

                    submitted = st.form_submit_button("💾 Update Food Listing")
                    if submitted:
                        query = """
                            UPDATE food_listings
                            SET Food_Name = %s, Quantity = %s, Food_Type = %s, Meal_Type = %s
                            WHERE Food_ID = %s
                        """
                        execute_action(query, (food_name, quantity, food_type, meal_type, update_id))
                        st.success(f"Updated Food_ID {update_id}")
            else:
                st.warning("No matching Food_ID found.")

    # ============================================================
    # PROVIDERS
    # ============================================================
    elif table_choice == "Providers":

        if crud_action == "View / Delete":
            df = run_query("SELECT * FROM providers ORDER BY Provider_ID")
            st.dataframe(df, use_container_width=True)

            delete_id = st.number_input("Provider_ID to delete", min_value=0, step=1)
            if st.button("🗑️ Delete Provider"):
                try:
                    affected = execute_action("DELETE FROM providers WHERE Provider_ID = %s", (delete_id,))
                    if affected:
                        st.success(f"Deleted Provider_ID {delete_id}")
                    else:
                        st.warning("No matching Provider_ID found.")
                except Exception as e:
                    st.error(f"Cannot delete - this provider likely has linked food listings. ({e})")

        elif crud_action == "Add New":
            with st.form("add_provider_form"):
                provider_id = st.number_input("Provider_ID", min_value=1, step=1)
                name = st.text_input("Name")
                ptype = st.text_input("Type (e.g. Restaurant, Grocery Store)")
                address = st.text_input("Address")
                city = st.text_input("City")
                contact = st.text_input("Contact")

                submitted = st.form_submit_button("➕ Add Provider")
                if submitted:
                    query = """
                        INSERT INTO providers (Provider_ID, Name, Type, Address, City, Contact)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    try:
                        execute_action(query, (provider_id, name, ptype, address, city, contact))
                        st.success(f"Added Provider_ID {provider_id}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif crud_action == "Update Existing":
            update_id = st.number_input("Provider_ID to update", min_value=1, step=1)
            existing = run_query("SELECT * FROM providers WHERE Provider_ID = %s", (update_id,))

            if not existing.empty:
                row = existing.iloc[0]
                with st.form("update_provider_form"):
                    name = st.text_input("Name", value=row["Name"])
                    address = st.text_input("Address", value=row["Address"])
                    city = st.text_input("City", value=row["City"])
                    contact = st.text_input("Contact", value=row["Contact"])

                    submitted = st.form_submit_button("💾 Update Provider")
                    if submitted:
                        query = """
                            UPDATE providers
                            SET Name = %s, Address = %s, City = %s, Contact = %s
                            WHERE Provider_ID = %s
                        """
                        execute_action(query, (name, address, city, contact, update_id))
                        st.success(f"Updated Provider_ID {update_id}")
            else:
                st.warning("No matching Provider_ID found.")

    # ============================================================
    # RECEIVERS
    # ============================================================
    elif table_choice == "Receivers":

        if crud_action == "View / Delete":
            df = run_query("SELECT * FROM receivers ORDER BY Receiver_ID")
            st.dataframe(df, use_container_width=True)

            delete_id = st.number_input("Receiver_ID to delete", min_value=0, step=1)
            if st.button("🗑️ Delete Receiver"):
                try:
                    affected = execute_action("DELETE FROM receivers WHERE Receiver_ID = %s", (delete_id,))
                    if affected:
                        st.success(f"Deleted Receiver_ID {delete_id}")
                    else:
                        st.warning("No matching Receiver_ID found.")
                except Exception as e:
                    st.error(f"Cannot delete - this receiver likely has linked claims. ({e})")

        elif crud_action == "Add New":
            with st.form("add_receiver_form"):
                receiver_id = st.number_input("Receiver_ID", min_value=1, step=1)
                name = st.text_input("Name")
                rtype = st.text_input("Type (e.g. NGO, Shelter, Individual)")
                city = st.text_input("City")
                contact = st.text_input("Contact")

                submitted = st.form_submit_button("➕ Add Receiver")
                if submitted:
                    query = """
                        INSERT INTO receivers (Receiver_ID, Name, Type, City, Contact)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    try:
                        execute_action(query, (receiver_id, name, rtype, city, contact))
                        st.success(f"Added Receiver_ID {receiver_id}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif crud_action == "Update Existing":
            update_id = st.number_input("Receiver_ID to update", min_value=1, step=1)
            existing = run_query("SELECT * FROM receivers WHERE Receiver_ID = %s", (update_id,))

            if not existing.empty:
                row = existing.iloc[0]
                with st.form("update_receiver_form"):
                    name = st.text_input("Name", value=row["Name"])
                    city = st.text_input("City", value=row["City"])
                    contact = st.text_input("Contact", value=row["Contact"])

                    submitted = st.form_submit_button("💾 Update Receiver")
                    if submitted:
                        query = """
                            UPDATE receivers
                            SET Name = %s, City = %s, Contact = %s
                            WHERE Receiver_ID = %s
                        """
                        execute_action(query, (name, city, contact, update_id))
                        st.success(f"Updated Receiver_ID {update_id}")
            else:
                st.warning("No matching Receiver_ID found.")

    # ============================================================
    # CLAIMS
    # ============================================================
    elif table_choice == "Claims":

        if crud_action == "View / Delete":
            df = run_query("SELECT * FROM claims ORDER BY Claim_ID")
            st.dataframe(df, use_container_width=True)

            delete_id = st.number_input("Claim_ID to delete", min_value=0, step=1)
            if st.button("🗑️ Delete Claim"):
                affected = execute_action("DELETE FROM claims WHERE Claim_ID = %s", (delete_id,))
                if affected:
                    st.success(f"Deleted Claim_ID {delete_id}")
                else:
                    st.warning("No matching Claim_ID found.")

        elif crud_action == "Add New":
            with st.form("add_claim_form"):
                claim_id = st.number_input("Claim_ID", min_value=1, step=1)
                food_id = st.number_input("Food_ID", min_value=1, step=1)
                receiver_id = st.number_input("Receiver_ID", min_value=1, step=1)
                status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
                timestamp = st.text_input("Timestamp (YYYY-MM-DD HH:MM:SS)")

                submitted = st.form_submit_button("➕ Add Claim")
                if submitted:
                    query = """
                        INSERT INTO claims (Claim_ID, Food_ID, Receiver_ID, Status, Timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    try:
                        execute_action(query, (claim_id, food_id, receiver_id, status, timestamp))
                        st.success(f"Added Claim_ID {claim_id}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif crud_action == "Update Existing":
            update_id = st.number_input("Claim_ID to update", min_value=1, step=1)
            existing = run_query("SELECT * FROM claims WHERE Claim_ID = %s", (update_id,))

            if not existing.empty:
                row = existing.iloc[0]
                with st.form("update_claim_form"):
                    status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"],
                                           index=["Pending", "Completed", "Cancelled"].index(row["Status"]))

                    submitted = st.form_submit_button("💾 Update Claim Status")
                    if submitted:
                        query = "UPDATE claims SET Status = %s WHERE Claim_ID = %s"
                        execute_action(query, (status, update_id))
                        st.success(f"Updated Claim_ID {update_id}")
            else:
                st.warning("No matching Claim_ID found.")
