# Scenario Definitions for Drone Organ Transportation Digital Twin

SCENARIOS = {
    "Normal Delivery": {
        "name": "Normal Delivery",
        "description": "Perfect flight profile. Stable wind (8-15 km/h), stable cooling (3.5-5.0 °C), and 100% telemetry link. Completes successfully.",
        "initial_battery": 100.0,
        "trigger_fraction": 0.40,  # Point of flight where fault or characteristic behavior shows
        "reasons": "Pre-flight checks and flight corridor cleared. Zero anomalies."
    },
    "Battery Emergency": {
        "name": "Battery Emergency",
        "description": "Simulates a power drain midway. Fast-dropping battery level below 20% triggers emergency landing at nearest hospital.",
        "initial_battery": 60.0,  # Starts slightly lower to trigger fault mid-flight
        "trigger_fraction": 0.45,
        "reasons": "Unbalance in LiPo cell resistance detected. Voltage dropping rapidly."
    },
    "Weather Emergency": {
        "name": "Weather Emergency",
        "description": "Simulates microburst or sea breeze gust. Winds rise to 40+ km/h, forcing drone to seek nearest emergency shelter.",
        "initial_battery": 100.0,
        "trigger_fraction": 0.35,
        "reasons": "Severe convective gusts exceeding 35 km/h dynamic limits."
    },
    "Cooling Failure": {
        "name": "Cooling Failure",
        "description": "Simulates a cooling container breakdown. Temperature exceeding 8°C triggers emergency landing to salvage the organ.",
        "initial_battery": 100.0,
        "trigger_fraction": 0.40,
        "reasons": "Thermoelectric cooler voltage drop. Inside container temperature rising."
    },
    "GPS Failure": {
        "name": "GPS Failure",
        "description": "Degrades navigation lock and cellular uplink, resulting in high telemetry loss and emergency return-to-base or nearest land.",
        "initial_battery": 100.0,
        "trigger_fraction": 0.30,
        "reasons": "RF jamming or multi-path GPS signal interference detected."
    },
    "Communication Failure": {
        "name": "Communication Failure",
        "description": "Complete signal blackout. Telemetry level dropping to ~5% forces the drone to execute autonomous emergency landing.",
        "initial_battery": 100.0,
        "trigger_fraction": 0.35,
        "reasons": "Loss of C2 (Command & Control) link for greater than 15 seconds."
    }
}

def get_scenario(name):
    return SCENARIOS.get(name, SCENARIOS["Normal Delivery"])
