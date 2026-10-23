# Cruise lines with tier (1=contemporary, 2=premium, 3=luxury)
CRUISE_LINES = [
    ("Carnival Cruise Line", "CCL", 1),
    ("Royal Caribbean International", "RCI", 2),
    ("Norwegian Cruise Line", "NCL", 2),
    ("MSC Cruises", "MSC", 1),
    ("Princess Cruises", "PCS", 2),
    ("Celebrity Cruises", "CEL", 3),
    ("Holland America Line", "HAL", 2),
    ("Disney Cruise Line", "DCL", 3),
    ("Viking Ocean Cruises", "VOC", 3),
    ("Regent Seven Seas", "RSS", 3),
    ("Oceania Cruises", "OCE", 3),
    ("Cunard Line", "CUN", 3),
    ("Silversea Cruises", "SIL", 3),
]

# Ship names per cruise line code
CRUISE_SHIPS = {
    "CCL": ["Carnival Celebration", "Carnival Jubilee", "Mardi Gras", "Carnival Breeze", "Carnival Vista", "Carnival Horizon", "Carnival Panorama", "Carnival Magic"],
    "RCI": ["Icon of the Seas", "Wonder of the Seas", "Symphony of the Seas", "Harmony of the Seas", "Oasis of the Seas", "Allure of the Seas", "Odyssey of the Seas", "Spectrum of the Seas"],
    "NCL": ["Norwegian Prima", "Norwegian Viva", "Norwegian Encore", "Norwegian Bliss", "Norwegian Joy", "Norwegian Escape", "Norwegian Getaway", "Norwegian Breakaway"],
    "MSC": ["MSC World Europa", "MSC Seascape", "MSC Seashore", "MSC Virtuosa", "MSC Grandiosa", "MSC Bellissima", "MSC Meraviglia", "MSC Seaside"],
    "PCS": ["Sun Princess", "Discovery Princess", "Enchanted Princess", "Sky Princess", "Majestic Princess", "Regal Princess", "Royal Princess", "Caribbean Princess"],
    "CEL": ["Celebrity Ascent", "Celebrity Beyond", "Celebrity Apex", "Celebrity Edge", "Celebrity Reflection", "Celebrity Silhouette", "Celebrity Eclipse", "Celebrity Equinox"],
    "HAL": ["Rotterdam", "Nieuw Statendam", "Koningsdam", "Nieuw Amsterdam", "Eurodam", "Westerdam", "Oosterdam", "Zuiderdam"],
    "DCL": ["Disney Wish", "Disney Fantasy", "Disney Dream", "Disney Wonder", "Disney Magic", "Disney Treasure"],
    "VOC": ["Viking Saturn", "Viking Neptune", "Viking Mars", "Viking Venus", "Viking Orion", "Viking Jupiter", "Viking Star", "Viking Sea"],
    "RSS": ["Seven Seas Grandeur", "Seven Seas Splendor", "Seven Seas Explorer", "Seven Seas Mariner", "Seven Seas Voyager", "Seven Seas Navigator"],
    "OCE": ["Vista", "Riviera", "Marina", "Nautica", "Regatta", "Insignia", "Sirena"],
    "CUN": ["Queen Anne", "Queen Mary 2", "Queen Victoria", "Queen Elizabeth"],
    "SIL": ["Silver Nova", "Silver Dawn", "Silver Moon", "Silver Muse", "Silver Spirit", "Silver Shadow", "Silver Whisper"],
}

# Cruise destinations/routes
CRUISE_DESTINATIONS = [
    ("Caribbean - Eastern", ["Nassau", "St. Thomas", "St. Maarten", "San Juan"]),
    ("Caribbean - Western", ["Cozumel", "Grand Cayman", "Jamaica", "Belize City"]),
    ("Caribbean - Southern", ["Aruba", "Curacao", "Bonaire", "Cartagena"]),
    ("Alaska", ["Juneau", "Ketchikan", "Skagway", "Glacier Bay", "Sitka"]),
    ("Mediterranean - Western", ["Barcelona", "Rome", "Naples", "Marseille", "Palma de Mallorca"]),
    ("Mediterranean - Eastern", ["Venice", "Dubrovnik", "Santorini", "Mykonos", "Athens"]),
    ("Bahamas", ["Nassau", "CocoCay", "Half Moon Cay", "Princess Cays"]),
    ("Mexican Riviera", ["Cabo San Lucas", "Puerto Vallarta", "Mazatlan", "Ensenada"]),
    ("Hawaii", ["Honolulu", "Maui", "Kona", "Kauai", "Hilo"]),
    ("Bermuda", ["Kings Wharf", "Hamilton", "St. Georges"]),
    ("Canada & New England", ["Halifax", "Quebec City", "Bar Harbor", "Boston", "Portland"]),
    ("Panama Canal", ["Cartagena", "Colon", "Panama City", "Puerto Limon"]),
    ("Transatlantic", ["Southampton", "Lisbon", "Azores", "Madeira"]),
    ("Northern Europe", ["Copenhagen", "Stockholm", "Helsinki", "St. Petersburg", "Tallinn"]),
]

