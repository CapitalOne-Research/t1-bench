from t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from t1_plus_plus.ontology.dining_establishment import (
    ESTABLISHMENT_NAMES,
    PRICES,
    RATINGS,
)

TYPE = "Food and Dining"

FOOD_AND_DINING_RATINGS = RATINGS[:]
FOOD_AND_DINING_PRICES = PRICES.copy()
FOOD_AND_DINING_CITIES = CITIES[:]
FOOD_AND_DINING_NEIGHBORHOODS = city_neighborhoods_dict.copy()

# ---------------------------------------------------------------------------
# Cuisines
# ---------------------------------------------------------------------------
CUISINES = [
    "American",
    "Asian Fusion",
    "Balkan",
    "Bangladeshi",
    "Barbecue",
    "Bengali",
    "Bistro",
    "Burger",
    "Burritos",
    "Caribbean",
    "Chinese",
    "Comfort Food",
    "Croatian",
    "Deli",
    "Brazilian",
    "Colombian",
    "Dutch",
    "Dumplings",
    "Estonian",
    "Ethiopian",
    "Finnish",
    "French",
    "Fried Chicken",
    "Fusion",
    "Game Day",
    "German",
    "Greek",
    "Moroccan",
    "Hawaiian",
    "Peruvian",
    "Hot Dogs",
    "Icelandic",
    "Indian",
    "Indonesian",
    "Italian",
    "Japanese",
    "Korean",
    "Latvian",
    "Lithuanian",
    "Livonian",
    "Mediterranean",
    "Mexican",
    "Norwegian",
    "Pakistani",
    "Pasta",
    "Persian",
    "Pizza",
    "Poke",
    "Poutine",
    "Romanian",
    "Salads",
    "Sandwiches",
    "Seafood",
    "Soul Food",
    "Soup",
    "Steakhouse",
    "Sushi",
    "Tacos",
    "Taiwanese",
    "Tapas",
    "Thai",
    "Turkish",
    "Vietnamese",
    "Filipino",
    "Wings",
]

# ---------------------------------------------------------------------------
# User schema
# ---------------------------------------------------------------------------
USER_FIELDS = [
    "user_id",
    "email",
    "addresses",
    "delivery_addresses",
    "payment_methods",
    "loyalty_membership",
    "reward_points_balance",
    "first_name",
    "last_name",
    "city",
    "state",
    "neighborhood",
    "signup_date",
]

PAYMENT_METHODS = [
    "credit_cards",
    "debit_cards",
    "cryptocurrencies",
    "gift_cards",
    "reward_points",
]

LOYALTY_TIERS = ["Member", "Gold", "Diamond"]

LOYALTY_BENEFITS = {
    "Member": {
        "reward_points_rate": 0.01,
    },
    "Gold": {
        "reward_points_rate": 0.05,
    },
    "Diamond": {
        "reward_points_rate": 0.10,
        "early_access_to_new_items": True,
        "free_delivery_threshold": 15.00,  # free delivery on orders over $15
    },
}

# ---------------------------------------------------------------------------
# Dietary options (shared across all sub-types)
# ---------------------------------------------------------------------------
DIETARY_OPTIONS = {
    "vegan_options": [True, False],
    "vegetarian_options": [True, False],
    "gluten_free_options": [True, False],
    "halal_options": [True, False],
    "kosher_options": [True, False],
    "low_carb_options": [True, False],
    "nut_allergy_options": [True, False],
    "dairy_allergy_options": [True, False],
    "shell_fish_allergy_options": [True, False],
    "tomato_allergy_options": [True, False],
    "nightshade_allergy_options": [True, False],
}

# ---------------------------------------------------------------------------
# Establishment features
# ---------------------------------------------------------------------------

# Dining (restaurant-style) features
DINING_FEATURES = [
    "Table Service",
    "Buffet",
    "Outdoor Seating",
    "Private Dining",
    "Full Bar",
    "Kid-Friendly",
]

# Quick-service (fast food-style) features
SERVICE_FEATURES = {
    "has_drive_thru": [True, False],
    "has_mobile_ordering_app": [True, False],
    "has_self_service_kiosks": [True, False],
    "has_curbside_pickup": [True, False],
    "has_free_wifi": [True, False],
    "has_play_area": [True, False],
    "is_open": [True, False],
    "is_open_24_7": [True, False],
}

# Promotion flags (restaurant-style)
PROMOTION_TYPES = [
    "Discount",
    "Buy One Get One Free",
    "Free Delivery",
    "Loyalty Points",
    "Happy Hour",
]

# Chain-level fields kept consistent across all locations of a fast food brand
CHAIN_CONSISTENT_FEATURES = [
    "cuisine",
    "price_level",
    "price_per_person",
]

