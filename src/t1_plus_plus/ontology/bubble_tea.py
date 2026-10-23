from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.dining_establishment import PRICES, RATINGS

TYPE = "Bubble Tea"

BUBBLE_TEA_RATINGS = RATINGS[:]
PRICES_RANGE = ["$", "$$"]
BUBBLE_TEA_PRICES = {k: v for k, v in PRICES.items() if k in PRICES_RANGE}
BUBBLE_TEA_CITIES = CITIES[:]
BUBBLE_TEA_NEIGHBORHOODS = city_neighborhoods_dict.copy()


# User Schema
BUBBLE_TEA_USER_FIELDS = [
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

BUBBLE_TEA_PAYMENT_METHODS = [
    "credit_cards",
    "debit_cards",
    "gift_cards",
]

BUBBLE_TEA_LOYALTY_TIERS = [
    "Basic",
    "Silver",
    "Gold",
]

BUBBLE_TEA_LOYALTY_FIELDS = ["brand", "tier"]

BUBBLE_TEA_LOYALTY_BENEFITS = {
    "Basic": {},
    "Silver": {
        "free_size_upgrade": True,
        "free_milk_alternative": True,
        "birthday_reward_value": 8,
    },
    "Gold": {
        "free_size_upgrade": True,
        "free_milk_alternative": True,
        "free_extra_topping": 1,
        "birthday_reward_value": 12,
        "early_access_seasonal": True,
    },
}


# Order Schema
BUBBLE_TEA_ORDER_FIELDS = [
    "order_id",
    "user_id",
    "cafe_id",
    "items",
    "payment_method",
    "promo_code",
    "total",
    "status",
]

BUBBLE_TEA_ORDER_STATUSES = [
    "Placed",
    "Preparing",
    "Ready_for_Pickup",
    "Completed",
    "Cancelled",
]

BUBBLE_TEA_TAX_RATE = 0.08875
BUBBLE_TEA_MAX_PROMOS_PER_ORDER = 1
BUBBLE_TEA_MILK_ALT_SURCHARGE = 0.60
BUBBLE_TEA_EXTRA_TOPPING_SURCHARGE = 0.75
BUBBLE_TEA_MAX_TOPPINGS_PER_DRINK = 3


MILK_ALTERATIVES = ["Oat", "Almond", "Soy", "Coconut", "Macadamia", "Pistachio"]

TOPPINGS = [
    "Brown Sugar Pearls",
    "Crystal Boba",
    "Popping Boba",
    "Lychee Jelly",
    "Grass Jelly",
    "Cheese Foam",
    "Egg Pudding",
    "Aloe Vera",
]

CUSTOMIZATION = {
    "sugar_levels": {
        "options": ["0%", "25%", "50%", "75%", "100%", "120%"],
        "use_all": True,
    },
    "ice_levels": {
        "options": ["No Ice", "Less Ice", "Regular Ice", "Extra Ice"],
        "use_all": True,
    },
    "tea_bases": {
        "options": [
            "Black Tea",
            "Jasmine Green",
            "Oolong",
            "Matcha",
            "Taro",
            "Thai Tea",
            "Fruit Tea",
        ],
        "use_all": False,
    },
    "toppings": {"options": TOPPINGS, "use_all": False},
    "milk_alternatives": {"options": MILK_ALTERATIVES, "use_all": False},
}


# Menu Item Schema
BUBBLE_TEA_MENU_ITEM_FIELDS = [
    "item_id",
    "cafe_id",
    "item_name",
    "description",
    "base_price",
    "is_available",
    "category",
]

REFERENCE_FIELDS = {
    "city": BUBBLE_TEA_CITIES,
    "neighborhood": BUBBLE_TEA_NEIGHBORHOODS,
    "rating": BUBBLE_TEA_RATINGS,
    "budget": BUBBLE_TEA_PRICES,
    "tea_bases": CUSTOMIZATION["tea_bases"]["options"],
    "toppings": TOPPINGS,
    "milk_alternatives": MILK_ALTERATIVES,
    "sugar_levels": CUSTOMIZATION["sugar_levels"]["options"],
    "ice_levels": CUSTOMIZATION["ice_levels"]["options"],
}
