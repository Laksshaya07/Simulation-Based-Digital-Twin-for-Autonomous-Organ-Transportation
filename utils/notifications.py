import datetime
import threading

class NotificationManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.notifications = []
        return cls._instance

    def add(self, mission_id, message, type="info"):
        """
        Add a notification to the global logs.
        Types: info, success, warning, danger
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self.notifications.insert(0, {
                "timestamp": timestamp,
                "mission_id": mission_id,
                "message": message,
                "type": type
            })
            # Cap at 100 recent notifications
            if len(self.notifications) > 100:
                self.notifications.pop()

    def get_all(self):
        with self._lock:
            return list(self.notifications)

    def get_for_mission(self, mission_id):
        with self._lock:
            return [n for n in self.notifications if n["mission_id"] == mission_id]

    def clear(self):
        with self._lock:
            self.notifications.clear()
