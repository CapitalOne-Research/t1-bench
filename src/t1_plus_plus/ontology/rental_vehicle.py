from rentals import (
    RENTAL_MAKES,
    RENTAL_MODELS,
    RENTAL_CATEGORIES,
    RENTAL_PRICE_TIERS,
    RENTAL_SEATS,
    RENTAL_FUEL_TYPES,
    RENTAL_RATINGS,
    RENTAL_LOCATIONS,
    RENTAL_AVAILABILITY_STATUS,
    RENTAL_FUEL_LEVELS,
    RENTAL_ODOMETER_RANGE,
    RENTAL_NEXT_AVAILABLE_FORMAT,
    RENTAL_FEATURES,
)

VEHICLE_SCHEMA = {
    "metadata": {
        "id": "uniqueid123",
        "make": RENTAL_MAKES,
        "model": RENTAL_MODELS,
        "year": "Integer (YYYY)",
        "category": list(RENTAL_CATEGORIES.keys()),
        "subcategory": RENTAL_CATEGORIES,
        "price_tier": RENTAL_PRICE_TIERS,
    },
    "specifications": {
        "seats": RENTAL_SEATS,
        "fuel_type": RENTAL_FUEL_TYPES,
        "rating": RENTAL_RATINGS,
    },
    "pricing": ["base_price_per_day"],
    "features": {"list": list(RENTAL_FEATURES.keys()), "values": [True, False]},
    "current_status": {
        "location": list(RENTAL_LOCATIONS.keys()),
        "availability": RENTAL_AVAILABILITY_STATUS,
        "fuel_level": RENTAL_FUEL_LEVELS,
        "odometer": RENTAL_ODOMETER_RANGE,
        "next_available": RENTAL_NEXT_AVAILABLE_FORMAT,
    },
}
