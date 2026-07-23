import random
from utils.geo import interpolate_coords, haversine_distance
from data.hospitals import get_hospital_by_id, HOSPITALS

class DroneTwin:
    def __init__(self, drone_id, payload="Heart", initial_battery=100.0):
        self.id = drone_id
        self.battery = initial_battery
        self.speed = 0.0          # km/h
        self.altitude = 0.0       # meters
        self.temperature = 4.0    # °C (safe range: 3.5 - 5.0)
        self.wind_speed = 10.0    # km/h
        self.signal_strength = 98.0  # %
        self.payload = payload
        self.status = "OFFLINE"   # OFFLINE, IDLE, READY, TAKEOFF, IN_FLIGHT, REROUTING, LANDING, LANDED, EMERGENCY
        
        # Geolocation
        self.latitude = 13.0601
        self.longitude = 80.2514
        
        # Flight navigation
        self.source_id = None
        self.dest_id = None
        self.current_dest_lat = 13.0601
        self.current_dest_lon = 80.2514
        self.mission_id = None
        
        # Simulation parameters
        self.elapsed_time_sec = 0.0
        self.total_duration_sec = 0.0
        self.distance_remaining_km = 0.0
        self.total_distance_km = 0.0
        
        # Emergency and failure states
        self.faults = []          # List of active faults
        self.emergency_target_id = None
        self.original_dest_id = None
        self.rerouted = False
        self.emergency_at_destination = False
        self.reroute_start_lat = None
        self.reroute_start_lon = None
        self.scenario_name = "Normal Delivery"

    def start_flight(self, mission_id, source_id, dest_id, payload, total_distance, scenario_name="Normal Delivery"):
        self.mission_id = mission_id
        self.source_id = source_id
        self.dest_id = dest_id
        self.payload = payload
        self.total_distance_km = total_distance
        self.distance_remaining_km = total_distance
        self.status = "READY"
        self.elapsed_time_sec = 0.0
        self.rerouted = False
        self.emergency_at_destination = False
        self.emergency_target_id = None
        self.original_dest_id = None
        self.reroute_start_lat = None
        self.reroute_start_lon = None
        self.faults = []
        self.scenario_name = scenario_name
        
        # Reset telemetry fields to nominal starting values
        self.wind_speed = 10.0
        self.temperature = 4.0
        self.signal_strength = 98.0
        self.speed = 0.0
        self.altitude = 0.0
        
        # Cruise duration in seconds: distance / (average speed 70km/h) * 3600
        self.total_duration_sec = (total_distance / 70.0) * 3600.0
        
        # Set initial position
        source = get_hospital_by_id(source_id)
        if source:
            self.latitude = source["latitude"]
            self.longitude = source["longitude"]
            
        dest = get_hospital_by_id(dest_id)
        if dest:
            self.current_dest_lat = dest["latitude"]
            self.current_dest_lon = dest["longitude"]

    def inject_fault(self, fault_type):
        """Inject an explicit fault into the drone."""
        if fault_type not in self.faults:
            self.faults.append(fault_type)
            return True
        return False

    def clear_faults(self):
        self.faults = []

    def update_tick(self, time_step_sec=5.0):
        """
        Advance simulation by a time step in seconds.
        Calculates location, altitude, speed, battery, wind, temp, and signal.
        """
        if self.status in ["OFFLINE", "IDLE", "MISSION_COMPLETED"]:
            self.speed = 0.0
            self.altitude = 0.0
            return

        self.elapsed_time_sec += time_step_sec
        fraction = min(1.0, self.elapsed_time_sec / self.total_duration_sec)
        
        # Resolve source and current destination coords
        if self.rerouted and self.reroute_start_lat is not None:
            src_lat, src_lon = self.reroute_start_lat, self.reroute_start_lon
        else:
            source = get_hospital_by_id(self.source_id)
            if not source:
                return
            src_lat, src_lon = source["latitude"], source["longitude"]
            
        dst_lat, dst_lon = self.current_dest_lat, self.current_dest_lon
        
        # Update Position
        self.latitude, self.longitude = interpolate_coords(src_lat, src_lon, dst_lat, dst_lon, fraction)
        self.distance_remaining_km = haversine_distance(self.latitude, self.longitude, dst_lat, dst_lon)

        # 1. STATUS & ALTITUDE SIMULATION
        if self.rerouted:
            if "Motor Failure" in self.faults:
                self.status = "EMERGENCY_LANDING"
                # Drop altitude and speed rapidly
                self.altitude = max(0.0, self.altitude - (time_step_sec * 3.5)) # drop 3.5m/s
                self.speed = max(10.0, self.speed - (time_step_sec * 1.5))
            elif fraction >= 0.95:
                # Landed stage
                self.status = "LANDED"
                self.altitude = 0.0
                self.speed = 0.0
            elif fraction >= 0.85:
                # Approaching Destination / Landing initiated
                self.status = "LANDING_INITIATED"
                # Drop altitude linearly from 120m to 10m
                rem_frac = (0.95 - fraction) / 0.10
                self.altitude = round(10.0 + (max(0.0, rem_frac) * 110.0), 1)
                self.speed = round(20.0 + (max(0.0, rem_frac) * 50.0), 1)
            else:
                self.status = "EMERGENCY_REROUTE"
                self.altitude = 120.0
                self.speed = 50.0  # Safe slow speed
        else:
            if fraction <= 0.05:
                # Takeoff stage
                self.status = "TAKEOFF_INITIATED"
                # Scale altitude from 0 to 120m
                self.altitude = round((fraction / 0.05) * 120.0, 1)
                # Speed increases during takeoff
                self.speed = round((fraction / 0.05) * 65.0, 1)
            elif fraction <= 0.10:
                self.status = "TAKEOFF_COMPLETED"
                self.altitude = 120.0
                self.speed = 70.0
            elif fraction <= 0.85:
                # Cruising stage
                if "Motor Failure" in self.faults:
                    self.status = "EMERGENCY_LANDING"
                    # Drop altitude and speed rapidly
                    self.altitude = max(0.0, self.altitude - (time_step_sec * 3.5)) # drop 3.5m/s
                    self.speed = max(10.0, self.speed - (time_step_sec * 1.5))
                else:
                    self.status = "IN_FLIGHT"
                    self.altitude = 120.0
                    # Realistically varying speed: normal 65-75 km/h
                    weather_impact = 15.0 if ("Weather Failure" in self.faults or self.wind_speed > 30.0) else 0.0
                    base_speed = random.uniform(68.0, 74.0) - weather_impact
                    self.speed = round(base_speed, 1)
            elif fraction <= 0.95:
                # Approaching Destination / Landing initiated
                self.status = "LANDING_INITIATED"
                # Drop altitude linearly from 120m to 10m
                rem_frac = (0.95 - fraction) / 0.10
                self.altitude = round(10.0 + (rem_frac * 110.0), 1)
                self.speed = round(20.0 + (rem_frac * 50.0), 1)
            else:
                # Landed stage
                self.status = "LANDED"
                self.altitude = 0.0
                self.speed = 0.0
            
        # 2. WIND SIMULATION
        if "Weather Failure" in self.faults:
            self.wind_speed = round(random.uniform(35.0, 48.0), 1)
        else:
            # Small realistic fluctuation
            self.wind_speed = round(max(4.0, self.wind_speed + random.uniform(-1.5, 1.5)), 1)
            if self.wind_speed > 25.0:  # Cap normal fluctuations
                self.wind_speed = 22.0

        # 3. TEMPERATURE (ORGAN CONTAINER) SIMULATION
        if "Cooling Failure" in self.faults:
            # Temperature rises gradually
            self.temperature = round(min(15.0, self.temperature + random.uniform(0.2, 0.5)), 2)
        else:
            # Stable inside the medical cooling chamber (3.5 - 5.0 °C)
            self.temperature = round(random.uniform(3.8, 4.4), 2)

        # 4. SIGNAL STRENGTH SIMULATION
        if "Communication Failure" in self.faults:
            self.signal_strength = round(random.uniform(2.0, 8.0), 1)
        elif "GPS Failure" in self.faults:
            self.signal_strength = round(random.uniform(10.0, 25.0), 1)
        else:
            # Fluctuating based on distance (or random small signal drops)
            self.signal_strength = round(max(70.0, min(100.0, 98.0 + random.uniform(-2.0, 1.5))), 1)

        # 5. BATTERY CONSUMPTION SIMULATION
        if self.status not in ["LANDED", "OFFLINE", "IDLE"]:
            # Battery consumption is higher in bad conditions
            payload_weight = 3.0  # kg base equivalent
            if self.payload in ["Heart", "Lung"]:
                payload_weight = 4.0
            elif self.payload == "Liver":
                payload_weight = 5.0
            elif self.payload == "Kidney":
                payload_weight = 6.0
                
            wind_factor = (self.wind_speed / 10.0) * 0.005
            speed_factor = (self.speed / 70.0) * 0.015
            payload_factor = (payload_weight / 5.0) * 0.008
            
            # Base loss per virtual second: nominal consumption + environmental factors (~2% per km at 70km/h)
            base_rate = 0.010
            
            # Fast drain if battery failure injected
            if "Battery Failure" in self.faults:
                base_rate = 0.35  # Exceedingly high drain (~20% per min)
                
            loss = (base_rate + speed_factor + payload_factor + wind_factor) * time_step_sec
            self.battery = round(max(0.0, self.battery - loss), 2)
        
        # Self-diagnose and auto-detect critical thresholds
        self.auto_detect_failures()

    def auto_detect_failures(self):
        """Automatically tag faults based on physical thresholds."""
        if self.scenario_name == "Normal Delivery":
            return
            
        # Check battery
        if self.battery < 20.0 and "Battery Failure" not in self.faults:
            if self.scenario_name == "Battery Emergency" or self.battery < 5.0:
                self.inject_fault("Battery Failure")
            
        # Check temperature
        if self.temperature > 8.0 and "Cooling Failure" not in self.faults:
            if self.scenario_name == "Cooling Failure":
                self.inject_fault("Cooling Failure")
            
        # Check wind
        if self.wind_speed > 30.0 and "Weather Failure" not in self.faults:
            if self.scenario_name == "Weather Emergency":
                self.inject_fault("Weather Failure")
            
        # Check signal
        if self.signal_strength < 30.0 and "Communication Failure" not in self.faults:
            if self.scenario_name == "Communication Failure":
                self.inject_fault("Communication Failure")

    def find_nearest_emergency_pad(self):
        """Find the closest hospital with emergency_landing_enabled."""
        nearest_hosp = None
        min_dist = 999.0
        for h in HOSPITALS:
            if h["emergency_landing_enabled"] and h["id"] != self.source_id:
                d = haversine_distance(self.latitude, self.longitude, h["latitude"], h["longitude"])
                if d < min_dist:
                    min_dist = d
                    nearest_hosp = h
        return nearest_hosp, min_dist

    def trigger_emergency_reroute(self, emergency_hospital_id):
        """Reroute drone navigation to an emergency landing hospital."""
        self.emergency_target_id = emergency_hospital_id
        self.original_dest_id = self.dest_id
        self.dest_id = emergency_hospital_id
        
        emerg_hosp = get_hospital_by_id(emergency_hospital_id)
        if emerg_hosp:
            self.current_dest_lat = emerg_hosp["latitude"]
            self.current_dest_lon = emerg_hosp["longitude"]
            
        # Reset source as the current position to interpolate from here
        self.source_id = "CURRENT_LOC"  # Temporary internal state
        self.reroute_start_lat = self.latitude
        self.reroute_start_lon = self.longitude
        # Create a mock hospital entry in HOSPITALS for current location
        # or just override interpolation logic
        self.rerouted = True
        
        # Recalculate duration based on new distance at emergency speed
        new_dist = haversine_distance(self.latitude, self.longitude, self.current_dest_lat, self.current_dest_lon)
        self.distance_remaining_km = new_dist
        self.total_distance_km = new_dist
        self.total_duration_sec = (new_dist / 50.0) * 3600.0  # 50 km/h emergency speed
        self.elapsed_time_sec = 0.0 # reset timer for the new segment

    def trigger_emergency_direct_destination(self):
        """Proceed to the current destination under emergency protocols (safe speed, direct tracking)."""
        self.emergency_target_id = self.dest_id
        self.original_dest_id = self.dest_id
        self.emergency_at_destination = True
        self.rerouted = True
        
        # Reset source as current coordinates to interpolate direct flight remaining path
        self.source_id = "CURRENT_LOC"
        self.reroute_start_lat = self.latitude
        self.reroute_start_lon = self.longitude
        
        # Recalculate remaining duration at safe speed (50 km/h)
        new_dist = haversine_distance(self.latitude, self.longitude, self.current_dest_lat, self.current_dest_lon)
        self.distance_remaining_km = new_dist
        self.total_distance_km = new_dist
        self.total_duration_sec = (new_dist / 50.0) * 3600.0
        self.elapsed_time_sec = 0.0
