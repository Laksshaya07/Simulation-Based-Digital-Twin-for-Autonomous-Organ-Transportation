# Hospital dataset for Chennai organ transportation digital twin.

HOSPITALS = [
    {
        "id": "HOSP-01",
        "name": "Apollo Hospitals, Greams Road",
        "latitude": 13.0601,
        "longitude": 80.2514,
        "capacity": 85,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-02",
        "name": "Fortis Malar Hospital, Adyar",
        "latitude": 13.0063,
        "longitude": 80.2575,
        "capacity": 45,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-03",
        "name": "MIOT International, Manapakkam",
        "latitude": 13.0223,
        "longitude": 80.1772,
        "capacity": 70,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-04",
        "name": "Madras Medical Mission, Mogappair",
        "latitude": 13.0854,
        "longitude": 80.1818,
        "capacity": 60,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-05",
        "name": "Sri Ramachandra Medical Centre, Porur",
        "latitude": 13.0361,
        "longitude": 80.1415,
        "capacity": 90,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-06",
        "name": "Gleneagles Global Health City, Perumbakkam",
        "latitude": 12.9034,
        "longitude": 80.2173,
        "capacity": 80,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-07",
        "name": "SIMS Hospital, Vadapalani",
        "latitude": 13.0513,
        "longitude": 80.2104,
        "capacity": 55,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-08",
        "name": "Kauvery Hospital, Alwarpet",
        "latitude": 13.0336,
        "longitude": 80.2522,
        "capacity": 40,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-09",
        "name": "MGM Healthcare, Aminjikarai",
        "latitude": 13.0736,
        "longitude": 80.2291,
        "capacity": 65,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-10",
        "name": "Rajiv Gandhi Government General Hospital",
        "latitude": 13.0805,
        "longitude": 80.2754,
        "capacity": 150,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-11",
        "name": "Government Stanley Hospital, Royapuram",
        "latitude": 13.1074,
        "longitude": 80.2885,
        "capacity": 120,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-12",
        "name": "Kilpauk Medical College Hospital",
        "latitude": 13.0781,
        "longitude": 80.2442,
        "capacity": 100,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-13",
        "name": "Billroth Hospital, Shenoy Nagar",
        "latitude": 13.0789,
        "longitude": 80.2223,
        "capacity": 35,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-14",
        "name": "Dr. Rela Institute & Medical Centre",
        "latitude": 12.9463,
        "longitude": 80.1412,
        "capacity": 75,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-15",
        "name": "Hindu Mission Hospital, Tambaram",
        "latitude": 12.9248,
        "longitude": 80.1218,
        "capacity": 30,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-16",
        "name": "Chettinad Health City, Kelambakkam",
        "latitude": 12.7885,
        "longitude": 80.2224,
        "capacity": 95,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-17",
        "name": "Voluntary Health Services (VHS), Adyar",
        "latitude": 12.9984,
        "longitude": 80.2471,
        "capacity": 50,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-18",
        "name": "Vijaya Hospital, Vadapalani",
        "latitude": 13.0506,
        "longitude": 80.2081,
        "capacity": 45,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-19",
        "name": "Mehta's Multispecialty Hospital",
        "latitude": 13.0691,
        "longitude": 80.2394,
        "capacity": 40,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-20",
        "name": "Prashanth Super Speciality Hospital",
        "latitude": 12.9796,
        "longitude": 80.2201,
        "capacity": 50,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-21",
        "name": "SRM Medical College Hospital",
        "latitude": 12.8228,
        "longitude": 80.0435,
        "capacity": 110,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-22",
        "name": "Saveetha Medical College Hospital",
        "latitude": 13.0272,
        "longitude": 80.0175,
        "capacity": 105,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-23",
        "name": "Tagore Medical College & Hospital",
        "latitude": 12.8687,
        "longitude": 80.1554,
        "capacity": 60,
        "emergency_landing_enabled": True
    },
    {
        "id": "HOSP-24",
        "name": "ACS Medical College and Hospital",
        "latitude": 13.0501,
        "longitude": 80.1342,
        "capacity": 45,
        "emergency_landing_enabled": False
    },
    {
        "id": "HOSP-25",
        "name": "Sree Balaji Medical College & Hospital",
        "latitude": 12.9515,
        "longitude": 80.1408,
        "capacity": 70,
        "emergency_landing_enabled": False
    }
]

def get_hospital_by_id(hosp_id):
    for h in HOSPITALS:
        if h["id"] == hosp_id:
            return h
    return None
