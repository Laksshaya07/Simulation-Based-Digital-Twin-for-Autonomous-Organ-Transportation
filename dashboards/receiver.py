import streamlit as st
import pandas as pd
from data.hospitals import get_hospital_by_id
from utils.navigation import safe_rerun

def render_receiver_dashboard(mission_manager):
    st.markdown("<h2 style='text-align: center; color: #ffffff; font-weight: 700; letter-spacing: -0.02em;'>Recipient Hospital Intake Console</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a1a1aa; font-size: 0.95rem; margin-bottom: 20px;'>Track incoming medical organ dispatches, monitor temperature-controlled payloads, and authorize landing handovers.</p>", unsafe_allow_html=True)
    
    st.divider()

    all_missions = mission_manager.get_all_missions()
    
    # Filter incoming dispatches (excluding unapproved, rejected or already fully completed/aborted)
    incoming_missions = [
        m for m in all_missions 
        if m["status"] not in [
            "REQUEST_CREATED", 
            "FEASIBILITY_CHECK", 
            "REJECTED_BY_FEASIBILITY", 
            "REJECTED_BY_ADMIN", 
            "MISSION_COMPLETED",
            "MISSION_ABORTED"
        ]
    ]

    st.subheader("📦 Incoming Cold-Chain Organ Deliveries")

    if not incoming_missions:
        st.info("No incoming organ dispatches detected for local recipient pads. Waiting for flight authorizations.")
    else:
        for m in reversed(incoming_missions):
            status = m["status"]
            drone = mission_manager.get_drone(m["drone_id"])
            
            if not drone:
                continue

            # Visual cues
            bg_color = "#121214"
            border_color = "#3B82F6"
            
            if status == "ORGAN_HANDOVER":
                bg_color = "rgba(16, 185, 129, 0.05)"  # Dark green translucent
                border_color = "#10B981"
            elif "EMERGENCY" in status or status == "LANDING_AT_NEAREST_HOSPITAL":
                bg_color = "rgba(245, 158, 11, 0.05)"  # Dark amber translucent
                border_color = "#F59E0B"
            elif status == "MISSION_ABORTED":
                bg_color = "rgba(239, 68, 68, 0.05)"  # Dark red translucent
                border_color = "#EF4444"

            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 18px; border-radius: 8px; border-left: 6px solid {border_color}; margin-bottom: 16px; border-top: 1px solid #27272a; border-right: 1px solid #27272a; border-bottom: 1px solid #27272a;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 1.2em; color: #ffffff;">Dispatch Ref: {m['id']}</span>
                    <span style="background-color: {border_color}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">{status}</span>
                </div>
                <div style="margin-top: 10px; font-size: 0.95em; color: #a1a1aa; line-height: 1.5;">
                    📍 <strong style="color: #fafafa;">Route Profile:</strong> {m['source_name']} → <span style="text-decoration: underline; font-weight: 500; color: #ffffff;">{m['dest_name']}</span><br/>
                    🧬 <strong style="color: #fafafa;">Tissue Payload:</strong> <span style="font-weight: 600; color: #3b82f6;">{m['organ_type']}</span> ({m['priority']} Priority)<br/>
                    🛸 <strong style="color: #fafafa;">UAV Assigned:</strong> {drone.id} | <strong style="color: #fafafa;">Cruise Speed:</strong> {drone.speed:.1f} km/h<br/>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive actions and live progress nested under each active incoming item
            col_prog, col_act = st.columns([1.5, 1])
            
            with col_prog:
                st.markdown("**🔋 Critical Flight State & Cold Chain Insulation**")
                
                # Temperature warning
                temp_alert = drone.temperature > 8.0
                st.write(f"🌡️ **Cold Storage Temperature:** `{drone.temperature:.2f} °C` " + ("⚠️ **WARNING: TEMPERATURE CRITICAL**" if temp_alert else "✅ Safe Temperature"))
                st.write(f"🔋 **UAV Battery level:** `{drone.battery:.1f}%` " + ("⚠️ **LOW BATTERY**" if drone.battery < 20 else "✅ Normal Power"))
                
                # Distance and ETA
                if status in ["MISSION_ABORTED", "LANDING_AT_NEAREST_HOSPITAL"]:
                    st.error("🚫 Flight terminated early. Organ payload preserved. Diverted to secondary hospital.")
                else:
                    eta_mins = (drone.distance_remaining_km / drone.speed) * 60.0 if drone.speed > 0 else 0.0
                    st.write(f"🛰️ **Distance Remaining:** `{drone.distance_remaining_km:.2f} km` | **Est. Transit ETA:** `{eta_mins:.1f} minutes`")
                    
                    # Progress Bar of flight path completed
                    pct_complete = 0.0
                    if drone.total_distance_km > 0:
                        pct_complete = min(1.0, 1.0 - (drone.distance_remaining_km / drone.total_distance_km))
                    st.progress(pct_complete, text=f"Route flight completion: {pct_complete*100:.1f}%")

            with col_act:
                st.markdown("**🛡️ Receiver Actions**")
                
                if status == "ORGAN_HANDOVER":
                    st.success("🎉 UAV Touchdown Completed! Organ is ready for collection.")
                    if st.button(f"🤝 Confirm Delivery for {m['id']}", key=f"conf_{m['id']}", use_container_width=True):
                        mission_manager.confirm_delivery(m["id"])
                        st.success("Handover confirmed! Database logged.")
                        safe_rerun()
                elif status == "LANDING_AT_NEAREST_HOSPITAL":
                    emerg_hosp = get_hospital_by_id(drone.dest_id)
                    emerg_name = emerg_hosp["name"] if emerg_hosp else "Emergency Pad"
                    st.warning(f"🚨 Drone emergency touchdown complete at **{emerg_name}**! Ready for secure organ recovery.")
                    if st.button(f"🔒 Acknowledge Secure Landing & Handover for {m['id']}", key=f"conf_emerg_{m['id']}", use_container_width=True):
                        with mission_manager._lock:
                            m["status"] = "MISSION_ABORTED"
                            drone.status = "IDLE"
                            drone.mission_id = None
                            mission_manager.notifier.add(m["id"], f"🚫 Mission Completed via Emergency Handover at {emerg_name}. Safe landing acknowledged.", "success")
                        st.success("Emergency Handover confirmed! Mission closed.")
                        safe_rerun()
                elif status == "MISSION_ABORTED":
                    st.error("❌ Mission Aborted. Drone crashed or emergency-landed at fallback pad.")
                elif status in ["TAKEOFF_INITIATED", "TAKEOFF_COMPLETED", "IN_FLIGHT", "APPROACHING_DESTINATION", "LANDING_INITIATED"]:
                    st.info("🕒 Drone is currently in-flight. Track its coordinates on the Admin map. Get ready at the helipad.")
                elif status == "EMERGENCY_REROUTE":
                    emerg_hosp = get_hospital_by_id(drone.dest_id)
                    emerg_name = emerg_hosp["name"] if emerg_hosp else "Fallback Pad"
                    st.warning(f"🚨 Drone diverted! Emergency rerouting to **{emerg_name}** is active.")
                else:
                    st.write("Awaiting pre-flight checklist authorization.")

            st.divider()

    # Recipient Feed
    st.subheader("🔔 Recipient Dispatch Alert Log")
    notifs = mission_manager.notifier.get_all()
    if notifs:
        recipient_hosp_names = [m["dest_name"] for m in incoming_missions]
        for n in notifs[:15]:
            if n["mission_id"] != "SYSTEM" and any(name in n["message"] for name in recipient_hosp_names):
                icon = "ℹ️"
                if n["type"] == "success":
                    icon = "✅"
                elif n["type"] == "warning":
                    icon = "⚠️"
                elif n["type"] == "danger":
                    icon = "🚨"
                st.markdown(f"**[{n['timestamp']}]** {icon} {n['message']}")
    else:
        st.write("Awaiting alert feeds from dispatch channels...")
