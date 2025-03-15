import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from datetime import datetime
from streamlit_folium import st_folium
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import bcrypt

# Page configuration
st.set_page_config(page_title="Geospatial Sales Analysis", layout="wide")

# Load user credentials
with open("credentials.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Authentication setup
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# Login page
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.success(f"Welcome, {name} 👋")
    
    # Session state for saved user preferences
    if "saved_filters" not in st.session_state:
        st.session_state["saved_filters"] = {}

    # Custom CSS
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

    # Load datasets
    def load_data():
        sales_data = pd.read_csv("Global_Superstore2.csv", encoding="ISO-8859-1", parse_dates=["Order Date"])
        world_cities = pd.read_csv("worldcities.csv", encoding="utf-8")

        world_cities = world_cities.rename(columns={"city": "City", "country": "Country", "lat": "Latitude", "lng": "Longitude"})
        merged_data = sales_data.merge(world_cities[["City", "Country", "Latitude", "Longitude"]], on=["City", "Country"], how="left")
        merged_data.dropna(subset=["Latitude", "Longitude"], inplace=True)

        return merged_data

    data = load_data()

    # Sidebar Filters
    st.sidebar.markdown("<h2>🔍 Filters & Data Upload</h2>", unsafe_allow_html=True)

    # File Upload
    uploaded_file = st.sidebar.file_uploader("Upload Sales Data (CSV)", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file, encoding="ISO-8859-1", parse_dates=["Order Date"])

    # Sidebar Filters
    start_date = st.sidebar.date_input("📅 Start Date", min(data["Order Date"]))
    end_date = st.sidebar.date_input("📅 End Date", max(data["Order Date"]))
    all_countries = sorted(data["Country"].unique())
    selected_countries = st.sidebar.multiselect("🌍 Select Country", all_countries, default=all_countries[:5])

    # Save user preferences
    if st.sidebar.button("Save Preferences"):
        st.session_state["saved_filters"][username] = {"start_date": start_date, "end_date": end_date, "countries": selected_countries}
        st.sidebar.success("Preferences saved!")

    # Load saved preferences
    if username in st.session_state["saved_filters"]:
        saved_filters = st.session_state["saved_filters"][username]
        start_date = saved_filters["start_date"]
        end_date = saved_filters["end_date"]
        selected_countries = saved_filters["countries"]

    # Apply Filters
    filtered_data = data[(data["Order Date"] >= pd.to_datetime(start_date)) & (data["Order Date"] <= pd.to_datetime(end_date))]
    if selected_countries:
        filtered_data = filtered_data[filtered_data["Country"].isin(selected_countries)]

    # Display Metrics
    st.markdown("<h2>📊 Sales Metrics</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("💰 Total Sales", f"${filtered_data['Sales'].sum():,.2f}")
    col2.metric("🛒 Total Transactions", f"{filtered_data.shape[0]:,}")

    # Create Heatmap
    st.markdown("<h2>📍 Sales Heatmap</h2>", unsafe_allow_html=True)
    map_center = [filtered_data["Latitude"].mean(), filtered_data["Longitude"].mean()]
    sales_map = folium.Map(location=map_center, zoom_start=3)

    # Add Heatmap Layer
    heat_data = filtered_data[['Latitude', 'Longitude', 'Sales']].values.tolist()
    HeatMap(heat_data, radius=10, blur=15, max_zoom=1).add_to(sales_map)

    # Add Markers for Top 10 High-Sales Cities
    top_cities = filtered_data.nlargest(10, 'Sales')[["City", "Country", "Latitude", "Longitude", "Sales"]]
    for _, row in top_cities.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row['City']}, {row['Country']}<br>Sales: ${row['Sales']:,}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(sales_map)

    st_folium(sales_map, width=1000, height=600)

    # Display Top 10 High-Sales Cities
    st.markdown("<h2>🏆 Top 10 High-Sales Cities</h2>", unsafe_allow_html=True)
    st.dataframe(top_cities)

    # Logout button
    authenticator.logout("Logout", "sidebar")

elif authentication_status is False:
    st.error("Incorrect username or password.")
elif authentication_status is None:
    st.warning("Please enter your credentials.")
