import time
import threading
import datetime
import random
from data.hospitals import get_hospital_by_id, HOSPITALS
from utils.geo import haversine_distance
from utils.notifications import NotificationManager
from simulation.drone import DroneTwin
from simulation.feasibility import check_feasibility
from simulation.emergency import trigger_drone_emergency
from simulation.telemetry import TelemetryLogger

class MissionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.missions = {}  # mission_id -> mission_dict
                cls._instance.drones = {}    # drone_id -> DroneTwin
                cls._instance.time_acceleration = 25.0  # default 25x speedup
                cls._instance.is_running = False
                cls._instance.thread = None
                cls._instance.notifier = NotificationManager()
                cls._instance.telemetry_logger = TelemetryLogger()
                
                # Pre-populate some inactive drones
                for i in range(1, 10):
                    drone_id = f"DR-{i:03d}"
                    cls._instance.drones[drone_id] = DroneTwin(drone_id)
                
                cls._instance.initialized = True
        return cls._instance

    def start_simulation(self):
        """Start the background simulation thread if not already running."""
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self.thread = threading.Thread(target=self._run_loop, daemon=True)
                self.thread.start()
                self.notifier.add("SYSTEM", "🌐 Digital Twin Simulation Thread Started.", "success")

    def stop_simulation(self):
        """Stop the background simulation thread."""
        with self._lock:
            self.is_running = False
            self.thread = None

    def _run_loop(self):
        last_time = time.time()
        while self.is_running:
            time.sleep(1.0)  # Core tick interval is 1 real-time second
            now = time.time()
            dt_real = now - last_time
            last_time = now

            # Simulated time step based on acceleration factor (e.g. 1s real = 25s sim)
            sim_dt_sec = dt_real * self.time_acceleration
            self.update_simulation_tick(sim_dt_sec)

    def create_mission(self, source_id, dest_id, organ_type, priority, scenario_name="Normal Delivery"):
        """Create a new transportation mission and run a feasibility check."""
        with self._lock:
            # Check for duplicate active requests
            for m in self.missions.values():
                if (m["source_id"] == source_id and 
                    m["dest_id"] == dest_id and 
                    m["organ_type"] == organ_type and 
                    m["priority"] == priority and 
                    m["status"] not in ["MISSION_COMPLETED", "REJECTED_BY_ADMIN", "REJECTED_BY_FEASIBILITY"]):
                    
                    source_name = m.get("source_name", "the selected source")
                    dest_name = m.get("dest_name", "the selected destination")
                    raise ValueError(f"⚠️ A dispatch request from {source_name} to {dest_name} for {organ_type} ({priority} priority) is already active (Mission: {m['id']}). Duplicate active requests are not permitted.")

            mission_id = f"MSN-{random.randint(1000, 9999)}"
            
            # 1. Perform feasibility check
            feasibility_res = check_feasibility(source_id, dest_id, organ_type, scenario_name)
            
            # Find an available idle drone
            assigned_drone_id = None
            for d_id, d in self.drones.items():
                if d.status in ["OFFLINE", "IDLE"] and d_id not in [m.get("drone_id") for m in self.missions.values() if m["status"] not in ["MISSION_COMPLETED", "MISSION_ABORTED"]]:
                    assigned_drone_id = d_id
                    break
            
            if not assigned_drone_id:
                # Force assign/reactivate one
                assigned_drone_id = f"DR-{len(self.drones)+1:03d}"
                self.drones[assigned_drone_id] = DroneTwin(assigned_drone_id)

            source = get_hospital_by_id(source_id)
            dest = get_hospital_by_id(dest_id)
            
            mission = {
                "id": mission_id,
                "organ_type": organ_type,
                "source_id": source_id,
                "source_name": source["name"] if source else "Unknown",
                "dest_id": dest_id,
                "dest_name": dest["name"] if dest else "Unknown",
                "priority": priority,
                "scenario_name": scenario_name,
                "drone_id": assigned_drone_id,
                "status": "REQUEST_CREATED",
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "feasibility_score": feasibility_res["score"],
                "feasibility_details": feasibility_res,
                "transition_timer": 0.0,  # timer to auto-progress stages
                "approved_by_admin": False,
                "completed_at": None,
                "elapsed_flight_time_sec": 0.0
            }
            
            self.missions[mission_id] = mission
            self.notifier.add(mission_id, f"📋 Transport Request Created for {organ_type} ({priority} Priority) from {mission['source_name']} to {mission['dest_name']}.", "info")
            
            # Progress status to FEASIBILITY_CHECK
            mission["status"] = "FEASIBILITY_CHECK"
            
            if feasibility_res["feasible"]:
                mission["status"] = "WAITING_FOR_APPROVAL"
                self.notifier.add(mission_id, f"✅ Route feasibility check PASSED with Score {feasibility_res['score']}/100. Waiting for Control Center approval.", "success")
            else:
                mission["status"] = "REJECTED_BY_FEASIBILITY"
                self.notifier.add(mission_id, f"❌ Route feasibility check FAILED with Score {feasibility_res['score']}/100. Reasons: {', '.join(feasibility_res['reasons'][:2])}", "danger")

            return mission_id

    def approve_mission(self, mission_id):
        """Manually approve the mission in the admin control center."""
        with self._lock:
            if mission_id in self.missions:
                m = self.missions[mission_id]
                m["approved_by_admin"] = True
                m["status"] = "MISSION_APPROVED"
                m["transition_timer"] = 0.0
                
                # Initialize drone
                drone = self.drones[m["drone_id"]]
                dist = m["feasibility_details"]["details"]["distance_km"]
                
                # Set initial battery based on scenario
                init_bat = 100.0
                from simulation.scenarios import get_scenario
                scen = get_scenario(m["scenario_name"])
                if scen:
                    init_bat = scen["initial_battery"]
                    
                drone.start_flight(mission_id, m["source_id"], m["dest_id"], m["organ_type"], dist, m["scenario_name"])
                drone.battery = init_bat
                
                # Clear legacy telemetry logs for this drone ID to start with a fresh chart
                self.telemetry_logger.clear_logs(m["drone_id"])
                
                self.notifier.add(mission_id, f"🛂 Control Center APPROVED Mission {mission_id}. Commencing pre-flight operations.", "success")
                return True
            return False

    def reject_mission(self, mission_id):
        """Reject the mission in the admin control center."""
        with self._lock:
            if mission_id in self.missions:
                self.missions[mission_id]["status"] = "REJECTED_BY_ADMIN"
                self.notifier.add(mission_id, f"🚫 Control Center REJECTED Mission {mission_id}.", "danger")
                return True
            return False

    def confirm_delivery(self, mission_id):
        """Confirm organ handover by the recipient hospital."""
        with self._lock:
            if mission_id in self.missions:
                m = self.missions[mission_id]
                m["status"] = "MISSION_COMPLETED"
                m["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Free drone
                drone = self.drones[m["drone_id"]]
                drone.status = "IDLE"
                drone.mission_id = None
                
                self.notifier.add(mission_id, f"🏆 DELIVERY CONFIRMED! Organ {m['organ_type']} successfully handed over at {m['dest_name']}. Mission complete.", "success")
                return True
            return False

    def inject_fault(self, mission_id, fault_type):
        """Force-inject a fault onto a running mission's drone."""
        with self._lock:
            if mission_id in self.missions:
                m = self.missions[mission_id]
                drone = self.drones[m["drone_id"]]
                if drone.inject_fault(fault_type):
                    self.notifier.add(mission_id, f"⚠️ FAULT INJECTED: {fault_type} forced on drone {drone.id} by Administrator.", "warning")
                    return True
            return False

    def get_mission(self, mission_id):
        with self._lock:
            return dict(self.missions.get(mission_id, {}))

    def get_all_missions(self):
        with self._lock:
            return [dict(m) for m in self.missions.values()]

    def get_drone(self, drone_id):
        with self._lock:
            return self.drones.get(drone_id)

    def get_all_drones(self):
        with self._lock:
            return list(self.drones.values())

    def update_simulation_tick(self, time_step_sec):
        """
        Main loop to tick active missions forward.
        Runs on background thread.
        """
        with self._lock:
            for m_id, m in self.missions.items():
                status = m["status"]
                
                # 1. Handle Pre-Flight State Progression (Automatic)
                if status == "MISSION_APPROVED":
                    m["transition_timer"] += time_step_sec
                    if m["transition_timer"] >= 5.0:  # 5s in sim
                        m["status"] = "ORGAN_LOADED"
                        m["transition_timer"] = 0.0
                        self.notifier.add(m_id, f"📦 Organ {m['organ_type']} loaded into thermal temperature-controlled drone bay.", "info")
                        
                elif status == "ORGAN_LOADED":
                    m["transition_timer"] += time_step_sec
                    if m["transition_timer"] >= 5.0:
                        m["status"] = "PRE_FLIGHT_CHECK"
                        m["transition_timer"] = 0.0
                        self.notifier.add(m_id, f"🛡️ Executing Pre-flight diagnostic checklists: RF, Battery cell voltage, Propeller check.", "info")
                        
                elif status == "PRE_FLIGHT_CHECK":
                    m["transition_timer"] += time_step_sec
                    if m["transition_timer"] >= 5.0:
                        m["status"] = "TAKEOFF_INITIATED"
                        m["transition_timer"] = 0.0
                        self.notifier.add(m_id, f"🚀 Autopilot Takeoff initiated at {m['source_name']}.", "success")
                        
                # 2. Handle Flights & Post-Takeoff Telemetry Ticks
                elif status in ["TAKEOFF_INITIATED", "TAKEOFF_COMPLETED", "IN_FLIGHT", "APPROACHING_DESTINATION", "LANDING_INITIATED", "EMERGENCY_REROUTE", "LANDING_AT_NEAREST_HOSPITAL"]:
                    drone = self.drones[m["drone_id"]]
                    
                    # Log active flight duration
                    m["elapsed_flight_time_sec"] += time_step_sec
                    
                    # Scenario triggers based on flight path completion
                    self.apply_scenario_triggers(m, drone)

                    # Advance drone navigation model
                    drone.update_tick(time_step_sec)
                    
                    # Mirror drone status to mission status
                    if drone.status == "TAKEOFF_INITIATED":
                        m["status"] = "TAKEOFF_INITIATED"
                    elif drone.status == "TAKEOFF_COMPLETED" and m["status"] != "TAKEOFF_COMPLETED":
                        m["status"] = "TAKEOFF_COMPLETED"
                        self.notifier.add(m_id, "🛫 Takeoff complete. Drone reached 120m cruise altitude. Cruising at 70 km/h.", "info")
                    elif drone.status == "IN_FLIGHT" and m["status"] not in ["IN_FLIGHT", "APPROACHING_DESTINATION"]:
                        m["status"] = "IN_FLIGHT"
                    elif drone.status == "EMERGENCY_REROUTE":
                        # If a fault triggered emergency but mission didn't reflect it
                        if m["status"] != "EMERGENCY_REROUTE":
                            m["status"] = "EMERGENCY_REROUTE"
                    elif drone.status == "LANDING_INITIATED" and m["status"] != "LANDING_INITIATED":
                        m["status"] = "LANDING_INITIATED"
                        self.notifier.add(m_id, f"📉 Approaching {m['dest_name']}. Descending from 120m cruise ceiling.", "info")
                    elif drone.status == "LANDED":
                        if drone.rerouted:
                            # Check if emergency landing was completed at the actual intended destination
                            if getattr(drone, "emergency_at_destination", False) or (drone.original_dest_id is not None and drone.dest_id == drone.original_dest_id):
                                if m["status"] != "ORGAN_HANDOVER":
                                    m["status"] = "ORGAN_HANDOVER"
                                    self.notifier.add(m_id, f"🛬 Emergency touchdown completed safely at the intended destination hospital {m['dest_name']}. The organ is SECURED! Initiating immediate medical handover.", "success")
                            else:
                                if m["status"] != "LANDING_AT_NEAREST_HOSPITAL":
                                    m["status"] = "LANDING_AT_NEAREST_HOSPITAL"
                                    self.notifier.add(m_id, f"🛑 Emergency touchdown completed successfully at {get_hospital_by_id(drone.dest_id)['name']}.", "warning")
                        elif m["status"] in ["LANDING_INITIATED", "IN_FLIGHT"]:
                            if m["status"] != "ORGAN_HANDOVER":
                                m["status"] = "ORGAN_HANDOVER"
                                self.notifier.add(m_id, f"🛬 Touchdown completed at {m['dest_name']}. Initiating organ unloading and medical team handover.", "success")
                    
                    # Check if drone hit automatic fault and triggers emergency
                    if len(drone.faults) > 0 and not drone.rerouted and drone.status not in ["LANDED", "EMERGENCY_LANDING"]:
                        # Select top reason
                        reason = drone.faults[0]
                        trigger_drone_emergency(drone, f"Threshold Exceeded: {reason}")
                        m["status"] = "EMERGENCY_REROUTE"
                        emerg_hosp = get_hospital_by_id(drone.dest_id)
                        if emerg_hosp:
                            m["dest_id"] = drone.dest_id
                            m["dest_name"] = emerg_hosp["name"]
                        
                    # Calculate ETA mins: distance_remaining / speed * 60 (convert to mins)
                    eta_mins = (drone.distance_remaining_km / drone.speed) * 60.0 if drone.speed > 0 else 0.0
                    
                    # Log to Telemetry logger for charting
                    self.telemetry_logger.log_telemetry(
                        drone_id=drone.id,
                        battery=drone.battery,
                        speed=drone.speed,
                        altitude=drone.altitude,
                        temperature=drone.temperature,
                        wind_speed=drone.wind_speed,
                        signal_strength=drone.signal_strength,
                        lat=drone.latitude,
                        lon=drone.longitude,
                        status=drone.status,
                        eta_mins=eta_mins
                    )
                    
                elif status == "ORGAN_HANDOVER":
                    # Wait for receiver's manual button confirmation
                    pass

    def apply_scenario_triggers(self, mission, drone):
        """Triggers faults automatically mid-flight based on scenario selected."""
        scenario_name = mission["scenario_name"]
        if scenario_name == "Normal Delivery":
            return
            
        from simulation.scenarios import get_scenario
        scen = get_scenario(scenario_name)
        if not scen:
            return
            
        # Trigger fault at trigger_fraction of flight duration
        fraction = drone.elapsed_time_sec / drone.total_duration_sec
        if fraction >= scen["trigger_fraction"] and not drone.rerouted and len(drone.faults) == 0:
            if scenario_name == "Battery Emergency":
                drone.inject_fault("Battery Failure")
            elif scenario_name == "Weather Emergency":
                drone.inject_fault("Weather Failure")
            elif scenario_name == "Cooling Failure":
                drone.inject_fault("Cooling Failure")
            elif scenario_name == "GPS Failure":
                drone.inject_fault("GPS Failure")
            elif scenario_name == "Communication Failure":
                drone.inject_fault("Communication Failure")
            
            # This triggers emergency sequence instantly
            self.notifier.add(mission["id"], f"⚠️ Scenario trigger activated: {scenario_name} initiated mid-flight.", "warning")

    def reset_system(self):
        """Wipes all simulated state."""
        with self._lock:
            self.missions.clear()
            self.notifier.clear()
            self.telemetry_logger.clear_logs()
            for d in self.drones.values():
                d.status = "IDLE"
                d.mission_id = None
                d.battery = 100.0
                d.faults = []
                d.rerouted = False
            self.notifier.add("SYSTEM", "♻️ System data reset complete.", "info")