# US Departure ports with coordinates
CRUISE_DEPARTURE_PORTS = [
    {"port": "Miami", "city": "Miami", "state": "FL", "latitude": 25.7753, "longitude": -80.1800},
    {"port": "Port Canaveral", "city": "Cape Canaveral", "state": "FL", "latitude": 28.4085, "longitude": -80.6100},
    {"port": "Fort Lauderdale", "city": "Fort Lauderdale", "state": "FL", "latitude": 26.0934, "longitude": -80.1129},
    {"port": "Tampa", "city": "Tampa", "state": "FL", "latitude": 27.9428, "longitude": -82.4517},
    {"port": "New Orleans", "city": "New Orleans", "state": "LA", "latitude": 29.9391, "longitude": -90.0580},
    {"port": "Galveston", "city": "Galveston", "state": "TX", "latitude": 29.2856, "longitude": -94.8147},
    {"port": "Seattle", "city": "Seattle", "state": "WA", "latitude": 47.6205, "longitude": -122.3509},
    {"port": "San Francisco", "city": "San Francisco", "state": "CA", "latitude": 37.7956, "longitude": -122.3933},
    {"port": "Los Angeles", "city": "Los Angeles", "state": "CA", "latitude": 33.7405, "longitude": -118.2720},
    {"port": "San Diego", "city": "San Diego", "state": "CA", "latitude": 32.7132, "longitude": -117.1763},
    {"port": "New York", "city": "New York", "state": "NY", "latitude": 40.6892, "longitude": -74.0445},
    {"port": "Boston", "city": "Boston", "state": "MA", "latitude": 42.3519, "longitude": -71.0497},
    {"port": "Baltimore", "city": "Baltimore", "state": "MD", "latitude": 39.2671, "longitude": -76.5785},
    {"port": "Charleston", "city": "Charleston", "state": "SC", "latitude": 32.7876, "longitude": -79.9403},
    {"port": "Honolulu", "city": "Honolulu", "state": "HI", "latitude": 21.3025, "longitude": -157.8636},
]

# Cabin types with base price multipliers
CABIN_TYPES = [
    ("Interior", 1.0),
    ("Ocean View", 1.3),
    ("Balcony", 1.6),
    ("Mini Suite", 2.0),
    ("Suite", 2.8),
    ("Penthouse Suite", 4.0),
]

# Price ranges per tier (per person, per night)
CRUISE_PRICES = {
    1: (75, 200),    # Contemporary
    2: (150, 400),   # Premium
    3: (400, 1500),  # Luxury
}

# Ratings by tier (similar to hotel pattern)
CRUISE_RATINGS = [
    # Tier 1 (Contemporary) - indices 0-9
    3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9,
    # Tier 2 (Premium) - indices 10-19
    3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.5, 4.6,
    # Tier 3 (Luxury) - indices 20-29
    4.5, 4.6, 4.7, 4.8, 4.8, 4.9, 4.9, 5.0, 5.0, 5.0,
]

# Duration options (nights)
CRUISE_DURATIONS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 21]

# Dining options
DINING_OPTIONS = [
    "main_dining_room",
    "buffet",
    "specialty_italian",
    "specialty_steakhouse",
    "specialty_asian",
    "specialty_seafood",
    "specialty_french",
    "room_service_24hr",
    "poolside_grill",
    "pizzeria",
    "coffee_bar",
    "ice_cream_bar",
]

# Entertainment options
ENTERTAINMENT_OPTIONS = [
    "broadway_shows",
    "comedy_club",
    "casino",
    "nightclub",
    "live_music",
    "movie_theater",
    "karaoke",
    "trivia_games",
    "deck_parties",
]

# Onboard amenities
ONBOARD_AMENITIES = [
    "swimming_pools",
    "water_slides",
    "hot_tubs",
    "fitness_center",
    "spa",
    "salon",
    "kids_club",
    "teens_club",
    "adult_only_area",
    "sports_court",
    "rock_climbing_wall",
    "mini_golf",
    "jogging_track",
    "library",
    "art_gallery",
    "shopping_arcade",
    "internet_cafe",
    "medical_center",
]

# Service amenities
SERVICE_AMENITIES = [
    "butler_service",
    "concierge",
    "laundry_service",
    "dry_cleaning",
    "photographer",
    "babysitting",
    "wedding_services",
    "shore_excursion_desk",
]
