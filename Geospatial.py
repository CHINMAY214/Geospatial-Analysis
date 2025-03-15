import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from datetime import datetime
from streamlit_folium import st_folium
import yaml

# ✅ Set page configuration at the very top
st.set_page_config(page_title="Geospatial Sales Analysis", layout="wide")

# ✅ Load user credentials from YAML file
with open("credentials.yaml", "r") as file:
    config = yaml.safe_load(file)

# ✅ Function to check login
def authenticate(username, password):
    for user, details in config["credentials"].items():
        if details["username"] == username and details["password"] == password:
            return True
    return False

# ✅ Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN PAGE ---
if not st.session_state.logged_in:
    st.title("🔐 Login to Access the Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful!")
            st.rerun()  # ✅ Restart app after login
        else:
            st.error("❌ Invalid username or password!")

else:
    # --- DASHBOARD STARTS HERE ---
    st.sidebar.success(f"Welcome, {st.session_state.username} 👋")

    # ✅ Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # ✅ Custom CSS for styling
    custom_css = """
    <style>
    body { background-color: #f8f9fa; font-family: 'Arial', sans-serif; }
    h1 { color: #007bff; text-align: center; font-weight: bold; }
    .sidebar .sidebar-content { background-color: #f1f1f1; padding: 15px; border-radius: 10px; }
    .stButton>button { background-color: #007bff !important; color: white !important; border-radius: 10px; font-size: 16px; padding: 10px; }
    .stMetric { text-align: center; font-weight: bold; font-size: 20px; color: #17a2b8; }
    .map-container { border-radius: 15px; overflow: hidden; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # --- ✅ FILE UPLOAD SECTION ---
    st.sidebar.markdown("### 📂 Upload Pre-Merged Dataset")
    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file:
        data = pd.read_csv(uploaded_file, encoding="ISO-8859-1", parse_dates=["Order Date"])
        st.success("✅ Data uploaded successfully!")

        # --- ✅ SIDEBAR FILTERS ---
        st.sidebar.markdown("<h2>🔍 Filters</h2>", unsafe_allow_html=True)
        start_date = st.sidebar.date_input("📅 Start Date", min(data["Order Date"]))
        end_date = st.sidebar.date_input("📅 End Date", max(data["Order Date"]))
        all_countries = sorted(data["Country"].unique())
        selected_countries = st.sidebar.multiselect("🌍 Select Country", all_countries, default=all_countries[:5])

        # ✅ Apply Filters
        filtered_data = data[
            (data["Order Date"] >= pd.to_datetime(start_date)) & 
            (data["Order Date"] <= pd.to_datetime(end_date))
        ]
        if selected_countries:
            filtered_data = filtered_data[filtered_data["Country"].isin(selected_countries)]

        # --- ✅ DISPLAY METRICS ---
        st.markdown("<h2>📊 Sales Metrics</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.metric("💰 Total Sales", f"${filtered_data['Sales'].sum():,.2f}")
        col2.metric("🛒 Total Transactions", f"{filtered_data.shape[0]:,}")

        # --- ✅ CREATE HEATMAP ---
        st.markdown("<h2>📍 Sales Heatmap</h2>", unsafe_allow_html=True)
        map_center = [filtered_data["Latitude"].mean(), filtered_data["Longitude"].mean()]
        sales_map = folium.Map(location=map_center, zoom_start=3)

        # ✅ Add Heatmap Layer
        heat_data = filtered_data[['Latitude', 'Longitude', 'Sales']].values.tolist()
        HeatMap(heat_data, radius=10, blur=15, max_zoom=1).add_to(sales_map)

        # ✅ Add Markers for Top 10 High-Sales Cities
        top_cities = filtered_data.nlargest(10, 'Sales')[["City", "Country", "Latitude", "Longitude", "Sales"]]
        for _, row in top_cities.iterrows():
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=f"{row['City']}, {row['Country']}<br>Sales: ${row['Sales']:,}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(sales_map)

        # ✅ Display Map
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st_folium(sales_map, width=1000, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

        # ✅ Display Top 10 High-Sales Cities
        st.markdown("<h2>🏆 Top 10 High-Sales Cities</h2>", unsafe_allow_html=True)
        st.dataframe(top_cities)

    else:
        st.warning("⚠️ Please upload a CSV file to proceed.")
