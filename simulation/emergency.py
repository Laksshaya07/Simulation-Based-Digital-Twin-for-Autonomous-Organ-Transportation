from utils.notifications import NotificationManager
from data.hospitals import get_hospital_by_id

def trigger_drone_emergency(drone_twin, reason_text):
    """
    Triggers emergency state on a drone.
    Finds the closest hospital with emergency_landing_enabled,
    updates destination path, and broadcasts notifications.
    """
    notifier = NotificationManager()

    # Find the nearest emergency landing pad
    nearest_hosp, distance = drone_twin.find_nearest_emergency_pad()

    if nearest_hosp:
        target_id = nearest_hosp["id"]
        target_name = nearest_hosp["name"]

        if target_id == drone_twin.dest_id:
            # The destination hospital is the nearest emergency landing pad!
            notifier.add(
                mission_id=drone_twin.mission_id,
                message=f"🚨 EMERGENCY ALERT: Drone {drone_twin.id} (Mission {drone_twin.mission_id}) detected '{reason_text}'. Current destination {target_name} ({distance:.2f} km away) is the closest safe landing pad. Continuing direct final approach with elevated emergency landing priority.",
                type="danger"
            )
            # Update drone routing properties to proceed directly with emergency protocol
            drone_twin.trigger_emergency_direct_destination()
        else:
            # Alert operators and dashboards
            notifier.add(
                mission_id=drone_twin.mission_id,
                message=f"🚨 EMERGENCY ALERT: Drone {drone_twin.id} (Mission {drone_twin.mission_id}) detected '{reason_text}'. Autonomous rerouting engaged to {target_name} ({distance:.2f} km away).",
                type="danger"
            )

            # Update drone routing properties
            drone_twin.trigger_emergency_reroute(target_id)

        return True, nearest_hosp, distance
    else:
        # No fallback found
        notifier.add(
            mission_id=drone_twin.mission_id,
            message=f"🚨 CRITICAL ESCALATION: Drone {drone_twin.id} detected '{reason_text}', but no certified emergency landing pad is accessible. Initiating immediate hovered soft-landing sequence.",
            type="danger"
        )
        drone_twin.status = "EMERGENCY"
        return False, None, 0.0
