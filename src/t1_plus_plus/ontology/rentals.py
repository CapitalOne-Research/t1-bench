from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict
from src.t1_plus_plus.ontology.flights import FLIGHT_AIRPORTS

RENTAL_RATINGS = [round(x * 0.1, 1) for x in range(10, 51)]

RENTAL_STARS = [1, 2, 3, 4, 5]


TYPE = "Rentals"


RENTAL_LOCATIONS = {}

# --- Integrated Service Names (30 per type) ---
RENTAL_SERVICE_NAMES = {
    "Car": [
        "Carvroomo",
        "Vehida",
        "Automozo",
        "Drivetrix",
        "Vroomize",
        "Motowheelz",
        "Fleeterra",
        "LuxoDrive",
        "Speedigo",
        "AutoVita",
        "ZoomWheels",
        "Ridovex",
        "Carluxx",
        "Drivelo",
        "Vehimax",
        "Autokind",
        "Roamster",
        "GearShyft",
        "Flexidrive",
        "Carpoolz",
        "Wheelnest",
        "Drivonix",
        "Velorent",
        "AutoNomad",
        "Cruizify",
        "Rentovelo",
        "Roadnest",
        "Carventure",
        "Driveloop",
        "Autocado",
    ],
    "Bike": [
        "EcoSpin",
        "Velociped",
        "Urban Gears",
        "City Cycle",
        "Green Path",
        "Pedal Pro",
        "PedalShare",
        "CycleHaven",
        "RentWheels",
        "TrailBikes",
        "Bikenture",
        "RentoCycle",
        "Cyclective",
        "Pedalocity",
        "WheelyGo",
        "Bikeify",
        "Pedalio",
        "Riderly",
        "Cycly",
        "Trailster",
        "Vireon",
        "Piveli",
        "ZenPedalers",
        "Sprintcycle",
        "Bikehop",
        "Pedaluxe",
        "Cyclovent",
        "Wheelista",
        "Spokenly",
        "Gearloop",
    ],
    "Truck": [
        "HaulNest",
        "LoadMaster Pro",
        "TruckVenture",
        "CargoShyft",
        "MoveLine",
        "HeavyGo",
        "Truckify",
        "VanForce",
        "Swift Haulers",
        "Heavy Haul",
        "Route 66 Moving",
        "Titan Transport",
        "Cargo King",
        "Big Load Logistics",
        "RoadMaster",
        "Ironclad Carriers",
        "EagleEye Transports",
        "BlueSky Freightways",
        "Zenith Logistics",
        "MetroMover",
        "SpeedyHaul",
        "CargoZoom",
        "QuickShift",
        "RapidRoute",
        "DriveMax",
        "BlazeLine",
        "Velocity Van Co.",
        "MileMight",
        "FleetForce",
        "HaulWave",
    ],
}


VEHICLE_METADATA = {
    "Car": {
        "makes": [
            "Toyota",
            "Honda",
            "Ford",
            "Tesla",
            "BMW",
            "Hyundai",
            "Nissan",
            "Chevrolet",
            "Kia",
            "Volkswagen",
            "Audi",
            "Mercedes-Benz",
            "Subaru",
            "Mazda",
            "Lexus",
            "Jeep",
            "Dodge",
            "Volvo",
            "Porsche",
            "Chrysler",
            "Rivian",
            "Lucid",
            "Polestar",
            "Mini",
            "Jaguar",
            "Land Rover",
            "Infiniti",
            "Acura",
            "Cadillac",
            "Buick",
        ],
        "models": [
            "Camry",
            "Civic",
            "F-150",
            "Model 3",
            "3 Series",
            "Elantra",
            "Altima",
            "Silverado",
            "Sportage",
            "Golf",
            "A4",
            "C-Class",
            "Outback",
            "CX-5",
            "RX 350",
            "Wrangler",
            "Challenger",
            "XC90",
            "911 Carrera",
            "Pacifica",
            "R1S",
            "Air",
            "2",
            "Cooper",
            "F-Type",
            "Defender",
            "Q50",
            "TLX",
            "Escalade",
            "Enclave",
        ],
    },
    "Bike": {
        "makes": [
            "Specialized",
            "Trek",
            "Giant",
            "Cannondale",
            "Schwinn",
            "Bianchi",
            "Scott",
            "Santa Cruz",
            "Canyon",
            "Marin",
            "Kona",
            "Fuji",
            "Raleigh",
            "Cervelo",
            "Pinarello",
            "Orbea",
            "Diamondback",
            "GT Bicycles",
            "Norco",
            "Merida",
            "Rad Power",
            "VanMoof",
            "Lectric",
            "Gazelle",
            "Brompton",
            "Tern",
            "Surly",
            "Yeti",
            "Ibis",
            "Pivot",
        ],
        "models": [
            "Roam",
            "Domane",
            "Escape",
            "Quick",
            "Sting-Ray",
            "Infinito",
            "Addict",
            "Tallboy",
            "Endurace",
            "Fairfax",
            "Honzo",
            "Transonic",
            "Carlton",
            "Aspero",
            "Dogma",
            "Orca",
            "Release",
            "Grade",
            "Sight",
            "Scultura",
            "RadRover",
            "S3",
            "XP 3.0",
            "Ultimate",
            "C-Line",
            "GSD",
            "Disc Trucker",
            "SB160",
            "Ripmo",
            "Firebird",
        ],
    },
    "Truck": {
        "makes": [
            "Freightliner",
            "Isuzu",
            "Hino",
            "Peterbilt",
            "Kenworth",
            "Volvo Trucks",
            "Mack",
            "International",
            "Scania",
            "DAF",
            "Ram",
            "GMC",
            "Ford Commercial",
            "Mitsubishi Fuso",
            "Western Star",
            "Sterling",
            "UD Trucks",
            "Tata Motors",
            "Ashok Leyland",
            "MAN",
            "Mercedes-Benz Trucks",
            "Iveco",
            "Paccar",
            "Autocar",
            "Oshkosh",
            "Terex",
            "Caterpillar",
            "Navistar",
            "Freightbrook",
            "Titan",
        ],
        "models": [
            "M2 106",
            "N-Series",
            "338",
            "579",
            "T680",
            "VNL 860",
            "Anthem",
            "MV Series",
            "R-Series",
            "XF",
            "3500 HD",
            "Sierra 3500",
            "E-450",
            "Canter",
            "49X",
            "Acterra",
            "Quon",
            "Prima",
            "Dost",
            "TGX",
            "Arocs",
            "Eurocargo",
            "TX",
            "ACX",
            "S-Series",
            "Advance",
            "797F",
            "Lonestar",
            "C-Series",
            "Goliath",
        ],
    },
}
YEARS = list(range(2015, 2026))

