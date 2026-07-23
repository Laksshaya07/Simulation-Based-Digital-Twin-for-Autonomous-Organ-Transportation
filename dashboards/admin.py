import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

from data.hospitals import HOSPITALS, get_hospital_by_id
from utils.geo import haversine_distance
from simulation.scenarios import SCENARIOS
from utils.navigation import safe_rerun
from simulation.feasibility import predict_realtime_success_probability

def render_admin_dashboard(mission_manager):
    st.markdown("<h2 style='text-align: center; color: #ffffff; font-weight: 700; letter-spacing: -0.02em;'>🎛️ Control Center & Digital Twin Command</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a1a1aa; font-size: 0.95rem; margin-bottom: 20px;'>Real-time monitoring, flight telemetry, predictive analytics, and manual flight override triggers.</p>", unsafe_allow_html=True)
    
    st.divider()

    # 1. ANALYTICS ROW
    all_missions = mission_manager.get_all_missions()
    drones = mission_manager.get_all_drones()
    
    total_missions = len(all_missions)
    completed_missions = len([m for m in all_missions if m["status"] == "MISSION_COMPLETED"])
    emergency_missions = len([m for m in all_missions if m["status"] in ["EMERGENCY_REROUTE", "LANDING_AT_NEAREST_HOSPITAL", "MISSION_ABORTED"]])
    active_missions = len([m for m in all_missions if m["status"] in ["TAKEOFF_INITIATED", "TAKEOFF_COMPLETED", "IN_FLIGHT", "APPROACHING_DESTINATION", "LANDING_INITIATED", "EMERGENCY_REROUTE"]])
    
    # Calculate Success Rate predictively using Random Forest Classifier for active/pending flights
    total_score = 0.0
    count = 0
    for m in all_missions:
        status = m["status"]
        if status == "MISSION_COMPLETED":
            total_score += 100.0
            count += 1
        elif status in ["MISSION_ABORTED", "REJECTED_BY_ADMIN", "REJECTED_BY_FEASIBILITY"]:
            total_score += 0.0
            count += 1
        else:
            drone = mission_manager.get_drone(m["drone_id"])
            if drone:
                prob = predict_realtime_success_probability(m, drone)
                total_score += prob * 100.0
            else:
                total_score += m.get("feasibility_score", 100.0)
            count += 1
            
    if count > 0:
        success_rate = total_score / count
    else:
        success_rate = 100.0
        
    avg_flight_time = "0.0m"
    completed_m_list = [m for m in all_missions if m["status"] == "MISSION_COMPLETED" and m.get("elapsed_flight_time_sec", 0) > 0]
    if completed_m_list:
        avg_sec = np.mean([m["elapsed_flight_time_sec"] for m in completed_m_list])
        avg_flight_time = f"{avg_sec/60:.1f}m"

    # Display metric cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Bookings", total_missions)
    m2.metric("Active Flights", active_missions, delta=f"{active_missions} flying" if active_missions > 0 else None, delta_color="normal")
    m3.metric("Deliveries Done", completed_missions)
    m4.metric("Emergencies", emergency_missions, delta=f"{emergency_missions} logged" if emergency_missions > 0 else None, delta_color="inverse")
    m5.metric("Avg Flight Duration", avg_flight_time)
    m6.metric("Success Rate", f"{success_rate:.1f}%")

    # 1.5 METEOROLOGICAL RADAR & CORRIDOR WARNING BANNER
    has_weather_emergency = any(m["scenario_name"] == "Weather Emergency" for m in all_missions if m["status"] in ["TAKEOFF_INITIATED", "TAKEOFF_COMPLETED", "IN_FLIGHT", "APPROACHING_DESTINATION", "LANDING_INITIATED", "EMERGENCY_REROUTE"])
    
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        if has_weather_emergency:
            st.error("⛈️ **CRITICAL METEOROLOGICAL NOTICE**: Strong Convective Storm Cells & Microburst warnings active over Chennai Grid. Severe flight restriction advising emergency touchdown.")
        else:
            st.success("🌤️ **METEOROLOGICAL STABILITY**: Chennai regional corridors report safe flight condition. Moderate winds (8-15 km/h), clear sight lines, stable barometric pressure.")
    with col_w2:
        subcol1, subcol2 = st.columns(2)
        if has_weather_emergency:
            subcol1.metric("Ambient Temp", "28.5 °C", "-3.3 °C (Storm)", delta_color="inverse")
            subcol2.metric("Corridor Winds", "42.1 km/h", "⛈️ GUSTING DANGER", delta_color="inverse")
        else:
            subcol1.metric("Ambient Temp", "31.8 °C", "Stable", delta_color="normal")
            subcol2.metric("Corridor Winds", "11.5 km/h", "✅ WIND SAFE", delta_color="normal")

    st.divider()

    # 2. FLIGHT MAP AND TELEMETRY GRID
    col_map, col_tel = st.columns([1.5, 1])
    
    active_mission_options = [m for m in all_missions if m["status"] not in ["MISSION_COMPLETED", "MISSION_ABORTED", "REJECTED_BY_FEASIBILITY", "REJECTED_BY_ADMIN"]]
    selected_mission_id = None
    
    with col_tel:
        st.subheader("📊 Live Telemetry Diagnostics")
        if not active_mission_options:
            st.info("No active drone flights currently. Pre-approve a waiting request to launch telemetry streaming.")
            # Put dummy zero cards
            t1, t2 = st.columns(2)
            t1.metric("Battery Reserve", "0.0%")
            t2.metric("Internal Temperature", "0.0 °C")
            t3, t4 = st.columns(2)
            t3.metric("UAV Altitude", "0m")
            t4.metric("Autopilot Speed", "0 km/h")
        else:
            selected_mission_name = st.selectbox(
                "Select Flight Stream",
                options=[f"{m['id']} ({m['organ_type']} -> {m['dest_name']})" for m in active_mission_options],
                index=0
            )
            selected_mission_id = selected_mission_name.split(" ")[0]
            m_data = next(m for m in all_missions if m["id"] == selected_mission_id)
            drone = mission_manager.get_drone(m_data["drone_id"])
            
            if drone:
                # Gauge alerts
                bat_color = "normal" if drone.battery >= 30 else "inverse"
                temp_color = "normal" if drone.temperature <= 8.0 else "inverse"
                sig_color = "normal" if drone.signal_strength >= 40 else "inverse"
                
                t1, t2 = st.columns(2)
                t1.metric("Battery Reserve", f"{drone.battery:.1f}%", delta=f"- {drone.battery/drone.total_distance_km:.1f}% / km" if drone.total_distance_km > 0 else None, delta_color="inverse")
                t2.metric("Internal Temperature", f"{drone.temperature:.2f} °C", delta="OVERHEATED" if drone.temperature > 8.0 else "COOLING ACTIVE", delta_color="inverse" if drone.temperature > 8.0 else "off")
                
                t3, t4 = st.columns(2)
                t3.metric("UAV Altitude", f"{drone.altitude:.1f} m", delta="CRUISING" if drone.status == "IN_FLIGHT" else drone.status)
                t4.metric("Autopilot Speed", f"{drone.speed:.1f} km/h")
                
                t5, t6 = st.columns(2)
                t5.metric("Local Wind Vector", f"{drone.wind_speed:.1f} km/h", delta="STORM WARNING" if drone.wind_speed > 30.0 else "SAFE WIND", delta_color="inverse" if drone.wind_speed > 30.0 else "off")
                t6.metric("Uplink Signal Strength", f"{drone.signal_strength:.1f}%", delta="LOW CELL COVERAGE" if drone.signal_strength < 40 else "CONNECTED", delta_color="inverse" if drone.signal_strength < 40 else "off")
                
                # Real-time ML Prediction
                pred_prob = predict_realtime_success_probability(m_data, drone)
                t7, t8 = st.columns(2)
                t7.metric("ML Success Probability", f"{pred_prob * 100:.1f}%", delta="DYNAMIC EVAL" if drone.faults else "NOMINAL", delta_color="inverse" if drone.faults else "normal")
                t8.metric("Active Phase", drone.status)
                
                # Active faults display
                if drone.faults:
                    st.markdown("##### ⚠️ ACTIVE UAV FAULTS:")
                    for f in drone.faults:
                        st.error(f"🚨 {f} DETECTED")

    with col_map:
        st.subheader("🗺️ Live Chennai Flight Corridors")
        
        # Center map over Chennai
        m_map = folium.Map(location=[13.04, 80.20], zoom_start=11, control_scale=True, tiles="CartoDB dark_matter")
        
        # Add all hospitals to map
        for h in HOSPITALS:
            pad_icon = folium.Icon(color="blue" if h["emergency_landing_enabled"] else "gray", icon="plus" if h["emergency_landing_enabled"] else "minus", prefix="fa")
            folium.Marker(
                location=[h["latitude"], h["longitude"]],
                popup=f"<b>{h['name']}</b><br/>Emergency Landing Enabled: {h['emergency_landing_enabled']}",
                tooltip=h["name"],
                icon=pad_icon
            ).add_to(m_map)
            
        # If active mission selected, draw flight line, source/destination, and active drone marker
        if selected_mission_id:
            m_data = next(m for m in all_missions if m["id"] == selected_mission_id)
            drone = mission_manager.get_drone(m_data["drone_id"])
            source = get_hospital_by_id(m_data["source_id"])
            dest = get_hospital_by_id(m_data["dest_id"])
            
            if source and dest:
                # Source Marker
                folium.Marker(
                    location=[source["latitude"], source["longitude"]],
                    popup=f"SOURCE: {source['name']}",
                    tooltip="Source Pad",
                    icon=folium.Icon(color="orange", icon="upload", prefix="fa")
                ).add_to(m_map)
                
                # Destination Marker
                folium.Marker(
                    location=[dest["latitude"], dest["longitude"]],
                    popup=f"DESTINATION: {dest['name']}",
                    tooltip="Target Landing Pad",
                    icon=folium.Icon(color="green", icon="download", prefix="fa")
                ).add_to(m_map)
                
                # Flight Path corridor (dashed white/blue)
                path_coords = [[source["latitude"], source["longitude"]], [dest["latitude"], dest["longitude"]]]
                folium.PolyLine(
                    path_coords,
                    color="#4F46E5",
                    weight=4,
                    opacity=0.6,
                    dash_array="8, 8",
                    tooltip=f"Original Flight Path for {selected_mission_id}"
                ).add_to(m_map)
                
                # If rerouted, draw line from current drone position to emergency hospital
                if drone.rerouted and drone.emergency_target_id:
                    emerg_hosp = get_hospital_by_id(drone.emergency_target_id)
                    if emerg_hosp:
                        # Draw warning marker
                        folium.Marker(
                            location=[emerg_hosp["latitude"], emerg_hosp["longitude"]],
                            popup=f"EMERGENCY LANDING: {emerg_hosp['name']}",
                            tooltip="Emergency Landing Site",
                            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
                        ).add_to(m_map)
                        # Draw orange path line to emergency pad
                        emerg_coords = [[drone.latitude, drone.longitude], [emerg_hosp["latitude"], emerg_hosp["longitude"]]]
                        folium.PolyLine(
                            emerg_coords,
                            color="#DC2626",
                            weight=5,
                            opacity=0.8,
                            tooltip="Emergency Reroute Vector"
                        ).add_to(m_map)

                # Drone location marker
                drone_color = "red" if drone.status == "EMERGENCY_REROUTE" else "cadetblue"
                folium.Marker(
                    location=[drone.latitude, drone.longitude],
                    popup=f"Drone {drone.id}<br/>Status: {drone.status}<br/>Alt: {drone.altitude}m<br/>Bat: {drone.battery}%",
                    tooltip=f"UAV {drone.id} Position",
                    icon=folium.Icon(color=drone_color, icon="plane", prefix="fa")
                ).add_to(m_map)
                
                # Auto center map near the active drone
                m_map.location = [drone.latitude, drone.longitude]
                m_map.zoom_start = 12
                
        # Render map using streamlit-folium
        st_folium(m_map, height=350, use_container_width=True, key="admin_folium_map")

    st.divider()

    # 3. LIVE GRAPHS PANEL (2x2 Multi-Charts with Plotly)
    st.subheader("📈 Live Telemetry Charts (Digital Twin Window)")
    if selected_mission_id:
        m_data = next(m for m in all_missions if m["id"] == selected_mission_id)
        logs = mission_manager.telemetry_logger.get_logs(m_data["drone_id"])
        
        if len(logs) > 1:
            df_logs = pd.DataFrame(logs)
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "Battery State-of-Charge (%)", 
                    "Payload Temp (°C)", 
                    "Flight Altitude (m)", 
                    "Air Speed & Wind Vector (km/h)"
                )
            )
            
            # Battery trace
            fig.add_trace(
                go.Scatter(x=df_logs["timestamp"], y=df_logs["battery"], name="Battery %", line=dict(color="#EF4444", width=3)),
                row=1, col=1
            )
            fig.update_yaxes(range=[0, 105], row=1, col=1)
            
            # Temp trace
            fig.add_trace(
                go.Scatter(x=df_logs["timestamp"], y=df_logs["temperature"], name="Temp °C", line=dict(color="#3B82F6", width=3)),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=df_logs["timestamp"], y=[8.0]*len(df_logs), name="Max Safety limit", line=dict(color="red", dash="dash")),
                row=1, col=2
            )
            fig.update_yaxes(range=[0, 16], row=1, col=2)
            
            # Altitude trace
            fig.add_trace(
                go.Scatter(x=df_logs["timestamp"], y=df_logs["altitude"], name="Altitude m", line=dict(color="#10B981", width=3)),
                row=2, col=1
            )
            fig.update_yaxes(range=[0, 150], row=2, col=1)
            
            # Speed & Wind trace
            fig.add_trace(
                go.Scatter(x=df_logs["timestamp"], y=df_logs["speed"], name="Speed km/h", line=dict(color="#8B5CF6", width=3)),
                row=2, col=2
            )
            fig.add_trace(
                go.Scatter(x=df_logs["timestamp"], y=df_logs["wind_speed"], name="Wind km/h", line=dict(color="#F59E0B", width=2, dash="dot")),
                row=2, col=2
            )
            fig.update_yaxes(range=[0, 85], row=2, col=2)
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#09090b",
                plot_bgcolor="#121214",
                height=450,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False,
                font=dict(color="#fafafa", family="Inter")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Accumulating telemetry log samples. Graph stream starts shortly...")
    else:
        st.info("Select an active flight stream from the telemetry box to populate dynamic plots.")

    st.divider()

    # 4. DECISION ROOM & MANUAL INTERVENTION
    st.subheader("🛂 Control Center Flight Authorization Room")
    
    col_auth, col_ovr = st.columns(2)
    
    with col_auth:
        st.markdown("##### 📃 Pending Authorizations")
        pending_missions = [m for m in all_missions if m["status"] == "WAITING_FOR_APPROVAL"]
        
        if not pending_missions:
            st.write("No missions currently requesting launch clearance.")
        else:
            for pm in pending_missions:
                st.write(f"**Mission:** {pm['id']} | **Organ:** {pm['organ_type']} | **Route:** {pm['source_name']} → {pm['dest_name']}")
                st.write(f"**Feasibility Score:** `{pm['feasibility_score']}/100` | **Scenario:** *{pm['scenario_name']}*")
                
                det = pm["feasibility_details"]["details"]
                if det.get("is_ai_assessment"):
                    st.markdown(f"""
                    <div style="background-color: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); padding: 12px; border-radius: 6px; margin-bottom: 12px; margin-top: 6px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span style="font-size: 1.1em;">🌲</span>
                            <strong style="color: #3b82f6; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.05em;">ML Dispatch Recommendation</strong>
                            <span style="background-color: {'#10b98120' if det.get('ai_verdict') == 'APPROVED' else '#f59e0b20' if det.get('ai_verdict') == 'CAUTION' else '#ef444420'}; color: {'#10b981' if det.get('ai_verdict') == 'APPROVED' else '#f59e0b' if det.get('ai_verdict') == 'CAUTION' else '#ef4444'}; font-size: 0.75em; font-weight: bold; padding: 1px 6px; border-radius: 3px; border: 1px solid {'#10b98130' if det.get('ai_verdict') == 'APPROVED' else '#f59e0b30' if det.get('ai_verdict') == 'CAUTION' else '#ef444430'}; margin-left: auto;">
                                {det.get('ai_verdict')}
                            </span>
                        </div>
                        <p style="margin: 0; font-size: 0.85rem; color: #d4d4d8; font-style: italic; line-height: 1.4;">
                            "{det.get('ai_analysis')}"
                        </p>
                        <div style="margin-top: 6px; font-size: 0.8rem; color: #a1a1aa;">
                            <strong>🛡️ Flight Recommendation:</strong> {det.get('recommended_profile')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("✅ Approve Launch", key=f"app_{pm['id']}", use_container_width=True):
                    mission_manager.approve_mission(pm["id"])
                    st.success(f"Mission {pm['id']} cleared for takeoff!")
                    safe_rerun()
                if c_btn2.button("❌ Deny Launch", key=f"rej_{pm['id']}", use_container_width=True):
                    mission_manager.reject_mission(pm["id"])
                    st.error(f"Mission {pm['id']} launch rejected.")
                    safe_rerun()

    with col_ovr:
        st.markdown("##### ⚠️ Inject Physical Anomalies (Fault Overrides)")
        active_uav_missions = [m for m in all_missions if m["status"] in ["TAKEOFF_INITIATED", "TAKEOFF_COMPLETED", "IN_FLIGHT", "APPROACHING_DESTINATION", "LANDING_INITIATED"]]
        
        if not active_uav_missions:
            st.write("No active UAV flights are in-air to accept override fault signals.")
        else:
            ovr_mission = st.selectbox(
                "Select UAV Mission to Hack",
                options=[f"{m['id']} (Drone {m['drone_id']})" for m in active_uav_missions],
                key="ovr_msn_sel"
            )
            ovr_m_id = ovr_mission.split(" ")[0]
            
            st.write("Inject telemetry breakdown to test safety mitigation algorithms:")
            
            b1, b2, b3 = st.columns(3)
            if b1.button("🔋 Battery Drain", use_container_width=True):
                mission_manager.inject_fault(ovr_m_id, "Battery Failure")
                st.warning(f"Injected Battery Overheat/Drain to {ovr_m_id}!")
                safe_rerun()
            if b2.button("💨 Severe Winds", use_container_width=True):
                mission_manager.inject_fault(ovr_m_id, "Weather Failure")
                st.warning(f"Injected High Turbulence/Wind to {ovr_m_id}!")
                safe_rerun()
            if b3.button("❄️ Cooler Leak", use_container_width=True):
                mission_manager.inject_fault(ovr_m_id, "Cooling Failure")
                st.warning(f"Injected Thermal Chamber Failure to {ovr_m_id}!")
                safe_rerun()
                
            b4, b5, b6 = st.columns(3)
            if b4.button("📡 Signal Jam", use_container_width=True):
                mission_manager.inject_fault(ovr_m_id, "Communication Failure")
                st.warning(f"RF/Uplink Interrupted on {ovr_m_id}!")
                safe_rerun()
            if b5.button("🛰️ GPS Drift", use_container_width=True):
                mission_manager.inject_fault(ovr_m_id, "GPS Failure")
                st.warning(f"GPS Lock Corrupted on {ovr_m_id}!")
                safe_rerun()
            if b6.button("⚙️ Motor Burn", use_container_width=True):
                mission_manager.inject_fault(ovr_m_id, "Motor Failure")
                st.error(f"Injected Core Actuator Motor Burnout! Immediate Emergency landing initiated on {ovr_m_id}.")
                safe_rerun()

    st.divider()

    # 5. DATA TABLES (MISSIONS & DRONES)
    st.subheader("📑 Global System Ledgers")
    
    t_tab1, t_tab2 = st.tabs(["📋 Missions Ledger", "🛸 Drone Fleet Registries"])
    
    with t_tab1:
        if not all_missions:
            st.write("No flight missions recorded in the global ledger.")
        else:
            df_m = pd.DataFrame(all_missions)
            df_m_clean = df_m[["id", "organ_type", "source_name", "dest_name", "priority", "status", "created_at", "feasibility_score"]]
            st.dataframe(df_m_clean, use_container_width=True)
            
    with t_tab2:
        fleet = mission_manager.get_all_drones()
        drone_data = []
        for d in fleet:
            drone_data.append({
                "Drone ID": d.id,
                "Battery (%)": f"{d.battery:.1f}%",
                "Speed (km/h)": f"{d.speed:.1f} km/h",
                "Altitude (m)": f"{d.altitude:.1f} m",
                "Temperature (°C)": f"{d.temperature:.2f} °C",
                "Wind Vector (km/h)": f"{d.wind_speed:.1f} km/h",
                "Signal Link (%)": f"{d.signal_strength:.1f}%",
                "Cargo Load": d.payload,
                "UAV State": d.status,
                "Active Mission": d.mission_id if d.mission_id else "Idle / Static"
            })
        st.dataframe(pd.DataFrame(drone_data), use_container_width=True)

    st.divider()
    
    # Global Control Center Log Feed
    st.subheader("🔔 Real-time Command & Control Feed")
    notifs = mission_manager.notifier.get_all()
    if notifs:
        for n in notifs[:20]:
            icon = "ℹ️"
            if n["type"] == "success":
                icon = "✅"
            elif n["type"] == "warning":
                icon = "⚠️"
            elif n["type"] == "danger":
                icon = "🚨"
            st.markdown(f"**[{n['timestamp']}]** {icon} {n['message']}")
    else:
        st.write("Waiting for telemetry/dispatch system actions...")
