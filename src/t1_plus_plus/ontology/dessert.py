from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.dining_establishment import PRICES, RATINGS

TYPE = "Dessert Shop"

DESSERT_RATINGS = RATINGS[:]
PRICES_RANGE = ["$", "$$"]
DESSERT_SHOP_PRICES = {k: v for k, v in PRICES.items() if k in PRICES_RANGE}
DESSERT_CITIES = CITIES[:]
DESSERT_NEIGHBORHOODS = city_neighborhoods_dict.copy()


# User Schema
DESSERT_SHOP_USER_FIELDS = [
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

DESSERT_SHOP_PAYMENT_METHODS = [
    "credit_cards",
    "debit_cards",
    "gift_cards",
]

DESSERT_SHOP_LOYALTY_TIERS = [
    "Basic",
    "Silver",
    "Gold",
]

DESSERT_SHOP_LOYALTY_FIELDS = ["brand", "tier"]

DESSERT_SHOP_LOYALTY_BENEFITS = {
    "Basic": {},
    "Silver": {
        "order_discount_pct": 0.05,
        "birthday_reward_value": 10,
    },
    "Gold": {
        "order_discount_pct": 0.10,
        "free_topping_per_item": 1,
        "birthday_reward_value": 15,
        "priority_custom_orders": True,
    },
}


# Order Schema
DESSERT_SHOP_ORDER_FIELDS = [
    "order_id",
    "user_id",
    "shop_id",
    "items",
    "payment_method",
    "promo_code",
    "total",
    "status",
    "order_type",
]

DESSERT_SHOP_ORDER_STATUSES = [
    "Placed",
    "Preparing",
    "Ready_for_Pickup",
    "Completed",
    "Cancelled",
]

DESSERT_SHOP_ORDER_TYPES = [
    "Standard_Pickup",
    "Custom_Order",
]

DESSERT_SHOP_TAX_RATE = 0.08875
DESSERT_SHOP_MAX_PROMOS_PER_ORDER = 1
DESSERT_SHOP_TOPPING_SURCHARGE = 0.75
DESSERT_SHOP_CUSTOM_ORDER_MIN_LEAD_HOURS = 48
DESSERT_SHOP_CUSTOM_ORDER_DEPOSIT_THRESHOLD = 100
DESSERT_SHOP_CUSTOM_ORDER_DEPOSIT_PCT = 0.50


DESSERT_CATEGORIES = [
    "Ice Cream",
    "Gelato",
    "Frozen Yogurt",
    "Chocolatier",
    "Cheesecake",
    "Red Velvet",
    "Cupcakes",
    "Brownies",
    "Cookies",
    "Tarts",
    "Creperie",
    "Donuts",
    "Patisserie",
    "Candy Store",
    "Pie Shop",
    "Pudding/Custard",
    "Milkshake",
    "Frappe",
    "Soda Float",
    "Pudding",
]

TEMPERATURE_PROFILES = [
    "Frozen",
    "Chilled",
    "Warm",
    "Room Temperature",
    "Made-to-Order (Hot)",
]

# Comprehensive sweet-specific dietary needs
DESSERT_DIETARY_OPTIONS = {
    "has_dairy_free_scoops": [True, False],
    "has_sugar_free_options": [True, False],
    "has_egg_free_options": [True, False],
    "has_gelatin_free_options": [True, False],
    "has_nut_free_facility": [True, False],
    "is_vegan_friendly": [True, False],
}

# Features specific to dessert-run businesses
DESSERT_FEATURES = [
    "Sample Spoons Available",
    "Custom Toppings Bar",
    "Take-Home Pints/Quarts",
    "Custom Cake Ordering",
    "Gift Boxes",
    "Dine-in Dessert Bar",
    "Seasonal Flavors",
]

# For places like Fro-Yo or Ice Cream shops
DESSERT_TOPPINGS = [
    "Fresh Fruit",
    "Hot Fudge",
    "Caramel",
    "Whipped Cream",
    "Sprinkles",
    "Crushed Cookies",
    "Nuts",
    "Gummy Candies",
    "Mochi Bits",
    "Peanut Butter",
]

CUSTOMIZATION = {
    "dessert_categories": {"options": DESSERT_CATEGORIES, "use_all": False},
    "temperature_profiles": {"options": TEMPERATURE_PROFILES, "use_all": False},
    "toppings": {"options": DESSERT_TOPPINGS, "use_all": False},
    "dietary_options": {"options": DESSERT_DIETARY_OPTIONS, "use_all": False},
    "features": {"options": DESSERT_FEATURES, "use_all": False},
}


# Menu Item Schema
DESSERT_SHOP_MENU_ITEM_FIELDS = [
    "item_id",
    "shop_id",
    "item_name",
    "description",
    "base_price",
    "is_available",
    "category",
]

REFERENCE_FIELDS = {
    "city": DESSERT_CITIES,
    "neighborhood": DESSERT_NEIGHBORHOODS,
    "rating": DESSERT_RATINGS,
    "budget": DESSERT_SHOP_PRICES,
    "dessert_categories": DESSERT_CATEGORIES,
    "temperature_profiles": TEMPERATURE_PROFILES,
    "toppings": DESSERT_TOPPINGS,
    "features": DESSERT_FEATURES,
}