# ---------------------------------------------------------------------------
# Menu item schema
# ---------------------------------------------------------------------------
MENU_ITEM_FIELDS = [
    "item_id",
    "restaurant_id",
    "item_name",
    "description",
    "base_price",
    "dietary_tags",   # e.g. ["vegan", "halal"]
    "allergens",      # e.g. ["dairy", "gluten"]
]

# ---------------------------------------------------------------------------
# Pickup order schema
# ---------------------------------------------------------------------------
PICKUP_ORDER_FIELDS = [
    "order_id",
    "user_id",
    "restaurant_id",
    "items",
    "payment_methods",
    "promo_code",
    "total",
    "status",
]

PICKUP_ORDER_STATUSES = [
    "Placed",
    "Ready_for_Pickup",
    "Completed",
    "Cancelled",
]

PICKUP_ITEM_FIELDS = [
    "item_id",
    "quantity",
    "line_total",
]

# ---------------------------------------------------------------------------
# Delivery order schema
# ---------------------------------------------------------------------------
DELIVERY_ORDER_FIELDS = [
    "order_id",
    "user_id",
    "restaurant_id",
    "delivery_address",
    "items",
    "special_instructions",
    "payment_methods",
    "promo_code",
    "total",
    "status",
]

DELIVERY_ORDER_STATUSES = [
    "Placed",
    "Preparing",
    "Out_for_Delivery",
    "Delivered",
    "Cancelled",
]

# ---------------------------------------------------------------------------
# Reservation schema
# ---------------------------------------------------------------------------
RESERVATION_FIELDS = [
    "reservation_id",
    "user_id",
    "restaurant_id",
    "primary_guest_name",
    "number_guests",
    "price_per_person",
    "has_private_dining",
    "reservation_charge",
    "latest_refund_date_days",
    "status",
]

RESERVATION_STATUSES = ["Active", "Cancelled"]
PRIVATE_DINING_UPGRADE_FEE = 50.00

# ---------------------------------------------------------------------------
# Pricing rules
# ---------------------------------------------------------------------------
PICKUP_TAX_RATE = 0.07
DELIVERY_TAX_RATE = 0.08
DELIVERY_FEE = 4.99

MAX_PAYMENT_METHODS_PER_ORDER = 2
MAX_PROMOS_PER_ORDER = 1

REWARD_POINTS_TO_DOLLAR = 100  # 100 points = $1.00

VALID_PROMO_CODES = {
    "SAVE10": {"type": "percent_off", "value": 0.10, "description": "10% off subtotal"},
    "FREEDELIVERY": {"type": "free_delivery", "value": DELIVERY_FEE, "description": "Free delivery"},
}

PRICING_COMPONENTS = [
    "subtotal",
    "promo_discount",
    "tax",
    "delivery_fee",
    "tip",
    "service_fee",
    "final_total",
    "reward_points_applied",
    "amount_due",
]

# ---------------------------------------------------------------------------
# CUSTOMIZATION dict (used by generate_establishment_features in data generator)
# ---------------------------------------------------------------------------
CUSTOMIZATION = {
    "cuisine": {
        "options": CUISINES,
        "use_all": False,
        "is_single_choice": True,
    },
    "features": {
        "options": SERVICE_FEATURES,
        "use_all": False,
    },
    "dietary_options": {
        "options": DIETARY_OPTIONS,
        "use_all": False,
    },
    "average_wait_time_minutes": {
        "options": [1, 30],
        "is_numeric_range": True,
    },
}

# ---------------------------------------------------------------------------
# Reference fields (for benchmarking / template generation)
# ---------------------------------------------------------------------------
REFERENCE_FIELDS = {
    "city": FOOD_AND_DINING_CITIES,
    "neighborhood": FOOD_AND_DINING_NEIGHBORHOODS,
    "rating": FOOD_AND_DINING_RATINGS,
    "budget": FOOD_AND_DINING_PRICES,
    "cuisines": CUISINES,
    "dietary_options": list(DIETARY_OPTIONS.keys()),
    "service_features": list(SERVICE_FEATURES.keys()),
    "dining_features": DINING_FEATURES,
    "loyalty_tiers": LOYALTY_TIERS,
    "pickup_order_statuses": PICKUP_ORDER_STATUSES,
    "delivery_order_statuses": DELIVERY_ORDER_STATUSES,
    "reservation_statuses": RESERVATION_STATUSES,
    "promo_codes": list(VALID_PROMO_CODES.keys()),
}

# ---------------------------------------------------------------------------
# Establishment names (reuse from dining_establishment)
# ---------------------------------------------------------------------------
FOOD_AND_DINING_NAMES = (
    ESTABLISHMENT_NAMES.get("Restaurant", [])
    + ESTABLISHMENT_NAMES.get("Fast Food", [])
)
