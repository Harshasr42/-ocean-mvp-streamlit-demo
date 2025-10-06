# Ocean MVP Streamlit Demo

A comprehensive Ocean Data Integration Platform with Fisherman Dashboard built with Streamlit and FastAPI.

## Features

- 🌊 **Real-time Ocean Data Dashboard**
- 🚢 **Vessel Tracking and Management**
- 🐟 **Catch Reporting System**
- 📊 **Advanced Analytics and Visualizations**
- 🗺️ **Interactive Maps with Folium**
- 🧬 **eDNA Sample Analysis**
- ⚙️ **System Health Monitoring**

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI (simple_main.py)
- **Data Visualization**: Plotly, Folium
- **Database**: Mock data storage
- **Deployment**: Streamlit Cloud

## Quick Start

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run the Streamlit app**: `streamlit run streamlit_app.py`
4. **Access the dashboard**: http://localhost:8501

## API Endpoints

The backend provides the following endpoints:

- `/api/species` - Species occurrence data
- `/api/vessels` - Vessel tracking data
- `/api/catch-reports` - Catch reporting
- `/api/edna` - eDNA samples
- `/api/analytics/dashboard` - Dashboard analytics
- `/health` - System health check

## Deployment

This app is ready for deployment on Streamlit Cloud:

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy with `streamlit_app.py` as the main file

## License

MIT License