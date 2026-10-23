from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.dining_establishment import (
    COMMON_DIETARY,
    PRICES,
    RATINGS,
)

TYPE = "Coffee Shop"

COFFEE_SHOP_RATINGS = RATINGS[:]
PRICES_RANGE = ["$", "$$"]
COFFEE_SHOP_PRICES = {k: v for k, v in PRICES.items() if k in PRICES_RANGE}
COFFEE_SHOP_CITIES = CITIES[:]
COFFEE_SHOP_NEIGHBORHOODS = city_neighborhoods_dict.copy()


TYPE = "Coffee Shop"


# User Schema
COFFEE_SHOP_USER_FIELDS = [
    "user_id",
    "email",
    "addresses",
    "payment_methods",
    "loyalty_membership",
    "first_name",
    "last_name",
    "city",
    "state",
    "neighborhood",
    "signup_date",
]

COFFEE_SHOP_PAYMENT_METHODS = [
    "credit_cards",
    "debit_cards",
    "gift_cards",
]

COFFEE_SHOP_LOYALTY_TIERS = [
    "Basic",
    "Silver",
    "Gold",
]

COFFEE_SHOP_LOYALTY_FIELDS = ["brand", "tier"]

COFFEE_SHOP_LOYALTY_BENEFITS = {
    "Basic": {},
    "Silver": {
        "free_size_upgrade": True,
        "free_milk_alternative": True,
        "birthday_reward_value": 8,
    },
    "Gold": {
        "free_size_upgrade": True,
        "free_milk_alternative": True,
        "free_flavor_additions": 2,
        "birthday_reward_value": 12,
        "early_access_seasonal": True,
    },
}


# Order Schema
COFFEE_SHOP_ORDER_FIELDS = [
    "order_id",
    "user_id",
    "cafe_id",
    "items",
    "payment_method",
    "promo_code",
    "total",
    "status",
]

COFFEE_SHOP_ORDER_STATUSES = [
    "Placed",
    "Preparing",
    "Ready_for_Pickup",
    "Completed",
    "Cancelled",
]

COFFEE_SHOP_TAX_RATE = 0.08875
COFFEE_SHOP_MAX_PROMOS_PER_ORDER = 1
COFFEE_SHOP_MILK_ALT_SURCHARGE = 0.60
COFFEE_SHOP_FLAVOR_ADDITION_SURCHARGE = 0.75


ROAST_TYPES = [
    "Light Roast",
    "Medium Roast",
    "Dark Roast",
    "Single Origin",
    "House Blend",
]

MILK_ALTERATIVES = ["Oat", "Almond", "Soy", "Coconut", "Macadamia", "Pistachio"]

FEATURES = [
    "Free Wi-Fi",
    "Laptop Friendly",
    "Quiet Zone",
    "Drive-Thru",
    "Roastery On-Site",
]

DIETARY_OPTIONS = {
    **COMMON_DIETARY,
    "sugar_free_syrups": [True, False],
    "decaf_options": [True, False],
}

CUSTOMIZATION = {
    "roast_types": {"options": ROAST_TYPES, "use_all": False},
    "milk_alternatives": {"options": MILK_ALTERATIVES, "use_all": False},
    "sugar_levels": {
        "options": ["No Sugar", "Light", "Regular", "Extra"],
        "use_all": False,
    },
    "flavor_additions": {
        "options": ["Vanilla", "Caramel", "Hazelnut", "Mocha", "Pumpkin Spice"],
        "use_all": False,
    },
}


# Menu Item Schema
COFFEE_SHOP_MENU_ITEM_FIELDS = [
    "item_id",
    "cafe_id",
    "item_name",
    "description",
    "base_price",
    "is_available",
    "category",
]

REFERENCE_FIELDS = {
    "city": COFFEE_SHOP_CITIES,
    "neighborhood": COFFEE_SHOP_NEIGHBORHOODS,
    "rating": COFFEE_SHOP_RATINGS,
    "budget": COFFEE_SHOP_PRICES,
    "roast_types": ROAST_TYPES,
    "milk_alternatives": MILK_ALTERATIVES,
    "features": FEATURES,
    "sugar_levels": CUSTOMIZATION["sugar_levels"]["options"],
    "flavor_additions": CUSTOMIZATION["flavor_additions"]["options"],
}
