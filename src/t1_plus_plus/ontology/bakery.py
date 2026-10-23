from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.dining_establishment import (
    COMMON_DIETARY,
    PRICES,
    RATINGS,
)

TYPE = "Bakery"

BAKERY_RATINGS = RATINGS[:]
BAKERY_PRICES = PRICES.copy()
BAKERY_CITIES = CITIES[:]
BAKERY_NEIGHBORHOODS = city_neighborhoods_dict.copy()

TYPE = "Bakery"


# User Schema
BAKERY_USER_FIELDS = [
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

BAKERY_PAYMENT_METHODS = [
    "credit_cards",
    "debit_cards",
    "gift_cards",
]

BAKERY_LOYALTY_TIERS = [
    "Basic",
    "Silver",
    "Gold",
]

BAKERY_LOYALTY_FIELDS = ["brand", "tier"]

BAKERY_LOYALTY_BENEFITS = {
    "Basic": {},
    "Silver": {
        "order_discount_pct": 0.05,
        "birthday_reward_value": 10,
    },
    "Gold": {
        "order_discount_pct": 0.10,
        "birthday_reward_value": 15,
        "priority_custom_orders": True,
    },
}


# Order Schema
BAKERY_ORDER_FIELDS = [
    "order_id",
    "user_id",
    "bakery_id",
    "items",
    "payment_method",
    "promo_code",
    "total",
    "status",
    "order_type",
]

BAKERY_ORDER_STATUSES = [
    "Placed",
    "Preparing",
    "Ready_for_Pickup",
    "Completed",
    "Cancelled",
]

BAKERY_ORDER_TYPES = [
    "Standard_Pickup",
    "Custom_Order",
]

BAKERY_TAX_RATE = 0.08875
BAKERY_MAX_PROMOS_PER_ORDER = 1
BAKERY_CUSTOM_ORDER_MIN_LEAD_HOURS = 48
BAKERY_WEDDING_CAKE_MIN_LEAD_DAYS = 14
BAKERY_CUSTOM_ORDER_DEPOSIT_THRESHOLD = 100
BAKERY_CUSTOM_ORDER_DEPOSIT_PCT = 0.50

SPECIALTIES = ["Sourdough", "Viennoiserie", "Artisan Bread", "Custom Cakes", "Pastries"]

SERVICE_OPTIONS = ["Retail", "Wholesale", "Custom Orders", "Wedding Cakes"]

DIETARY_OPTIONS = {
    **COMMON_DIETARY,
    "has_sugar_free_baked_goods": [True, False],
    "yeast_free_options": [True, False],
}

CUSTOMIZATION = {
    "bread_types": {"options": SPECIALTIES, "use_all": False},
    "service_options": {"options": SERVICE_OPTIONS, "use_all": False},
    "has_custom_cakes": {"options": [True, False], "use_all": False},
    "has_pastries": {"options": [True, False], "use_all": False},
    "dietary_options": {"options": DIETARY_OPTIONS, "use_all": False},
}


# Menu Item Schema
BAKERY_MENU_ITEM_FIELDS = [
    "item_id",
    "bakery_id",
    "item_name",
    "description",
    "base_price",
    "is_available",
    "category",
]

REFERENCE_FIELDS = {
    "city": BAKERY_CITIES,
    "neighborhood": BAKERY_NEIGHBORHOODS,
    "rating": BAKERY_RATINGS,
    "budget": BAKERY_PRICES,
    "specialties": SPECIALTIES,
    "service_options": SERVICE_OPTIONS,
}
