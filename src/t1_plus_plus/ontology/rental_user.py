from rentals import USER_LOYALTY_TIERS, USER_PAYMENT_METHODS


USER_SCHEMA = {
    "profile": {
        "user_id": "uniqueid123",
        "first_name": "ABC",
        "last_name": "DEF",
        "birthdate": "YYYY-MM-DD",
        "age": "calculate from birthdate",
        "has_drivers_license": True,
        "loyalty_tier": USER_LOYALTY_TIERS,
        "signup_date": "YYYY-MM-DD",
    },
    "payment_info": {"preferred_method": USER_PAYMENT_METHODS, "is_verified": True},
}
