from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.dining_establishment import (
    COMMON_DIETARY,
    PRICES,
    RATINGS,
)

TYPE = "Bar"

BAR_TYPES = [
    "Speakeasy",
    "Dive Bar",
    "Sports Bar",
    "Wine Bar",
    "Gastropub",
    "Rooftop Bar",
    "Cocktail Lounge",
    "Tiki Bar",
    "Brewery Taproom",
    "Whiskey/Bourbon Bar",
    "Karaoke Bar",
    "Arcade Bar",
    "Hotel Bar",
    "Piano Bar",
    "Jazz Club",
    "Irish Pub",
    "Sake Bar",
    "Champagne Bar",
    "Hookah Lounge",
    "Cigar Bar",
    "Beach Bar",
    "Biker Bar",
    "Microbrewery",
]

BAR_RATINGS = RATINGS[:]
PRICES_RANGE = ["$", "$$", "$$$"]
BAR_PRICES = {k: v for k, v in PRICES.items() if k in PRICES_RANGE}
BAR_CITIES = CITIES[:]
BAR_NEIGHBORHOODS = city_neighborhoods_dict.copy()

DIETARY_OPTIONS = {
    **COMMON_DIETARY,
    "has_halal_options": [True, False],
    "has_kosher_options": [True, False],
    "has_low_carb_options": [True, False],
    "has_nut_allergy_options": [True, False],
    "has_dairy_allergy_options": [True, False],
    "has_shell_fish_allergy_options": [True, False],
    "has_tomato_allergy_options": [True, False],
    "has_nightshade_allergy_options": [True, False],
}

DRINK_SPECIALTIES = [
    "Craft Beer",
    "Natural Wine",
    "Classic Cocktails",
    "Signature Mixology",
    "Sake",
    "Whiskey Flight",
    "Mocktails",
]

FEATURES = [
    "Happy Hour",
    "Live Music",
    "DJ",
    "Pool Tables",
    "Dance Floor",
    "Smoking Area",
    "Karaoke",
    "Sports Games",
    "Tvs",
    "Trivia",
    "Late Night Food Menu",
    "Darts",
    "Foosball",
    "Waterfront View",
    "Coat Check",
    "Valet Parking",
    "Phone Charging Stations",
    "Wheelchair Accessible",
    "Free WiFi",
]

COVER_FEES = [
    0,
    100,
    150,
    200,
    250,
    300,
    350,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
    850,
    900,
    950,
    1000,
]

# Weighting 21 as the most common, but adding 18 and 25 for variety
AGE_OPTIONS = [21, 21, 21, 21, 18, 25]

CUSTOMIZATION = {
    "bar_type": {"options": BAR_TYPES, "is_single_choice": True},
    "features": {"options": FEATURES, "use_all": False},
    "dietary_options": {"options": DIETARY_OPTIONS, "use_all": False},
    "drink_specialties": {"options": DRINK_SPECIALTIES, "use_all": False},
    "has_vip_lounge": {"options": [True, False], "use_all": False},
    "has_vip_room_upgrade": {"options": [True, False], "use_all": False},
    "cover_fee": {"options": COVER_FEES, "is_single_choice": True},
    "event_occupancy": {"options": [30, 150], "is_numeric_range": True},
    # --- NEW VIBES, AGE, AND HOURS ---
    "minimum_age": {"options": AGE_OPTIONS, "is_single_choice": True},
    "has_intimate_vibes": {"options": [True, False], "use_all": False},
    "has_fun_vibes": {"options": [True, False], "use_all": False},
    "has_social_vibes": {"options": [True, False], "use_all": False},
    "operating_hours": {
        "is_time_window": True,
        "open_options": [15, 16, 17, 18, 19, 20, 21],  # 3 PM to 9 PM
        "close_options": [23, 0, 1, 2, 3, 4],  # 11 PM to 4 AM
    },
    "dietary_options": {"options": DIETARY_OPTIONS, "use_all": False},
}

REFERENCE_FIELDS = {
    "city": BAR_CITIES,
    "neighborhood": BAR_NEIGHBORHOODS,
    "rating": BAR_RATINGS,
    "budget": BAR_PRICES,
    "cover_fee_max": COVER_FEES,
    "minimum_age": AGE_OPTIONS,
    "bar_types": BAR_TYPES,
    "drink_specialties": DRINK_SPECIALTIES,
    "features": FEATURES,
    "operating_hours": {
        "open_options": CUSTOMIZATION["operating_hours"]["open_options"],
        "close_options": CUSTOMIZATION["operating_hours"]["close_options"],
    },
}