for city_state, neighborhoods in city_neighborhoods_dict.items():
    city_name = city_state.split(",")[0]
    for i, nh in enumerate(neighborhoods):
        loc_id = f"NB-{city_name.replace(' ', '').upper()}-{i}"
        RENTAL_LOCATIONS[loc_id] = {
            "name": nh["neighborhood"],
            "type": "neighborhood",
            "city": city_name,
            "coordinates": (nh["latitude"], nh["longitude"]),
            "affiliated_airport": None,
        }


for ap in FLIGHT_AIRPORTS:
    loc_id = f"AIR-{ap['code']}"
    RENTAL_LOCATIONS[loc_id] = {
        "name": ap["name"],
        "type": "airport",
        "city": ap["city"],
        "coordinates": (ap["latitude"], ap["longitude"]),
        "affiliated_airport": ap["code"],
        "size": ap["size"],
    }


RENTAL_SEATS = {"car": [2, 4, 5, 7, 8], "bike": [1, 2], "truck": [2, 3]}
RENTAL_CATEGORIES = {
    "car": ["sedan", "suv", "hatchback", "coupe", "convertible"],
    "bike": ["standard", "electric", "classic"],
    "truck": ["cargo", "heavy_duty", "standard"],
}
RENTAL_PRICE_TIERS_VALUES = {
    "luxury": (150, 500),  # High-end Tesla, BMW, Luxury SUVs
    "premium": (80, 149),  # Newer models, well-equipped sedans
    "classic": (45, 79),  # Standard reliable rentals
    "budget": (15, 44),  # Economy cars, older models, or bikes
}


RENTAL_AVAILABILITY_STATUS = ["available", "not available"]

RENTAL_FUEL_LEVELS = list(range(0, 101))


RENTAL_ODOMETER_RANGE = (0, 200000)

RENTAL_NEXT_AVAILABLE_FORMAT = "ISO_8601_TIMESTAMP"


RENTAL_FEATURES = {
    "has_gps": [True, False],
    "is_automatic": [True, False],
    "has_unlimited_mileage": [True, False],
    "has_insurance_included": [True, False],
    "is_pet_friendly": [True, False],
    "has_child_seat_option": [True, False],
    "has_tow_hitch": [True, False],
    "is_wheelchair_accessible": [True, False],
}

RENTAL_FUEL_TYPES = [
    "gasoline",
    "diesel",
    "electric",
    "hybrid",
]

USER_FIRST_NAMES = [
    "James",
    "Mary",
    "Robert",
    "Patricia",
    "John",
    "Jennifer",
    "Michael",
    "Linda",
    "David",
    "Elizabeth",
    "William",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Lisa",
    "Matthew",
    "Betty",
    "Anthony",
    "Margaret",
    "Mark",
    "Sandra",
]

USER_LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
]
USER_PAYMENT_METHODS = ["credit_card", "debit_card", "crypto", "gift_card"]
USER_LOYALTY_TIERS = ["none", "silver", "gold", "platinum"]
LOYALTY_MULTIPLIERS = {
    USER_LOYALTY_TIERS[0]: 1.0,
    USER_LOYALTY_TIERS[1]: 0.95,
    USER_LOYALTY_TIERS[2]: 0.90,
    USER_LOYALTY_TIERS[3]: 0.85,
}


MIN_PICKUP_NOTICE_MINUTES = 60
MAX_LATE_DROPOFF_GRACE_PERIOD_MINUTES = 29


TAX_RATE = 0.15
SECURITY_DEPOSIT_AMOUNT = 250.0
INSURANCE_DAILY_FEE = 25.0


LATE_RETURN_HOURLY_PENALTY = 20.0
CANCELLATION_FULL_REFUND_HOURS_THRESHOLD = 24

REFERENCE_FIELDS = {
    "vehicle_type": ["Car", "Bike", "Truck"],
    "city": CITIES,
    "neighborhood": city_neighborhoods_dict,
    "airport_locations": [
        loc_id for loc_id, data in RENTAL_LOCATIONS.items() if data["type"] == "airport"
    ],
    "rating": RENTAL_RATINGS,
    "stars": RENTAL_STARS,
    "price_tier": list(RENTAL_PRICE_TIERS_VALUES.keys()),
    "makes": VEHICLE_METADATA,
    "models": VEHICLE_METADATA,
    "fuel_type": RENTAL_FUEL_TYPES,
    "features": list(RENTAL_FEATURES.keys()),
    "seats": RENTAL_SEATS,
    "categories": RENTAL_CATEGORIES,
    "service_names": RENTAL_SERVICE_NAMES,
    "available": RENTAL_AVAILABILITY_STATUS,
}
