from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.dining_establishment import (
    PRICES,
    RATINGS,
)

TYPE = "Hotel"

# Zenith Brand Definitions
HOTEL_BRANDS = [
    "Aura",   # Luxury/Sophisticated
    "Apex",   # High-Tech/Family-Reliable
    "Verve",  # Wellness/Inclusive Collection
    "Nomad",  # Independent/Boutique
]

HOTEL_RATINGS = RATINGS[:]
HOTEL_PRICES_RANGE = ["$", "$$", "$$$"]
HOTEL_PRICES = {k: v for k, v in PRICES.items() if k in HOTEL_PRICES_RANGE}
HOTEL_CITIES = CITIES[:]
HOTEL_NEIGHBORHOODS = city_neighborhoods_dict.copy()

# Room and Property Features
VIEW_TYPES = [
    "Ocean View",
    "City View",
    "Garden View",
    "Standard View",
    "Poolside View",
    "Mountain View",
]

FEATURES = {
    "has_pool": [True, False],
    "has_gym": [True, False],
    "has_spa": [True, False],
    "has_digital_key": [True, False],
    "has_valet_parking": [True, False],
    "has_business_center": [True, False],
    "is_pet_friendly": [True, False],
    "has_electric_vehicle_charging": [True, False],
    "has_childcare_services": [True, False],
    "has_shuttle_service": [True, False],
}

# Membership and Loyalty Definitions
MEMBERSHIP_TIERS = [
    "Member",
    "Silver",
    "Gold",
    "Platinum",
    "Diamond",
]

# User Schema
HOTEL_USER_FIELDS = [
    "user_id",
    "email",
    "addresses",
    "payment_methods",
    "membership_level",
    "reward_points_balance",
]

HOTEL_PAYMENT_METHODS = [
    "credit_card",
    "debit_card",
    "cryptocurrencies",
    "reward_points",
]

# Property Schema
HOTEL_PROPERTY_FIELDS = [
    "hotel_id",
    "hotel_name",
    "brand",
    "address",
    "city",
    "state",
    "neighborhood",
    "latitude",
    "longitude",
    "star_rating",
] + list(FEATURES.keys())

# Room Schema
HOTEL_ROOM_FIELDS = [
    "room_id",
    "room_type",
    "view_type",
    "occupancy",
    "cash_price",   
    "points_price",  
    "resort_fees",
    "price_tier",
    "status",
]

HOTEL_ROOM_STATUSES = [
    "Available",
    "Booked",
    "Maintenance",
]

# Reservation (Order) Schema
HOTEL_RESERVATION_FIELDS = [
    "reservation_id",
    "user_id",
    "hotel_id",
    "room_id",
    "check_in_date",
    "check_out_date",
    "payment_method", # Singular, per EITHER/OR rule
    "total",
    "status",
]

HOTEL_RESERVATION_STATUSES = [
    "Booked",
    "Cancelled",
    "Completed",
]

# Policy Constants
MAX_ROOM_OCCUPANCY = 7
CANCELLATION_WINDOW_HOURS = 48
CHECK_IN_TIME = 15  # 3:00 PM

HOTEL_MAX_PAYMENT_METHODS_PER_ORDER = 1 # EITHER reward points OR standard currency
HOTEL_SUPPORTS_REWARD_POINTS_PAYMENT = True

HOTEL_PRICING_COMPONENTS = [
    "cash_price",
    "points_price",
    "resort_fees",
    "total",
]

CUSTOMIZATION = {
    "brand": {"options": HOTEL_BRANDS, "is_single_choice": True},
    "star_rating": {"options": HOTEL_RATINGS, "is_single_choice": True},
    "features": {
        "options": FEATURES,
        "use_all": False,
    },
    "view_type": {"options": VIEW_TYPES, "is_single_choice": True},
    "price_tier": {"options": HOTEL_PRICES_RANGE, "is_single_choice": True},
    "max_occupancy": {"options": [1, 7], "is_numeric_range": True},
}

# Reference Fields mapping for entity resolution 
REFERENCE_FIELDS = {
    "city": HOTEL_CITIES,
    "neighborhood": HOTEL_NEIGHBORHOODS,
    "star_rating": HOTEL_RATINGS,
    "price_tier": HOTEL_PRICES_RANGE,
    "brand": HOTEL_BRANDS,
    "view_type": VIEW_TYPES,
    "features": list(FEATURES.keys()),
    "membership_tiers": MEMBERSHIP_TIERS,
    "payment_methods": HOTEL_PAYMENT_METHODS,
    "room_statuses": HOTEL_ROOM_STATUSES,
    "reservation_statuses": HOTEL_RESERVATION_STATUSES,
}