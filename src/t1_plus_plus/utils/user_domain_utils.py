# =====================================================================
# UNIVERSAL USER UTILITIES
# =====================================================================

BASE_USER_FIELDS = [
    "user_id",
    "first_name",
    "last_name",
    "email",
    "city",
    "state",
    "neighborhood",
    "birthdate",
    "payment_wallet",
]


def get_clean_domain_user_dict(user: dict, domain_prefix: str | list[str]) -> dict:
    """
    Dynamically extracts universal base fields + domain-specific fields
    from the massive combined user dictionary.

    Args:
        user (dict): A single raw user dictionary from the combined CSV.
        domain_prefix (str | list[str]): One or more domain identifiers
            (e.g., "coffee_shop" or ["coffee_shop", "bakery"]). When multiple
            prefixes are provided, fields from each domain are merged in order,
            with later prefixes taking precedence on key collisions.

    Returns:
        dict: A clean dictionary containing only the relevant fields for the prompt.
    """
    clean_user = {k: user.get(k) for k in BASE_USER_FIELDS}

    if isinstance(domain_prefix, str):
        domain_prefix = [domain_prefix]

    # Automatically pull in domain fields (e.g., 'bakery_loyalty_membership')
    # and format them cleanly as 'loyalty_membership'
    for prefix in domain_prefix:
        prefix_with_underscore = f"{prefix}_"
        for key, value in user.items():
            if key.startswith(prefix_with_underscore):
                clean_key = key.replace(prefix_with_underscore, "", 1)
                clean_user[clean_key] = value

    return clean_user
