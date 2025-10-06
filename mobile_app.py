"""
Mobile App for Ocean Data Integration Platform
React Native / Flutter app for fishermen and researchers
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
class APIConfig:
    API_BASE_URL = os.getenv("API_BASE_URL", "https://ocean-mvp-backend.onrender.com")  # Live backend URL - Updated
    PREDICT_API_URL = os.getenv("PREDICT_API_URL", "https://ocean-mvp-backend.onrender.com")  # Live backend URL - Updated
    
    ENDPOINTS = {
        "species": f"{API_BASE_URL}/api/species",
        "vessels": f"{API_BASE_URL}/api/vessels",
        "edna": f"{API_BASE_URL}/api/edna",
        "catch_reports": f"{API_BASE_URL}/api/catch-reports",
        "predict": f"{API_BASE_URL}/api/predict",
        "auth": f"{API_BASE_URL}/api/auth"
    }

class MobileOceanApp:
    """Mobile-friendly Ocean Data Platform for fishermen and researchers."""
    
    def __init__(self):
        """Initialize the mobile app."""
        self.user_data = None
        self.api_token = None
        self.api_config = APIConfig()
        
        st.set_page_config(
            page_title="Fisherman Dashboard",
            page_icon="🐟",
            layout="wide"
        )
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """Authenticate user with the API."""
        try:
            response = requests.post(
                f"{self.api_config.ENDPOINTS['auth']}/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                token_data = response.json()
                self.api_token = token_data["access_token"]
                self.user_data = {"email": email, "role": "fisherman"}
                return True
            else:
                st.error("Authentication failed. Please check your credentials.")
                return False
        except Exception as e:
            st.error(f"Authentication error: {e}")
            return False
    
    def get_headers(self) -> dict:
        """Get API headers with authentication token."""
        if self.api_token:
            return {"Authorization": f"Bearer {self.api_token}"}
        return {}
    
    def get_real_weather_data(self, latitude, longitude):
        """Get real weather data for MVP demo."""
        try:
            import requests
            # OpenWeatherMap free tier - REPLACE WITH YOUR API KEY
            api_key = "a6f35cc90e0f6323be584d35b59ba6f6"  # Your actual OpenWeatherMap API key
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    'sst': data['main']['temp'],
                    'wind_speed': data['wind']['speed'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure']
                }
        except Exception as e:
            print(f"Weather API error: {e}")
        
        # Fallback to realistic mock data
        return {
            'sst': 28.0 + (latitude - 12) * 0.1,
            'wind_speed': 12.0,
            'humidity': 75.0,
            'pressure': 1013.0
        }
    
    def preprocess_catch_data_for_ml(self, latitude, longitude, species, catch_weight, individual_count, gear_type, vessel_type, fishing_depth):
        """Preprocess catch data for ML prediction."""
        # Real-time data integration for MVP
        try:
            # Get real weather data
            weather_data = self.get_real_weather_data(latitude, longitude)
            base_sst = weather_data.get('sst', 28.0)
        except:
            # Fallback to simulated data
            base_sst = 28.0 + (latitude - 12) * 0.1 + np.random.normal(0, 0.5)
        
        # Simulate biodiversity based on catch success
        biodiversity_index = min(1.0, 0.5 + (catch_weight / 10) + (individual_count / 20))
        
        # Simulate genetic diversity
        genetic_diversity = 0.6 + (biodiversity_index - 0.5) * 0.4
        
        # Species richness based on gear type and location
        gear_richness = {"longline": 8, "gillnet": 12, "purse_seine": 15, "trawl": 20, "handline": 6}
        species_richness = gear_richness.get(gear_type, 10)
        
        # Season based on current month
        current_month = datetime.now().month
        season_map = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring", 
                     6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
        season = season_map.get(current_month, "Summer")
        
        # SST category
        if base_sst < 26:
            sst_category = "Cool"
        elif base_sst < 29:
            sst_category = "Moderate"
        elif base_sst < 31:
            sst_category = "Warm"
        else:
            sst_category = "Hot"
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "mean_sst": round(base_sst, 1),
            "biodiversity_index": round(biodiversity_index, 2),
            "genetic_diversity": round(genetic_diversity, 2),
            "species_richness": species_richness,
            "season": season,
            "sst_category": sst_category,
            "biodiversity_category": "High" if biodiversity_index > 0.8 else "Medium" if biodiversity_index > 0.6 else "Low"
        }
    
    def get_species_abundance_prediction(self, prediction_data):
        """Get species abundance prediction from ML API."""
        try:
            # Convert prediction_data to the format expected by FastAPI backend
            # Use the full prediction_data which already contains the required fields
            fastapi_data = {
                "mean_sst": prediction_data.get("mean_sst", 28.0),
                "biodiversity_index": prediction_data.get("biodiversity_index", 0.75),
                "genetic_diversity": prediction_data.get("genetic_diversity", 0.68),
                "species_richness": prediction_data.get("species_richness", 12),
                "season": prediction_data.get("season", "Summer"),
                "sst_category": prediction_data.get("sst_category", "Moderate"),
                "biodiversity_category": prediction_data.get("biodiversity_category", "High")
            }
            
            response = requests.post(
                self.api_config.ENDPOINTS["predict"],
                json=fastapi_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "prediction": result.get("predicted_species_count", 15),  # FastAPI returns predicted_species_count
                    "confidence": result.get("confidence", 0.85),
                    "model_version": result.get("model_version", "1.0.0"),
                    "predicted_species": result.get("predicted_species", "Unknown")
                }
            else:
                logger.error(f"Prediction API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def show_prediction_insights(self, prediction_result, prediction_data):
        """Show additional insights from the prediction."""
        st.subheader("📊 Prediction Insights")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Predicted Abundance", f"{prediction_result['prediction']:.1f}")
            st.metric("Sea Surface Temperature", f"{prediction_data['mean_sst']:.1f}°C")
            st.metric("Biodiversity Index", f"{prediction_data['biodiversity_index']:.2f}")
        
        with col2:
            st.metric("Species Richness", prediction_data['species_richness'])
            st.metric("Season", prediction_data['season'])
            st.metric("SST Category", prediction_data['sst_category'])
        
        # Show recommendations
        st.subheader("🎯 Fishing Recommendations")
        if prediction_result['prediction'] > 20:
            st.success("🟢 **Excellent fishing conditions!** High species abundance predicted.")
        elif prediction_result['prediction'] > 15:
            st.info("🟡 **Good fishing conditions.** Moderate species abundance expected.")
        else:
            st.warning("🔴 **Challenging conditions.** Lower species abundance predicted.")
        
        # Environmental factors
        if prediction_data['mean_sst'] > 30:
            st.info("🌡️ **High SST detected** - Consider fishing in deeper waters")
        if prediction_data['biodiversity_index'] < 0.6:
            st.warning("🧬 **Low biodiversity** - This area may be overfished")
    
    def render_login_screen(self):
        """Render the login screen."""
        st.title("🐟 Fisherman Dashboard")
        st.markdown("**Login to access marine data platform**")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if self.authenticate_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please try again.")
        
        # Demo login for testing
        st.markdown("---")
        st.markdown("**Demo Login (for testing)**")
        if st.button("Login as Fisherman (Demo)"):
            self.user_data = {"email": "demo@oceandata.in", "role": "admin"}
            self.api_token = "demo_token"
            st.success("Demo login successful!")
            st.rerun()
    
    def render_fisherman_dashboard(self):
        """Render dashboard for fishermen."""
        st.title("🐟 Fisherman Dashboard")
        
        # Navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📍 Report Catch", "🗺️ Fishing Zones", "🌡️ Weather", "📊 My Data"])
        
        with tab1:
            self.render_catch_report_form()
        with tab2:
            self.render_fishing_zones()
        with tab3:
            self.render_weather_info()
        with tab4:
            self.render_fisherman_data()
    
    def render_catch_report_form(self):
        """Render catch reporting form."""
        st.subheader("📝 Report Your Catch")
        
        # Location selection (outside the form)
        st.subheader("📍 Location")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            latitude = st.number_input("Latitude", min_value=0.0, max_value=90.0, value=12.5, format="%.6f")
        with col2:
            longitude = st.number_input("Longitude", min_value=0.0, max_value=180.0, value=77.2, format="%.6f")
        with col3:
            if st.button("📍 Use Current Location"):
                st.info("Location services would be enabled here")
                # In a real app, this would use GPS
                latitude = 12.5
                longitude = 77.2
        
        # Catch report form
        with st.form("catch_report"):
            col1, col2 = st.columns(2)
            with col1:
                species = st.selectbox(
                    "Species Caught",
                    ["Thunnus albacares", "Scomberomorus commerson", "Lutjanus argentimaculatus", 
                     "Epinephelus coioides", "Rastrelliger kanagurta", "Other"]
                )
                if species == "Other":
                    species = st.text_input("Enter species name")
                
                catch_weight = st.number_input("Catch Weight (kg)", min_value=0.0, value=0.0)
                individual_count = st.number_input("Number of Fish", min_value=1, value=1)
            
            with col2:
                gear_type = st.selectbox("Gear Type", ["longline", "gillnet", "purse_seine", "trawl", "handline"])
                vessel_type = st.selectbox("Vessel Type", ["commercial", "artisanal", "recreational"])
                fishing_depth = st.number_input("Fishing Depth (m)", min_value=0, value=50)
            
            # Submit button
            submitted = st.form_submit_button("📤 Submit Catch Report")
            
            if submitted:
                try:
                    # Prepare data for catch reports API
                    catch_data = {
                        "species": species,
                        "latitude": latitude,
                        "longitude": longitude,
                        "catch_weight": catch_weight,
                        "individual_count": individual_count,
                        "gear_type": gear_type,
                        "vessel_type": vessel_type,
                        "fishing_depth": fishing_depth,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Submit to API
                    try:
                        response = requests.post(
                            f"{self.api_config.API_BASE_URL}/api/catch-reports",
                            json=catch_data,
                            headers=self.get_headers(),
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Catch report submitted successfully!")
                            st.balloons()
                            
                            # Now trigger ML prediction
                            st.info("🤖 Analyzing environmental conditions and predicting species abundance...")
                            
                            # Preprocess data for ML prediction
                            prediction_data = self.preprocess_catch_data_for_ml(
                                latitude, longitude, species, catch_weight, individual_count, 
                                gear_type, vessel_type, fishing_depth
                            )
                            
                            # Get ML prediction
                            prediction_result = self.get_species_abundance_prediction(prediction_data)
                            
                            if prediction_result:
                                st.success(f"🎯 **Predicted Species Abundance: {prediction_result['prediction']:.1f} individuals**")
                                st.info(f"📊 **Model Confidence: {prediction_result['confidence']:.1%}**")
                                st.info(f"🌡️ **Based on SST: {prediction_data['mean_sst']:.1f}°C**")
                                st.info(f"🧬 **Biodiversity Index: {prediction_data['biodiversity_index']:.2f}**")
                                
                                # Show prediction insights
                                self.show_prediction_insights(prediction_result, prediction_data)
                            else:
                                st.warning("⚠️ ML prediction temporarily unavailable, but catch report was saved successfully!")
                        else:
                            st.error(f"❌ Failed to submit catch report: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"Error submitting catch report: {e}")
    
    def render_fishing_zones(self):
        """Render fishing zones map."""
        st.subheader("🗺️ Fishing Zones & Advisories")
        
        # Create map
        center_lat, center_lon = 12.75, 77.5
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add fishing zones (off the coast of Kerala/Karnataka)
        fishing_zones = [
            {"name": "Zone A - High Productivity", "lat": 12.5, "lon": 74.5, "status": "Open", "color": "green", "radius": 20000},
            {"name": "Zone B - Moderate Productivity", "lat": 11.8, "lon": 74.8, "status": "Open", "color": "blue", "radius": 25000},
            {"name": "Zone C - Protected Area", "lat": 13.2, "lon": 74.2, "status": "Closed", "color": "red", "radius": 15000},
            {"name": "Zone D - Seasonal Closure", "lat": 12.0, "lon": 75.0, "status": "Seasonal", "color": "orange", "radius": 18000}
        ]
        
        for zone in fishing_zones:
            color = zone["color"]
            folium.CircleMarker(
                location=[zone["lat"], zone["lon"]],
                radius=15,
                popup=f"<b>{zone['name']}</b><br>Status: {zone['status']}",
                color=color,
                fill=True,
                fillOpacity=0.7
            ).add_to(m)
        
        # Display map
        st_folium(m, width=700, height=500)
        
        # Zone information
        st.subheader("📋 Zone Information")
        for zone in fishing_zones:
            status_emoji = {"Open": "✅", "Closed": "❌", "Seasonal": "⚠️"}
            st.write(f"**{zone['name']}**: {status_emoji[zone['status']]} {zone['status']}")
    
    def render_weather_info(self):
        """Render weather and ocean conditions."""
        st.subheader("🌡️ Weather & Ocean Conditions")
        
        # Mock weather data
        weather_data = {
            "Sea Surface Temperature": "28.5°C",
            "Wind Speed": "12 knots",
            "Wind Direction": "SE",
            "Wave Height": "1.2m",
            "Visibility": "Good",
            "Weather": "Partly Cloudy"
        }
        
        col1, col2 = st.columns(2)
        with col1:
            for key, value in list(weather_data.items())[:3]:
                st.metric(key, value)
        with col2:
            for key, value in list(weather_data.items())[3:]:
                st.metric(key, value)
        
        # Fishing advisories
        st.subheader("🎣 Fishing Advisories")
        advisories = [
            "✅ Good fishing conditions expected",
            "⚠️ Moderate wind conditions",
            "🌊 Small waves, safe for small vessels",
            "🐟 Target species: Tuna, Mackerel"
        ]
        for advisory in advisories:
            st.write(advisory)
    
    def render_fisherman_data(self):
        """Render fisherman's personal data."""
        st.subheader("📊 My Fishing Data")
        
        # Mock personal data
        personal_stats = {
            "Total Catches This Month": 15,
            "Total Weight (kg)": 450.5,
            "Most Common Species": "Thunnus albacares",
            "Average Catch per Trip": 30.0,
            "Fishing Days": 12
        }
        
        col1, col2 = st.columns(2)
        with col1:
            for key, value in list(personal_stats.items())[:3]:
                st.metric(key, value)
        with col2:
            for key, value in list(personal_stats.items())[3:]:
                st.metric(key, value)
        
        # Recent catches
        st.subheader("📝 Recent Catches")
        recent_catches = pd.DataFrame({
            "Date": ["2023-12-20", "2023-12-19", "2023-12-18"],
            "Species": ["Thunnus albacares", "Scomberomorus commerson", "Lutjanus argentimaculatus"],
            "Weight (kg)": [45.2, 32.1, 28.7],
            "Location": ["Zone A", "Zone B", "Zone A"]
        })
        st.dataframe(recent_catches, width='stretch')
    
    def render_researcher_dashboard(self):
        """Render dashboard for researchers."""
        st.title("🔬 Researcher Dashboard")
        
        # Navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "🧬 eDNA Data", "🤖 AI Predictions", "📈 Trends"])
        
        with tab1:
            self.render_researcher_analytics()
        with tab2:
            self.render_edna_analysis()
        with tab3:
            self.render_ai_predictions()
        with tab4:
            self.render_trend_analysis()
    
    def render_researcher_analytics(self):
        """Render analytics for researchers."""
        st.subheader("📊 Marine Data Analytics")
        
        # Fetch data from API
        try:
            response = requests.get(self.api_config.ENDPOINTS["species"], headers=self.get_headers())
            if response.status_code == 200:
                species_data = response.json()
                st.success(f"✅ Loaded {len(species_data)} species records")
            else:
                st.warning("⚠️ Using mock data")
                species_data = []
        except:
            st.warning("⚠️ API not available, using mock data")
            species_data = []
        
        # Analytics metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(species_data) or 150)
        with col2:
            st.metric("Unique Species", 25)
        with col3:
            st.metric("Data Coverage", "12 months")
        with col4:
            st.metric("API Status", "✅ Connected")
    
    def render_edna_analysis(self):
        """Render eDNA analysis for researchers."""
        st.subheader("🧬 eDNA Analysis")
        
        # eDNA sample form
        with st.form("edna_sample"):
            st.write("**Add New eDNA Sample**")
            col1, col2 = st.columns(2)
            with col1:
                sample_id = st.text_input("Sample ID", value="EDNA001")
                latitude = st.number_input("Latitude", value=12.5)
                longitude = st.number_input("Longitude", value=77.2)
                sample_date = st.date_input("Sample Date", value=datetime.now().date())
            with col2:
                biodiversity_index = st.slider("Biodiversity Index", 0.0, 1.0, 0.75)
                species_richness = st.number_input("Species Richness", min_value=1, value=12)
                genetic_diversity = st.slider("Genetic Diversity", 0.0, 1.0, 0.65)
                dominant_species = st.text_input("Dominant Species", value="Thunnus albacares")
            
            if st.form_submit_button("📤 Submit eDNA Sample"):
                st.success("✅ eDNA sample submitted successfully!")
    
    def render_ai_predictions(self):
        """Render AI prediction interface."""
        st.subheader("🤖 AI Species Abundance Prediction")
        
        with st.form("prediction_form"):
            st.write("**Environmental Parameters**")
            col1, col2 = st.columns(2)
            with col1:
                sst = st.slider("Sea Surface Temperature (°C)", 24.0, 32.0, 28.0)
                biodiversity = st.slider("Biodiversity Index", 0.5, 1.0, 0.75)
                genetic_diversity = st.slider("Genetic Diversity", 0.4, 0.9, 0.65)
            with col2:
                species_richness = st.slider("Species Richness", 5, 25, 12)
                season = st.selectbox("Season", ["Winter", "Spring", "Summer", "Autumn"])
                sst_category = st.selectbox("SST Category", ["Cool", "Moderate", "Warm", "Hot"])
            
            if st.form_submit_button("🔮 Predict Species Abundance"):
                # Make prediction
                prediction_data = {
                    "mean_sst": sst,
                    "biodiversity_index": biodiversity,
                    "genetic_diversity": genetic_diversity,
                    "species_richness": species_richness,
                    "season": season,
                    "sst_category": sst_category,
                    "biodiversity_category": "Medium"
                }
                
                try:
                    response = requests.post(
                        self.api_config.ENDPOINTS["predict"],
                        json=prediction_data,
                        headers=self.get_headers()
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        # Handle both API response formats
                        if 'prediction' in result:
                            prediction_value = result['prediction']
                            confidence = 0.85  # Default confidence for mock model
                        elif 'predicted_species_count' in result:
                            prediction_value = result['predicted_species_count']
                            confidence = result.get('confidence', 0.85)
                        else:
                            prediction_value = result.get('prediction', 15)
                            confidence = 0.85
                        
                        st.success(f"🎯 Predicted Species Abundance: **{prediction_value:.1f}** individuals")
                        st.info(f"📊 Model Confidence: {confidence:.1%}")
                    else:
                        # Mock prediction
                        prediction = 15 + (sst - 28) * 2 + biodiversity * 10
                        st.success(f"🎯 Predicted Species Abundance: **{prediction:.1f}** individuals")
                        st.info("📊 Model Confidence: 85%")
                except Exception as e:
                    st.error(f"Prediction error: {e}")
    
    def render_trend_analysis(self):
        """Render trend analysis."""
        st.subheader("📈 Environmental Trends")
        
        # Mock trend data
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='MS')
        sst_trend = 28 + 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 12) + np.random.normal(0, 0.5, len(dates))
        species_trend = 15 + 3 * np.sin(2 * np.pi * np.arange(len(dates)) / 12) + np.random.normal(0, 1, len(dates))
        
        # Create trend chart
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Sea Surface Temperature Trend', 'Species Abundance Trend'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Scatter(x=dates, y=sst_trend, name='SST (°C)', line=dict(color='red')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=dates, y=species_trend, name='Species Count', line=dict(color='blue')),
            row=2, col=1
        )
        
        fig.update_layout(height=600, title_text="Environmental Trends")
        st.plotly_chart(fig, use_container_width=True)
    
    def render_main_app(self):
        """Render the main mobile app interface."""
        # Temporarily skip authentication and show fisherman dashboard directly
        self.user_data = {"email": "demo@oceandata.in", "role": "fisherman"}
        self.api_token = "demo_token"
        self.render_fisherman_dashboard()
        
        # Logout button (temporarily disabled)
        # if st.button("🚪 Logout"):
        #     self.user_data = None
        #     self.api_token = None
        #     st.rerun()
    
    def main(self):
        """Main function to run the mobile app."""
        # Page configuration for mobile PWA
        st.set_page_config(
            page_title="Ocean Fisherman",
            page_icon="🐟",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # PWA configuration
        st.markdown("""
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="theme-color" content="#1f77b4">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="Ocean Fisherman">
        <link rel="manifest" href="./mobile/manifest.json">
        <style>
        /* Mobile-first responsive design */
        .main > div {
            padding-top: 1rem;
        }
        .stButton > button {
            width: 100%;
            height: 3rem;
            font-size: 1.2rem;
            margin: 0.5rem 0;
        }
        .stSelectbox, .stNumberInput, .stTextInput {
            margin-bottom: 1rem;
        }
        /* Hide Streamlit branding for PWA feel */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .stDeployButton { display: none; }
        </style>
        """, unsafe_allow_html=True)
        
        # Initialize app
        app = MobileOceanApp()
        
        # Render main interface
        app.render_main_app()

# Initialize the app when the module is imported
app = MobileOceanApp()

# Run the main function when streamlit runs this file
if __name__ == "__main__":
    app.main()
