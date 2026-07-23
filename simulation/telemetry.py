import datetime
import threading

class TelemetryLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.logs = {}  # drone_id -> list of telemetry records
        return cls._instance

    def log_telemetry(self, drone_id, battery, speed, altitude, temperature, wind_speed, signal_strength, lat, lon, status, eta_mins):
        """Log a telemetry slice for a drone."""
        timestamp = datetime.datetime.now().strftime("%M:%S")  # Min:Sec for clean chart X-axis
        record = {
            "timestamp": timestamp,
            "battery": float(battery),
            "speed": float(speed),
            "altitude": float(altitude),
            "temperature": float(temperature),
            "wind_speed": float(wind_speed),
            "signal_strength": float(signal_strength),
            "latitude": float(lat),
            "longitude": float(lon),
            "status": status,
            "eta_mins": float(eta_mins)
        }
        with self._lock:
            if drone_id not in self.logs:
                self.logs[drone_id] = []
            
            self.logs[drone_id].append(record)
            
            # Keep only the last 30 readings for plotting performance
            if len(self.logs[drone_id]) > 30:
                self.logs[drone_id].pop(0)

    def get_logs(self, drone_id):
        """Retrieve telemetry history for a specific drone."""
        with self._lock:
            return list(self.logs.get(drone_id, []))

    def clear_logs(self, drone_id=None):
        with self._lock:
            if drone_id:
                if drone_id in self.logs:
                    self.logs[drone_id] = []
            else:
                self.logs.clear()
