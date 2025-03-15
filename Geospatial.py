import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import yaml
import plotly.express as px

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
        data = pd.read_csv(uploaded_file, encoding="ISO-8859-1")

        # ✅ Ensure required columns exist
        required_columns = {"City", "State", "Country", "Sales", "Profit", "Latitude", "Longitude"}
        if not required_columns.issubset(set(data.columns)):
            st.error(f"❌ Missing required columns! Expected: {required_columns}")
            st.stop()

        st.success("✅ Data uploaded successfully!")

        # --- ✅ SIDEBAR FILTERS ---
        st.sidebar.markdown("<h2>🔍 Filters</h2>", unsafe_allow_html=True)
        all_countries = sorted(data["Country"].unique())
        selected_countries = st.sidebar.multiselect("🌍 Select Country", all_countries, default=all_countries[:5])

        all_states = sorted(data["State"].unique())
        selected_states = st.sidebar.multiselect("🏙️ Select State", all_states, default=all_states[:5])

        # ✅ Apply Filters
        filtered_data = data.copy()
        if selected_countries:
            filtered_data = filtered_data[filtered_data["Country"].isin(selected_countries)]
        if selected_states:
            filtered_data = filtered_data[filtered_data["State"].isin(selected_states)]

        # --- ✅ DISPLAY METRICS ---
        st.markdown("<h2>📊 Sales & Profit Metrics</h2>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Total Sales", f"${filtered_data['Sales'].sum():,.2f}")
        col2.metric("📈 Total Profit", f"${filtered_data['Profit'].sum():,.2f}")
        col3.metric("📊 Avg. Sales per City", f"${filtered_data.groupby('City')['Sales'].sum().mean():,.2f}")
        col4.metric("🏢 Total Cities", f"{filtered_data['City'].nunique()}")

        # --- ✅ SALES HEATMAP ---
        st.markdown("<h2>📍 Sales Heatmap</h2>", unsafe_allow_html=True)
        map_center = [filtered_data["Latitude"].mean(), filtered_data["Longitude"].mean()]
        sales_map = folium.Map(location=map_center, zoom_start=5)

        # ✅ Add Heatmap Layer
        heat_data = filtered_data[['Latitude', 'Longitude', 'Sales']].values.tolist()
        HeatMap(heat_data, radius=10, blur=15, max_zoom=1).add_to(sales_map)

        # ✅ Display Map
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st_folium(sales_map, width=1000, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- ✅ TOP 10 HIGH-SALES CITIES ---
        st.markdown("<h2>🏆 Top 10 High-Sales Cities</h2>", unsafe_allow_html=True)
        top_cities = filtered_data.groupby(["City", "State", "Country"]).sum().reset_index().nlargest(10, "Sales")
        st.dataframe(top_cities[["City", "State", "Country", "Sales", "Profit"]])

        # --- ✅ SALES BY COUNTRY BAR CHART ---
        st.markdown("<h2>📊 Sales by Country</h2>", unsafe_allow_html=True)
        sales_by_country = filtered_data.groupby("Country")["Sales"].sum().reset_index()
        fig1 = px.bar(sales_by_country, x="Country", y="Sales", title="Total Sales by Country", color="Sales")
        st.plotly_chart(fig1)

        # --- ✅ SALES BY STATE BAR CHART ---
        st.markdown("<h2>📊 Sales by State</h2>", unsafe_allow_html=True)
        sales_by_state = filtered_data.groupby("State")["Sales"].sum().reset_index()
        fig2 = px.bar(sales_by_state, x="State", y="Sales", title="Total Sales by State", color="Sales")
        st.plotly_chart(fig2)

    else:
        st.warning("⚠️ Please upload a CSV file to proceed.")
