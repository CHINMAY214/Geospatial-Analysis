import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import yaml
import bcrypt

# ✅ Set Streamlit page configuration
st.set_page_config(page_title="Sales Heatmap Analysis", layout="wide")

# ✅ Load user credentials from YAML file
def load_credentials():
    with open("credentials.yaml", "r") as file:
        return yaml.safe_load(file)

def save_credentials(credentials):
    with open("credentials.yaml", "w") as file:
        yaml.dump(credentials, file, default_flow_style=False)

# ✅ Hash passwords before saving
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# ✅ Function to check login
def authenticate(username, password):
    credentials = load_credentials()
    if username in credentials["credentials"]:
        stored_password = credentials["credentials"][username]["password"]
        return bcrypt.checkpw(password.encode(), stored_password.encode())
    return False

# ✅ Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN & SIGN-UP PAGE ---
st.title("🔐 Login or Sign Up")

option = st.radio("Select an option:", ["Login", "Sign Up"])

if option == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password!")

elif option == "Sign Up":
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if new_password != confirm_password:
            st.error("❌ Passwords do not match!")
        else:
            credentials = load_credentials()
            if new_username in credentials["credentials"]:
                st.error("❌ Username already exists! Choose another.")
            else:
                credentials["credentials"][new_username] = {"password": hash_password(new_password)}
                save_credentials(credentials)
                st.success("✅ Account created successfully! Please log in.")

# --- DASHBOARD ---
if st.session_state.logged_in:
    st.sidebar.success(f"Welcome, {st.session_state.username} 👋")

    # ✅ Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # ✅ Streamlit app title
    st.title("📍 Sales Heatmap with High-Sales City Markers")

    # ✅ File upload section
    st.sidebar.markdown("### 📂 Upload Pre-Merged Dataset")
    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file:
        # ✅ Load dataset
        data = pd.read_csv(uploaded_file, encoding="ISO-8859-1")

        # ✅ Ensure required columns exist
        required_columns = {"City", "Country", "Sales", "Latitude", "Longitude"}
        if not required_columns.issubset(set(data.columns)):
            st.error(f"❌ Dataset is missing required columns! Expected: {required_columns}")
            st.stop()

        # ✅ Drop rows with missing Latitude/Longitude
        data = data.dropna(subset=["Latitude", "Longitude"])

        # ✅ Check if dataset has valid locations
        if data.empty:
            st.error("❌ No valid location data available. Please check your dataset.")
            st.stop()

        # ✅ Compute the map center
        map_center = [data["Latitude"].mean(), data["Longitude"].mean()]
        sales_map = folium.Map(location=map_center, zoom_start=3)

        # ✅ Prepare data for the heatmap
        heat_data = data[['Latitude', 'Longitude', 'Sales']].values.tolist()
        HeatMap(heat_data, radius=10, blur=15, max_zoom=1).add_to(sales_map)

        # ✅ Identify the top 10 high-sales cities
        top_10_sales_cities = data.nlargest(10, 'Sales')[["City", "Country", "Latitude", "Longitude", "Sales"]]

        # ✅ Add markers for the top 10 high-sales cities
        for _, row in top_10_sales_cities.iterrows():
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=f"{row['City']}, {row['Country']}<br>Sales: ${row['Sales']:,}",
                icon=folium.Icon(color="red", icon="info-sign")  # Red marker for high-sales cities
            ).add_to(sales_map)

        # ✅ Display Map inside Streamlit
        st.markdown("<h2>📊 Sales Heatmap</h2>", unsafe_allow_html=True)
        st_folium(sales_map, width=1000, height=600)

        # ✅ Display Top 10 High-Sales Cities Table
        st.markdown("<h2>🏆 Top 10 High-Sales Cities</h2>", unsafe_allow_html=True)
        st.dataframe(top_10_sales_cities)

    else:
        st.warning("⚠️ Please upload a CSV file to proceed.")
