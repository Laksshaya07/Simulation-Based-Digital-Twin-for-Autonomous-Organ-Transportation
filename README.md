# 🚁 Real-Time Digital Twin System for Autonomous Organ Transportation Using Medical Drones

A production-grade, state-of-the-art multi-dashboard Digital Twin and simulation command system for autonomous medical drone transport of human organs between donor and recipient hospitals in Chennai, India.

Built with Python, Streamlit, Folium, Plotly, and Scikit-Learn.

---

## 🚀 Key Features

### 1. Multi-Console Role Views
* **Donor Hospital (Sender) Dashboard**: Select donor organs (Heart, Liver, Kidney, Lung, Cornea), evaluate pre-flight ML route feasibility, inspect organ cold-chain ischemia limits, and submit dispatch requests.
* **Control Center (Admin) Command Console**: Monitor all active flights simultaneously on interactive Leaflet maps, track real-time ML mission success probability, view 2x2 live telemetry subplots (Battery, Speed, Altitude, Cargo Temp), and inject physical inflight anomalies.
* **Recipient Hospital (Receiver) Console**: Track incoming organ deliveries, monitor live countdown timers and cold-chain temperatures, and confirm safe payload handover.

### 2. Machine Learning Predictive Feasibility & Real-Time Assessment
* **Random Forest ML Model**: Trained using `scikit-learn` on synthetic historical medical drone telemetry to predict real-time mission success probability.
* **Feature Inputs**: Distance remaining, estimated battery loss, wind speed, signal strength, organ viability hours, preflight anomaly count, and weather hazard indicator.
* **Dynamic Flight Evaluation**: Provides real-time probability scores during flight, dynamically reflecting battery consumption, environmental turbulence, and fault conditions.

### 3. Multi-Flight Background Digital Twin Simulation
* Runs a thread-safe parallel simulation engine using standard Python threading. Drones navigate physical GPS coordinates, drain battery based on airspeed, payload weight, and wind resistance, adjust altitudes, and log continuous sliding-window telemetry records.

### 4. Airspace Safety & Pre-Flight Checks
* Validates route distance, organ cold-chain viability hours, wind speeds, signal coverage, emergency helipad availability, and Chennai No-Fly Zone restrictions (such as Chennai International Airport MAA airspace).

### 5. Autonomous Fault Detection & Emergency Rerouting
* Autopilot continuously monitors drone health. Upon detecting critical failures—such as battery drops (<20%), severe windstorms (>30 km/h), cooler breakdown (>8°C), or motor faults—the autopilot automatically triggers emergency protocols:
  * Identifies the nearest compatible Chennai emergency hospital landing pad.
  * Overrides flight coordinates and reroutes to the emergency destination.
  * Alerts the control center with real-time status updates.

---

## 📂 Project Structure

```text
├── app.py                       # Main Streamlit application entry point & role router
├── dashboards/
│   ├── sender.py                # Donor hospital dispatch & feasibility console
│   ├── admin.py                 # Central command center, map visualization & ML metrics
│   └── receiver.py              # Recipient hospital delivery tracking & handover
├── simulation/
│   ├── drone.py                 # Drone physics, battery loss model & digital twin state
│   ├── feasibility.py           # Scikit-Learn ML model & pre-flight checklist validator
│   ├── mission_manager.py       # Thread-safe simulation state and clock manager
│   ├── emergency.py             # Nearest emergency helipad search & rerouting engine
│   ├── scenarios.py             # Flight anomaly definitions & pre-configured scenarios
│   └── telemetry.py             # Sliding-window telemetry logger
├── data/
│   └── hospitals.py             # Chennai 25-hospital dataset with spatial coordinates
├── utils/
│   ├── geo.py                   # Haversine distance & GPS path interpolation
│   └── notifications.py         # Rolling system event logger
├── requirements.txt             # Python package dependencies
├── Dockerfile                   # Container configuration for production deployment
└── README.md                    # Project documentation
```

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.10 or higher
* `pip` package manager

### Local Execution

```bash
# 1. Clone the repository and navigate into the project directory
cd organ-drone-app

# 2. Install required Python packages
pip install -r requirements.txt

# 3. Launch the Streamlit command center
streamlit run app.py
```

The application will launch and open in your default browser at `http://localhost:8501` (or `http://localhost:3000` in containerized environments).

---

## ⚙️ How to Test & Demonstrate

1. **⚡ Quick-Seed Demonstration**:
   Open the sidebar navigation and click **"⚡ Quick-Seed Demo Flights"**. This populates the system with pre-configured mission profiles:
   * *Normal Delivery*: Flawless organ transport under nominal weather and battery consumption.
   * *Weather Emergency*: En-route encounter with high wind gusts triggering autonomous rerouting.
   * *Battery Emergency*: Simulated power cell drain forcing an emergency landing at the nearest helipad.

2. **✅ Approve Launches**:
   Switch to the **Control Center (Admin)** console. Under *Pending Authorizations*, review the pre-flight ML feasibility score and click **"✅ Approve Launch"**.

3. **📊 Monitor Live Telemetry & ML Success Probability**:
   Observe real-time drone icon movement on the interactive Folium map. Watch live metrics, 2x2 Plotly telemetry charts, and the **ML Success Probability** score dynamically update.

4. **⚠️ Inject Anomalies**:
   Under *Inject Physical Anomalies*, select an active drone and trigger a **Cooler Leak**, **Battery Failure**, or **Motor Burn** to observe immediate autopilot emergency response and path redirection.

5. **🤝 Confirm Handover**:
   Switch to the **Recipient Hospital (Receiver)** dashboard. Once a drone lands, click **"🤝 Confirm Delivery"** to complete the handover and archive the mission.

---

## ☁️ Deployment Guide

### 1. Google Cloud Run (Recommended for Enterprise Containers)

Google Cloud Run provides serverless container hosting that automatically scales.

```bash
# Set GCP Project ID
export PROJECT_ID="YOUR_GCP_PROJECT_ID"

# Build and push container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/organ-drone-app

# Deploy service to Cloud Run
gcloud run deploy organ-drone-app \
    --image gcr.io/$PROJECT_ID/organ-drone-app \
    --platform managed \
    --allow-unauthenticated \
    --region us-central1
```

### 2. Streamlit Community Cloud

1. Push code to your GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app**, select your repository, set the main file to `app.py`, and click **Deploy**.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
