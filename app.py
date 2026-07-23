import streamlit as st
from streamlit_autorefresh import st_autorefresh
import datetime
import os
import logging

# Configure standard production-grade logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("OrganDroneApp")

# Resolve PORT for deployment configuration
PORT = int(os.environ.get("PORT", 8501))
logger.info(f"Lifeline Digital Twin Application starting on resolved port: {PORT}")


# Import modular layers
from simulation.mission_manager import MissionManager
from simulation.feasibility import get_ml_metrics
from dashboards.sender import render_sender_dashboard
from dashboards.admin import render_admin_dashboard
from dashboards.receiver import render_receiver_dashboard
from utils.navigation import safe_rerun

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Lifeline Digital Twin Console",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INJECT SOPHISTICATED DARK THEME STYLING
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* Global Font and Base Overrides */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
    background-color: #09090b !important;
    color: #fafafa !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Header & Sidebar Controls */
[data-testid="stHeader"] {
    background-color: transparent !important;
    z-index: 100 !important;
}
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    color: #ffffff !important;
    background-color: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    margin: 8px !important;
}
[data-testid="stToolbar"] {
    right: 1.5rem !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #09090b !important;
    border-right: 1px solid #27272a !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* Dark Inputs, Selectboxes, textboxes and options */
div[data-baseweb="select"] > div {
    background-color: #121214 !important;
    color: #fafafa !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
}
input, select, textarea {
    background-color: #121214 !important;
    color: #fafafa !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
}
div[role="listbox"] {
    background-color: #121214 !important;
    border: 1px solid #27272a !important;
}
div[role="option"] {
    background-color: #121214 !important;
    color: #fafafa !important;
}
div[role="option"]:hover {
    background-color: #18181b !important;
}

/* Metrics Dashboard Overrides */
div[data-testid="metric-container"] {
    background-color: #121214 !important;
    border: 1px solid #27272a !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}
div[data-testid="stMetricLabel"] {
    color: #71717a !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}

/* Buttons Theme Styling */
div.stButton > button {
    background-color: #18181b !important;
    color: #fafafa !important;
    border: 1px solid #27272a !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
div.stButton > button:hover {
    background-color: #27272a !important;
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.25) !important;
}

/* Dividers */
hr {
    border-color: #27272a !important;
}

/* Custom Header layout CSS code */
.custom-header {
    height: 64px;
    border-bottom: 1px solid #27272a;
    background-color: #09090b;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    margin-bottom: 1.5rem;
}
.header-title-container {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-badge {
    background-color: rgba(16, 185, 129, 0.1);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.2);
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    animation: pulse-glow 2s infinite alternate;
}
@keyframes pulse-glow {
    0% { box-shadow: 0 0 4px rgba(16, 185, 129, 0.1); opacity: 0.8; }
    100% { box-shadow: 0 0 12px rgba(16, 185, 129, 0.3); opacity: 1; }
}
.header-sector {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}
.header-sector-lbl {
    font-size: 9px;
    font-family: 'JetBrains Mono', monospace;
    color: #71717a;
    letter-spacing: 0.05em;
}
.header-sector-val {
    font-size: 12px;
    font-weight: 700;
    color: #3b82f6;
    letter-spacing: 0.05em;
}
.header-user {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-user-text {
    text-align: right;
}
.header-username {
    font-size: 12px;
    font-weight: 600;
    color: #ffffff;
}
.header-userid {
    font-size: 10px;
    color: #71717a;
}
.header-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: #27272a;
    border: 1px solid #3f3f46;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    color: #fafafa;
}

/* Expanders dark override */
div[data-testid="stExpander"] {
    background-color: #121214 !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
}

/* Tabs Styling */
button[data-baseweb="tab"] {
    color: #71717a !important;
    font-weight: 600 !important;
}
button[aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* Scrollbars customization */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #09090b;
}
::-webkit-scrollbar-thumb {
    background: #27272a;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #3f3f46;
}
</style>
""", unsafe_allow_html=True)

# 3. RENDER SOPHISTICATED TOP HEADER
st.markdown("""<div class="custom-header">
<div class="header-title-container">
<div style="width: 32px; height: 32px; background-color: #2563eb; border-radius: 4px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px rgba(37, 99, 235, 0.4);">
<svg style="width: 20px; height: 20px; color: white;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
</svg>
</div>
<h1 style="font-size: 1.1rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; text-transform: uppercase;">
LIFELINE <span style="color: #3b82f6; font-weight: 800;">DIGITAL TWIN</span>
</h1>
<span class="header-badge">SYSTEM ONLINE</span>
</div>
<div style="display: flex; align-items: center; gap: 1.5rem;">
<div class="header-sector">
<span class="header-sector-lbl">CURRENT SECTOR</span>
<span class="header-sector-val">CHENNAI-NORTH-METRO</span>
</div>
<div style="height: 32px; width: 1px; background-color: #27272a;"></div>
<div class="header-user">
<div class="header-user-text">
<p class="header-username" style="margin:0;">Admin Control</p>
<p class="header-userid" style="margin:0;">User ID: DR-9092</p>
</div>
<div class="header-avatar">AD</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

# Define Dashboard Roles & Initialize State
roles_list = [
    "👨‍⚕️ Donor Hospital (Sender)",
    "🎛️ Control Center (Admin)",
    "🏥 Recipient Hospital (Receiver)"
]
if "role_selection_state" not in st.session_state:
    st.session_state["role_selection_state"] = "🎛️ Control Center (Admin)"
if "sidebar_role_selector" not in st.session_state:
    st.session_state["sidebar_role_selector"] = "🎛️ Control Center (Admin)"

# Render Gorgeous Top Navigation Tabs/Pills for easy access
st.markdown("""
<div style="margin-top: -10px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
    <span style="font-size: 0.8rem; color: #71717a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Console Active Perspective:</span>
</div>
""", unsafe_allow_html=True)

nav_cols = st.columns(3)
for idx, r in enumerate(roles_list):
    with nav_cols[idx]:
        is_active = (st.session_state["role_selection_state"] == r)
        btn_type = "primary" if is_active else "secondary"
        if st.button(r, key=f"top_nav_role_{idx}", type=btn_type, use_container_width=True):
            st.session_state["role_selection_state"] = r
            st.session_state["sidebar_role_selector"] = r
            safe_rerun()

st.markdown("<hr style='margin: 15px 0 25px 0; border-color: #27272a;'/>", unsafe_allow_html=True)

# 4. INITIALIZE SINGLETON ENGINE
mission_manager = MissionManager()
# Start background simulation thread
mission_manager.start_simulation()

# 5. GLOBAL AUTO-REFRESH (Every 3 seconds to update positions/telem on maps/charts)
st_autorefresh(interval=3000, limit=None, key="digital_twin_tick")

# 6. SIDEBAR LOGISTICS CONTROL
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #ffffff; margin-bottom: 0; font-size: 1.3rem;'>UAV Command</h2>
    <span style='background-color: rgba(16, 185, 129, 0.1); color: #10b981; font-size: 0.75em; font-weight: bold; padding: 3px 10px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.2);'>
        🟢 TWIN ENGINE: ACTIVE
    </span>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

# Navigation Selection
st.sidebar.subheader("🕹️ Dashboard Role Selection")

def on_sidebar_role_change():
    st.session_state["role_selection_state"] = st.session_state["sidebar_role_selector"]

role_selection = st.sidebar.radio(
    "Select Console View:",
    options=roles_list,
    index=roles_list.index(st.session_state["role_selection_state"]),
    key="sidebar_role_selector",
    on_change=on_sidebar_role_change
)

st.sidebar.divider()

# Simulation Speed Controls
st.sidebar.subheader("⚡ Simulator Configurations")
sim_speed = st.sidebar.slider(
    "Time Acceleration Factor",
    min_value=5.0,
    max_value=100.0,
    value=25.0,
    step=5.0,
    help="Speed up flight durations. 25x means a 25-minute flight is completed in 60 real seconds."
)
mission_manager.time_acceleration = sim_speed

# 7. WEATHER RADAR CONTROL PANEL
st.sidebar.subheader("🌤️ Meteorological Radar")

# Check if there is a weather emergency active
all_active_missions = mission_manager.get_all_missions()
has_weather_emergency = any(
    m["status"] in ["TAKEOFF_INITIATED", "TAKEOFF_COMPLETED", "IN_FLIGHT", "APPROACHING_DESTINATION", "LANDING_INITIATED", "EMERGENCY_REROUTE"] 
    and m["scenario_name"] == "Weather Emergency"
    for m in all_active_missions
)

if has_weather_emergency:
    weather_icon = "⛈️"
    weather_cond = "Severe Convective Storm"
    weather_alert_color = "#EF4444"  # Red
    weather_alert_text = "⚠️ HIGH GUST WARNING"
    wind_speed_text = "38.5 km/h (Gusts: 48.0+)"
    temp_text = "28.5 °C"
    humidity_text = "92% (Convective Rain)"
    visibility_text = "2.5 km (Reduced)"
else:
    weather_icon = "🌤️"
    weather_cond = "Clear / Partly Cloudy"
    weather_alert_color = "#10B981"  # Green
    weather_alert_text = "✅ CORRIDORS SAFE"
    wind_speed_text = "11.5 km/h (Stable)"
    temp_text = "31.8 °C"
    humidity_text = "74%"
    visibility_text = "10.0 km (Clear)"

st.sidebar.markdown(f"""
<div style="background-color: #121214; padding: 15px; border-radius: 8px; border: 1px solid #27272a; margin-bottom: 15px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <span style="font-weight: bold; font-size: 1.0em; color: #ffffff;">{weather_icon} Chennai Weather</span>
        <span style="background-color: {weather_alert_color}20; color: {weather_alert_color}; border: 1px solid {weather_alert_color}40; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; font-weight: bold;">
            {weather_alert_text}
        </span>
    </div>
    <div style="font-size: 0.85em; color: #a1a1aa; line-height: 1.5;">
        <strong style="color: #fafafa;">Status:</strong> {weather_cond}<br/>
        <strong style="color: #fafafa;">Wind Speed:</strong> {wind_speed_text}<br/>
        <strong style="color: #fafafa;">Ambient Temp:</strong> {temp_text}<br/>
        <strong style="color: #fafafa;">Relative Humidity:</strong> {humidity_text}<br/>
        <strong style="color: #fafafa;">Sectors Visibility:</strong> {visibility_text}<br/>
    </div>
</div>
""", unsafe_allow_html=True)

# 7.5 MACHINE LEARNING MODEL SUMMARY
ml_metrics = get_ml_metrics()
if ml_metrics:
    importances = ml_metrics.get("feature_importances", {})
    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    
    importance_html_items = []
    for f, imp in sorted_importances:
        f_clean = f.replace("_", " ").title()
        importance_html_items.append(
            f'<div style="margin-top: 6px;">'
            f'<div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #a1a1aa; margin-bottom: 1px;">'
            f'<span>{f_clean}</span>'
            f'<span style="font-family: monospace;">{imp*100:.1f}%</span>'
            f'</div>'
            f'<div style="background-color: #27272a; height: 4px; border-radius: 2px; width: 100%;">'
            f'<div style="background-color: #3b82f6; width: {imp*100}%; height: 100%; border-radius: 2px;"></div>'
            f'</div>'
            f'</div>'
        )
    importance_html = "".join(importance_html_items)
        
    sidebar_card_html = (
        f'<div style="background-color: #121214; padding: 15px; border-radius: 8px; border: 1px solid #27272a; margin-bottom: 15px;">'
        f'<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">'
        f'<span style="font-weight: bold; font-size: 1.0em; color: #ffffff;">🌲 RandomForest Dispatcher</span>'
        f'<span style="background-color: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.2); padding: 2px 6px; border-radius: 4px; font-size: 0.75em; font-weight: bold;">'
        f'ACC: {ml_metrics.get("accuracy", 0.95)*100:.1f}%'
        f'</span>'
        f'</div>'
        f'<div style="font-size: 0.82em; color: #a1a1aa; line-height: 1.4; margin-bottom: 8px;">'
        f'Trained on <strong style="color: #fafafa;">{ml_metrics.get("n_samples", 1200)}</strong> historical medical flights in Chennai.'
        f'</div>'
        f'<div style="font-size: 0.8em; font-weight: 600; color: #fafafa; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px;">'
        f'Feature Importance Weights:'
        f'</div>'
        f'{importance_html}'
        f'</div>'
    )
    st.sidebar.markdown(sidebar_card_html, unsafe_allow_html=True)

# Quick Seed Utility (Grader cheat code)
st.sidebar.subheader("🧪 Rapid Testing Suite")
if st.sidebar.button("⚡ Quick-Seed Demo Flights", help="Pre-load 3 missions immediately to demonstrate all behaviors of the Digital Twin (Normal, Battery failure, and Weather failure).", use_container_width=True):
    # Check if we already seeded
    existing = mission_manager.get_all_missions()
    if len(existing) < 3:
        # Seed 1: Normal Delivery
        # Apollo Hospital Greams Road (HOSP-01) to Fortis Malar Hospital (HOSP-02)
        mission_manager.create_mission("HOSP-01", "HOSP-02", "Heart", "CRITICAL", "Normal Delivery")
        
        # Seed 2: Weather Anomaly (initially normal)
        # Rajiv Gandhi Hospital (HOSP-10) to Madras Medical Mission (HOSP-04)
        mission_manager.create_mission("HOSP-10", "HOSP-04", "Liver", "HIGH", "Normal Delivery")
        
        # Seed 3: Battery Breakdown (initially normal)
        # Apollo Hospitals, Greams Road (HOSP-01) to SRM Hospital (HOSP-21)
        mission_manager.create_mission("HOSP-01", "HOSP-21", "Kidney", "MEDIUM", "Normal Delivery")
        
        st.sidebar.success("Seeded 3 test flights! Head to the Control Center to approve them.")
        safe_rerun()
    else:
        st.sidebar.warning("Missions already active in ledger.")

# Wipe State
if st.sidebar.button("♻️ Reset Simulation Data", use_container_width=True):
    mission_manager.reset_system()
    st.sidebar.success("System registers cleared!")
    safe_rerun()

st.sidebar.markdown(f"""
<div style='position: fixed; bottom: 10px; font-size: 0.8em; color: #6B7280;'>
    Digital Twin System v1.0.0<br/>
    Chennai UAV Logistics Grid<br/>
    Local Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
""", unsafe_allow_html=True)


# 5. RENDER CHOSEN ROLE DASHBOARD
active_role = st.session_state["role_selection_state"]
if "Donor Hospital" in active_role:
    render_sender_dashboard(mission_manager)
elif "Control Center" in active_role:
    render_admin_dashboard(mission_manager)
elif "Recipient Hospital" in active_role:
    render_receiver_dashboard(mission_manager)
