from t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict

TYPE = "KayakRental"


KAYAK_CITIES = CITIES[:]
KAYAK_NEIGHBORHOODS = city_neighborhoods_dict.copy()

# --- Kayak Specifics ---
KAYAK_TYPES = [
    "Sit-on-Top",
    "Sit-In",
    "Tandem (2-Person)",
    "Fishing Kayak",
    "Touring/Sea Kayak",
    "Inflatable",
    "Canoe",
    "Stand-Up Paddleboard (SUP)"
]

# --- Environmental Context ---
# Useful for determining if a rental in a specific city neighborhood is on a lake or river
WATER_BODY_TYPES = ["Lake", "River", "Bay", "Canal", "Open Ocean", "Marina"]

# --- Safety & Equipment Logic ---
EQUIPMENT_OPTIONS = {
    "life_jacket_included": [True, False],
    "dry_bag_included": [True, False],
    "padding_included": [True, False],
    "guide_available": [True, False],
    "is_accessible_by_public_transit": [True, False]
}

# --- Column Customization for Dataset Generation ---
CUSTOMIZATION = {
    "city": {
        "options": KAYAK_CITIES,
        "is_single_choice": True,
        "use_all": False,
    },
    "neighborhood": {
        "options": KAYAK_NEIGHBORHOODS,
        "is_single_choice": True,
        "use_all": False,
    },
    "vessel_type": {
        "options": KAYAK_TYPES,
        "is_single_choice": True,
        "use_all": False,
    },
    "water_type": {
        "options": WATER_BODY_TYPES,
        "is_single_choice": True,
        "use_all": False,
    },
    "equipment": {
        "options": EQUIPMENT_OPTIONS,
        "use_all": True # Maps to multiple boolean columns in your CSV
    }
}