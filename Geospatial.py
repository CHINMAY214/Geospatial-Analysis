import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from datetime import datetime
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(page_title="Geospatial Sales Analysis", layout="wide")

# Custom CSS for styling
custom_css = """
<style>
/* Background and Font */
body {
    background-color: #f8f9fa;
    font-family: 'Arial', sans-serif;
}

/* Main Heading */
h1 {
    color: #007bff;
    text-align: center;
    font-weight: bold;
}

/* Sidebar Styling */
.sidebar .sidebar-content {
    background-color: #f1f1f1;
    padding: 15px;
    border-radius: 10px;
}

/* Buttons */
.stButton>button {
    background-color: #007bff !important;
    color: white !important;
    border-radius: 10px;
    font-size: 16px;
    padding: 10px;
}

/* Data Table */
.stDataFrame {
    border-radius: 10px;
    box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
}

/* Metrics */
.stMetric {
    text-align: center;
    font-weight: bold;
    font-size: 20px;
    color: #17a2b8;
}

/* Map Container */
.map-container {
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
</style>
"""

# Apply CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Load datasets
@st.cache_data

# Load datasets with proper encoding
def load_data():
    sales_data = pd.read_csv("Global_Superstore2.csv", encoding="ISO-8859-1", parse_dates=["Order Date"])
    world_cities = pd.read_csv("worldcities.csv", encoding="utf-8")

    # Merge sales data with latitude & longitude
    world_cities = world_cities.rename(columns={"city": "City", "country": "Country", "lat": "Latitude", "lng": "Longitude"})
    merged_data = sales_data.merge(world_cities[["City", "Country", "Latitude", "Longitude"]], on=["City", "Country"], how="left")
    merged_data.dropna(subset=["Latitude", "Longitude"], inplace=True)

    return merged_data


# Load data
data = load_data()

# Sidebar Filters
st.sidebar.markdown("<h2>🔍 Filters</h2>", unsafe_allow_html=True)
start_date = st.sidebar.date_input("📅 Start Date", min(data["Order Date"]))
end_date = st.sidebar.date_input("📅 End Date", max(data["Order Date"]))
all_countries = sorted(data["Country"].unique())
selected_countries = st.sidebar.multiselect("🌍 Select Country", all_countries, default=all_countries[:5])

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

# Display Map with Styled Container
st.markdown('<div class="map-container">', unsafe_allow_html=True)
st_folium(sales_map, width=1000, height=600)
st.markdown('</div>', unsafe_allow_html=True)

# Display Top 10 High-Sales Cities
st.markdown("<h2>🏆 Top 10 High-Sales Cities</h2>", unsafe_allow_html=True)
st.dataframe(top_cities)
