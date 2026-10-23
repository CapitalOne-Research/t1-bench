"""
Generic simulation runner for any domain.

Usage:
    python scripts/run_simulation.py --domain food_and_dining --conversation_id 1
    python scripts/run_simulation.py --domain bar --conversation_id 1
    python scripts/run_simulation.py --domain bar --conversation_id 3 --max_turns 15
    python scripts/run_simulation.py --domain flight --conversation_id 2 --user_model_name openai/gpt-4o --assistant_model_name openai/gpt-4o
    python scripts/run_simulation.py --domain food_and_dining --conversation_id -1  # run all IDs

Multi-domain (combined):
    python scripts/run_simulation.py --domain live_show food_and_dining \\
        --templates data/user_policies/data/live_show_food_dining/populated_live_show_food_dining_user_policy_templates.json \\
        --conversation_id 1

Supported domains: food_and_dining, bar, hotel, cafe, dessert, live_show,
                   rental (vehicle_rental), cruise, flight, attraction, desserts,
                   kayak_rental, 
"""

import argparse
import datetime
import importlib
import json
import logging
import os
import sys
import time

# Allow running from repo root or scripts/ directory
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from src.t1_plus_plus.utils.convert_tools_openai import convert_tools_to_openai_format
from src.t1_plus_plus.utils.policy_classifier import (
    classify_domains,
    load_policies_for_domains,
)
from scripts.conversation_generator import run_simulation
from scripts.eval_tool_conversations import (
    evaluate_single_conversation,
    evaluate_tool_output_exact_match,
    compute_pass,
    get_expected_tool_calls,
    get_llm_judge_metrics,
    get_actual_tool_log,
)

# Load LLM-as-judge rubric from rubric.json (two criteria: helpfulness, coherence)
_rubric_path = os.path.join(os.path.dirname(__file__), "rubric.json")
with open(_rubric_path, "r", encoding="utf-8") as _f:
    LLM_JUDGE_RUBRIC = json.load(_f)

_policies_dir = os.path.join(_repo_root, "policies")


# ---------------------------------------------------------------------------
# Logging: logs/<YYYY-MM-DD>/run_<NNN>.log
# ---------------------------------------------------------------------------


def setup_run_logging(domain_label: str, log_dir: str | None = None) -> str | None:
    """Create a log file at <log_dir>/run_<NNN>_<domain>.log.

    Returns the log file path. Tees stdout/stderr to both console and log file.
    """
    log_base = log_dir if log_dir else os.path.join(_repo_root, "logs")
    os.makedirs(log_base, exist_ok=True)

    # Determine next run number
    existing = [
        f for f in os.listdir(log_base) if f.startswith("run_") and f.endswith(".log")
    ]
    run_numbers = []
    for f in existing:
        parts = f.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            run_numbers.append(int(parts[1]))
    next_run = max(run_numbers, default=0) + 1

    log_filename = f"run_{next_run:03d}_{domain_label}.log"
    log_path = os.path.join(log_base, log_filename)

    # Tee stdout and stderr to both console and the log file
    log_file = open(log_path, "w", encoding="utf-8")

    class _Tee:
        def __init__(self, original, log_fp):
            self._original = original
            self._log_fp = log_fp

        def write(self, data):
            self._original.write(data)
            self._log_fp.write(data)
            self._log_fp.flush()

        def flush(self):
            self._original.flush()
            self._log_fp.flush()

        def fileno(self):
            return self._original.fileno()

        def isatty(self):
            return False

    sys.stdout = _Tee(sys.stdout, log_file)
    sys.stderr = _Tee(sys.stderr, log_file)

    print(f"[LOG] Writing to: {log_path}")
    return log_path


def resolve_run_dir(
    name: str | None, domain: str, model: str, dev: bool = False
) -> str:
    """Return a run folder under simulated_conversation/<model>/<domain>/.

    If `name` is None, a timestamped `run_<YYYYMMDD_HHMMSS>` subfolder is used
    so repeated runs don't overwrite each other.  Pass dev=True to write
    directly into the base directory without a timestamped subfolder.
    """
    base = os.path.join(_repo_root, "simulated_conversation", model, domain)
    os.makedirs(base, exist_ok=True)
    if dev and not name:
        return base
    if not name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"run_{timestamp}"
    run_dir = name if os.path.isabs(name) else os.path.join(base, name)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def launch_batch(
    *,
    script: str,
    domain: str | list[str],
    model: str,
    model_flag: str,
    start: int,
    end: int,
    parallel: int,
    max_turns: int,
    save: bool,
    log_name: str | None,
    run_dir_name: str | None,
    extra_flags: list[str] | None = None,
    model_dir: str | None = None,
    dev: bool = False,
) -> None:
    """Spawn a background bash loop that reruns `script` once per conversation_id
    in [start, end], optionally up to `parallel` at a time.

    `model_flag` is the CLI arg name used by `script` to pass the model (e.g.
    "--model_name" for run_simulation.py, "--claude_model" for the Claude one).
    `model` is the raw model value passed via `model_flag` to child processes.
    `model_dir` is the directory name used for output paths; defaults to `model`.
    `extra_flags` is a list of additional "--flag value" tokens forwarded to
    each child invocation.
    `domain` can be a string (single domain) or list of strings (multiple domains).
    """
    import subprocess as _subprocess  # local alias so callers don't need to import

    # For directory naming, use joined label
    if isinstance(domain, list):
        domain_label = "_".join(domain)
        domain_cli = " ".join(domain)
    else:
        domain_label = domain
        domain_cli = domain

    run_dir = resolve_run_dir(run_dir_name, domain_label, model_dir or model, dev=dev)
    save_flag = "--save" if save else ""
    extras = " ".join(extra_flags or [])

    child_cmd = (
        f"PYTHONPATH=src python {script} "
        f"--domain {domain_cli} "
        f"--conversation_id $i "
        f"--max_turns {max_turns} "
        f"{model_flag} {model} "
        f"--run_dir {run_dir} "
        f"{extras} {save_flag}"
    ).strip()

    if parallel and parallel > 1:
        bash_script = f"""
set -u
seq {start} {end} | xargs -n 1 -P {parallel} -I{{}} bash -c '
i="$1"
echo "=== [START] conversation_id=$i ==="
{child_cmd} 2>&1 | sed "s/^/[id=$i] /"
echo "=== [END]   conversation_id=$i ==="
' _ {{}}
"""
    else:
        bash_script = f"""
set -u
for i in $(seq {start} {end}); do
    echo "=== Running conversation_id=$i ==="
    {child_cmd}
    echo ""
done
"""
    log_dir = os.path.join(_repo_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = log_name or f"sim_{domain_label}_{timestamp}.log"
    log_path = (
        log_file_name
        if os.path.isabs(log_file_name)
        else os.path.join(log_dir, log_file_name)
    )
    log_fp = open(log_path, "w")
    proc = _subprocess.Popen(
        ["bash", "-c", bash_script],
        stdout=log_fp,
        stderr=_subprocess.STDOUT,
        cwd=_repo_root,
    )
    print(f"Started batch PID: {proc.pid}")
    print(f"Domain           : {domain_label}")
    print(f"Model            : {model}")
    print(f"Conversation IDs : {start}..{end}")
    print(f"Parallelism      : {parallel}")
    print(f"Log file         : {log_path}")
    print(f"Run dir          : {run_dir}")
    print(f"\nTail the log with: tail -f '{log_path}'")


# ---------------------------------------------------------------------------
# Domain registry
# Each entry maps a domain key to:
#   tools        – dict of {tool_name: module_path} for tools to import
#   policy_file  – path (relative to repo root) of the markdown policy
#   templates    – default path to the populated user-policy templates JSON
#   greeting     – opening line from the assistant
#   user_intro   – one-line description used in the user role-play prompt
#   schema_note  – properties the user is restricted to asking about (optional)
#   filter_note  – extra instruction for the assistant about filter tool usage
# ---------------------------------------------------------------------------

DOMAIN_REGISTRY = {
    "food_and_dining": {
        "tools": {
            "search_food_and_dining": "t1_plus_plus.tools.food_and_dining.search_food_and_dining",
            "filter_food_and_dining": "t1_plus_plus.tools.food_and_dining.filter_food_and_dining",
            "get_food_and_dining_menu": "t1_plus_plus.tools.food_and_dining.get_food_and_dining_menu",
            "get_food_and_dining_pickup_order": "t1_plus_plus.tools.food_and_dining.get_food_and_dining_pickup_order",
            "place_food_and_dining_pickup_order": "t1_plus_plus.tools.food_and_dining.place_food_and_dining_pickup_order",
            "cancel_food_and_dining_pickup_order": "t1_plus_plus.tools.food_and_dining.cancel_food_and_dining_pickup_order",
            "modify_food_and_dining_pickup_order": "t1_plus_plus.tools.food_and_dining.modify_food_and_dining_pickup_order",
            "get_food_and_dining_delivery_order": "t1_plus_plus.tools.food_and_dining.get_food_and_dining_delivery_order",
            "place_food_and_dining_delivery_order": "t1_plus_plus.tools.food_and_dining.place_food_and_dining_delivery_order",
            "cancel_food_and_dining_delivery_order": "t1_plus_plus.tools.food_and_dining.cancel_food_and_dining_delivery_order",
            "modify_food_and_dining_delivery_order": "t1_plus_plus.tools.food_and_dining.modify_food_and_dining_delivery_order",
            "book_food_and_dining_reservation": "t1_plus_plus.tools.food_and_dining.book_food_and_dining_reservation",
            "modify_food_and_dining_reservation": "t1_plus_plus.tools.food_and_dining.modify_food_and_dining_reservation",
            "cancel_food_and_dining_reservation": "t1_plus_plus.tools.food_and_dining.cancel_food_and_dining_reservation",
            "get_food_and_dining_reservation": "t1_plus_plus.tools.food_and_dining.get_food_and_dining_reservation",
        },
        "policy_file": "policies/food_and_dining_policy.md",
        "templates": "data/user_policies/data/food_and_dining/populated_food_and_dining_user_policy_templates.json",
        "greeting": "Hello! Welcome to the Food and Dining Assistant. How can I help you today? To get started, could you let me know which city you are in?",
        "user_intro": "looking for a place to eat, order pickup, or make a dine-in reservation",
        "assistant_name": "Food and Dining Assistant",
        "schema_note": "features explicitly defined in the food and dining schema (e.g., cuisine, vegan_options, has_drive_thru, price_level, supports_delivery)",
        "filter_tool": "filter_food_and_dining",
        "search_tool": "search_food_and_dining",
        "hallucination_examples": "McDonalds, Nobu, Eleven Madison Park, DoorDash, UberEats",
    },
    "bar": {
        "tools": {
            "search_bars": "t1_plus_plus.tools.bar.search_bars",
            "filter_bars": "t1_plus_plus.tools.bar.filter_bars",
            "book_bar_reservation": "t1_plus_plus.tools.bar.book_bar_reservation",
            "cancel_bar_reservation": "t1_plus_plus.tools.bar.cancel_bar_reservation",
            "modify_bar_reservation": "t1_plus_plus.tools.bar.modify_bar_reservation",
        },
        "policy_file": "policies/bar_policy.md",
        "templates": "data/user_policies/data/bar/populated_bar_user_policy_templates.json",
        "greeting": "Hello! Welcome to Bar Assistant. How can I help you tonight? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a bar and making a reservation",
        "assistant_name": "Bar Assistant",
        "schema_note": "features explicitly defined in the Bar Properties schema (e.g., has_pool_tables, has_live_music, has_valet_parking, price_level)",
        "filter_tool": "filter_bars",
        "search_tool": "search_bars",
        "hallucination_examples": "Double Chicken Please, Angels Share",
    },
    "hotel": {
        "tools": {
            "search_hotel": "t1_plus_plus.tools.hotel.search_hotel",
            "filter_hotel": "t1_plus_plus.tools.hotel.filter_hotel",
            "book_hotel_reservation": "t1_plus_plus.tools.hotel.book_hotel_reservation",
            "modify_hotel_reservation": "t1_plus_plus.tools.hotel.modify_hotel_reservation",
            "cancel_hotel_reservation": "t1_plus_plus.tools.hotel.cancel_hotel_reservation",
            "get_hotel_reservation": "t1_plus_plus.tools.hotel.get_hotel_reservation",
            "get_hotel_room_inventory": "t1_plus_plus.tools.hotel.get_hotel_room_inventory",
        },
        "policy_file": "policies/hotel_policy.md",
        "templates": "data/user_policies/data/hotel/populated_hotel_user_policy_templates.json",
        "greeting": "Hello! Welcome to Hotel Assistant. How can I help you with your stay? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a hotel and making a reservation",
        "assistant_name": "Hotel Assistant",
        "schema_note": "features explicitly defined in the hotel schema (e.g., has_pool, has_gym, star_rating, price_per_night)",
        "filter_tool": "filter_hotel",
        "search_tool": "search_hotel",
        "hallucination_examples": "Marriott, Hilton, Four Seasons",
    },
    "cafe": {
        "tools": {
            "search_cafes": "t1_plus_plus.tools.cafe.search_cafes",
            "filter_cafes": "t1_plus_plus.tools.cafe.filter_cafes",
            "get_cafe_menu": "t1_plus_plus.tools.cafe.get_cafe_menu",
            "place_cafe_order": "t1_plus_plus.tools.cafe.place_cafe_order",
            "cancel_cafe_order": "t1_plus_plus.tools.cafe.cancel_cafe_order",
            "get_cafe_order": "t1_plus_plus.tools.cafe.get_cafe_order",
        },
        "policy_file": "policies/cafe_policy.md",
        "templates": "data/user_policies/data/cafe/populated_cafe_user_policy_templates.json",
        "greeting": "Hello! Welcome to Cafe Assistant. How can I help you today? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a cafe and placing an order",
        "assistant_name": "Cafe Assistant",
        "schema_note": "features explicitly defined in the cafe schema (e.g., has_wifi, has_outdoor_seating, price_level)",
        "filter_tool": "filter_cafes",
        "search_tool": "search_cafes",
        "hallucination_examples": "Starbucks, Blue Bottle, Intelligentsia",
    },
    "dessert": {
        "tools": {
            "search_dessert_shops": "t1_plus_plus.tools.dessert.search_dessert_shops",
            "filter_dessert_shops": "t1_plus_plus.tools.dessert.filter_dessert_shops",
            "search_bakeries": "t1_plus_plus.tools.dessert.search_bakeries",
            "filter_bakeries": "t1_plus_plus.tools.dessert.filter_bakeries",
            "get_shop_menu": "t1_plus_plus.tools.dessert.get_shop_menu",
            "place_dessert_order": "t1_plus_plus.tools.dessert.place_dessert_order",
            "cancel_dessert_order": "t1_plus_plus.tools.dessert.cancel_dessert_order",
            "get_dessert_order": "t1_plus_plus.tools.dessert.get_dessert_order",
        },
        "policy_file": "policies/dessert_policy.md",
        "templates": "data/user_policies/data/dessert/populated_dessert_user_policy_templates.json",
        "greeting": "Hello! Welcome to Dessert Assistant. How can I help satisfy your sweet tooth? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a dessert shop and placing an order",
        "assistant_name": "Dessert Assistant",
        "schema_note": "features explicitly defined in the dessert shop schema (e.g., has_vegan_options, has_gluten_free_options, price_level)",
        "filter_tool": "filter_dessert_shops",
        "search_tool": "search_dessert_shops",
        "hallucination_examples": "Milk Bar, Magnolia Bakery, Levain",
    },
    "live_show": {
        "tools": {
            "search_live_shows": "t1_plus_plus.tools.live_show.search_live_shows",
            "filter_live_shows": "t1_plus_plus.tools.live_show.filter_live_shows",
            "check_live_show_seat_availability": "t1_plus_plus.tools.live_show.check_live_show_seat_availability",
            "book_live_show_reservation": "t1_plus_plus.tools.live_show.book_live_show_reservation",
            "cancel_live_show_reservation": "t1_plus_plus.tools.live_show.cancel_live_show_reservation",
            "modify_live_show_reservation": "t1_plus_plus.tools.live_show.modify_live_show_reservation",
            "get_live_show_details": "t1_plus_plus.tools.live_show.get_live_show_details",
        },
        "policy_file": "policies/live_show_policy.md",
        "templates": "data/user_policies/data/live_show/populated_live_show_user_policy_templates.json",
        "greeting": "Hello! Welcome to Live Show Assistant. How can I help you find an event? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a live show and booking tickets",
        "assistant_name": "Live Show Assistant",
        "schema_note": "features explicitly defined in the live show schema (e.g., performer, venue_name, show_name)",
        "filter_tool": "filter_live_shows",
        "search_tool": "search_live_shows",
        "hallucination_examples": "Coachella, Madison Square Garden events, Madonna concert",
    },
    "rental": {
        "tools": {
            "search_vehicle_rentals": "t1_plus_plus.tools.vehicle_rental.search_vehicle_rentals",
            "filter_vehicle_rentals": "t1_plus_plus.tools.vehicle_rental.filter_vehicle_rentals",
            "book_vehicle_rental_reservation": "t1_plus_plus.tools.vehicle_rental.book_vehicle_rental_reservation",
            "cancel_vehicle_rental_reservation": "t1_plus_plus.tools.vehicle_rental.cancel_vehicle_rental_reservation",
            "modify_vehicle_rental_reservation": "t1_plus_plus.tools.vehicle_rental.modify_vehicle_rental_reservation",
        },
        "policy_file": "policies/vehicle_rental_policy.md",
        "templates": "data/user_policies/data/vehicle_rental/populated_vehicle_rental_user_policy_templates.json",
        "greeting": "Hello! Welcome to Vehicle Rental Assistant. How can I help you find a vehicle? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a vehicle rental and making a reservation",
        "assistant_name": "Vehicle Rental Assistant",
        "schema_note": "features explicitly defined in the rental schema (e.g., category, has_gps, is_automatic, is_pet_friendly, has_insurance_included, has_child_seat_option, has_unlimited_mileage, price_tier, etc)",
        "filter_tool": "filter_vehicle_rentals",
        "search_tool": "search_vehicle_rentals",
        "hallucination_examples": "Hertz, Enterprise, Avis",
    },
    "cruise": {
        "tools": {
            "search_cruises": "t1_plus_plus.tools.cruise.search_cruises",
            "filter_cruises": "t1_plus_plus.tools.cruise.filter_cruises",
            "book_cruise_reservation": "t1_plus_plus.tools.cruise.book_cruise_reservation",
            "cancel_cruise_reservation": "t1_plus_plus.tools.cruise.cancel_cruise_reservation",
            "modify_cruise_reservation": "t1_plus_plus.tools.cruise.modify_cruise_reservation",
        },
        "policy_file": "policies/cruise_policy.md",
        "templates": "data/user_policies/data/cruise/populated_cruise_user_policy_templates.json",
        "greeting": "Hello! Welcome to Cruise Assistant. How can I help you plan your voyage? To get started, could you let me know your departure port or destination?",
        "user_intro": "looking for a cruise and making a reservation",
        "assistant_name": "Cruise Assistant",
        "schema_note": "features explicitly defined in the cruise schema (e.g., destination, cabin_type, price_level)",
        "filter_tool": "filter_cruises",
        "search_tool": "search_cruises",
        "hallucination_examples": "Carnival, Royal Caribbean, Norwegian",
    },
    "flight": {
        "tools": {
            "search_flight": "t1_plus_plus.tools.flight.search_flight",
            "filter_flight": "t1_plus_plus.tools.flight.filter_flight",
            "book_flight": "t1_plus_plus.tools.flight.book_flight",
            "cancel_flight": "t1_plus_plus.tools.flight.cancel_flight",
            "modify_flight_reservation": "t1_plus_plus.tools.flight.modify_flight_reservation",
        },
        "policy_file": (
            "policies/flight_policy.md"
            if os.path.exists(os.path.join(_repo_root, "policies/flight_policy.md"))
            else None
        ),
        "templates": "data/user_policies/data/flight/populated_flight_user_policy_templates.json",
        "greeting": "Hello! Welcome to Flight Assistant. How can I help you with your travel plans? To get started, could you tell me your departure city and destination?",
        "user_intro": "looking for a flight and making a booking",
        "assistant_name": "Flight Assistant",
        "schema_note": "features explicitly defined in the flight schema (e.g., cabin_class, airline, price_range)",
        "filter_tool": "filter_flight",
        "search_tool": "search_flight",
        "hallucination_examples": "Delta, American Airlines, United",
    },
    "attraction": {
        "tools": {
            "search_attractions": "t1_plus_plus.tools.attraction.search_attractions",
            "filter_attractions": "t1_plus_plus.tools.attraction.filter_attractions",
            "get_attraction_details": "t1_plus_plus.tools.attraction.get_attraction_details",
            "get_nearby_attractions": "t1_plus_plus.tools.attraction.get_nearby_attractions",
            "get_top_attractions": "t1_plus_plus.tools.attraction.get_top_attractions",
        },
        "policy_file": "policies/attraction_policy.md",
        "templates": "data/user_policies/data/attraction/populated_attraction_user_policy_templates.json",
        "greeting": "Hello! Welcome to Attractions Assistant. How can I help you discover things to do? To get started, could you let me know which city you are interested in?",
        "user_intro": "looking for attractions and activities",
        "assistant_name": "Attractions Assistant",
        "schema_note": "features explicitly defined in the attraction schema (e.g., attraction_type, price_range, has_guided_tours)",
        "filter_tool": "filter_attractions",
        "search_tool": "search_attractions",
        "hallucination_examples": "Disneyland, Times Square, Eiffel Tower",
    },
    "kayak_rental": {
        "tools": {
            "search_kayak_rentals": "t1_plus_plus.tools.kayak.search_kayak_rentals",
            "filter_kayak_rentals": "t1_plus_plus.tools.kayak.filter_kayak_rentals",
            "get_rental_details": "t1_plus_plus.tools.kayak.get_rental_details",
            "book_kayak_reservation": "t1_plus_plus.tools.kayak.book_kayak_reservation",
            "modify_kayak_reservation": "t1_plus_plus.tools.kayak.modify_kayak_reservation",
            "cancel_kayak_reservation": "t1_plus_plus.tools.kayak.cancel_kayak_reservation",
        },
        "policy_file": "policies/kayak_rental_policy.md",
        "templates": "data/user_policies/data/kayak_rental/populated_kayak_rental_user_policy_templates.json",
        "greeting": "Hello! Welcome to Kayak Rental Assistant. How can I help you find a kayak rental? To get started, could you let me know which city you are looking in?",
        "user_intro": "looking for a kayak rental and managing a reservation",
        "assistant_name": "Kayak Rental Assistant",
        "schema_note": "features explicitly defined in the kayak rental schema (e.g., vessel_type, price_per_hour, rating, duration)",
        "filter_tool": "filter_kayak_rentals",
        "search_tool": "search_kayak_rentals",
        "hallucination_examples": "REI, Outdoorsy, specific kayak shop names",
    },
}

# ---------------------------------------------------------------------------
# Domain aliases — shorthand names that expand to multiple domains with a
# default templates path.
# ---------------------------------------------------------------------------

DOMAIN_ALIASES = {
    "multi_8domain": {
        "domains": ["flight", "hotel", "rental", "food_and_dining", "attraction", "live_show", "bar", "cafe"],
        "templates": "data/user_policies/data/multi_8domain/populated_multi_8domain_user_policy_templates.json",
    },
    "multi_11domain": {
        "domains": [
            "food_and_dining", "bar", "hotel", "cafe", "dessert", "live_show",
            "rental", "cruise", "flight", "attraction", "kayak_rental",
        ],
        "templates": "data/user_policies/data/multi_11domain/populated_multi_11domain_user_policy_templates.json",
    },
    "attraction_cafe": {
        "domains": ["attraction", "cafe"],
        "templates": "data/user_policies/data/attraction_cafe/populated_attraction_cafe_user_policy_templates.json",
    },
    "attraction_dessert": {
        "domains": ["attraction", "dessert"],
        "templates": "data/user_policies/data/attraction_dessert/populated_attraction_dessert_user_policy_templates.json",
    },
    "attraction_food_dining_cafe": {
        "domains": ["attraction", "food_and_dining", "cafe"],
        "templates": "data/user_policies/data/attraction_food_dining_cafe/populated_attraction_food_dining_cafe_user_policy_templates.json",
    },
    "flight_hotel_attraction_rental": {
        "domains": ["flight", "hotel", "attraction", "rental"],
        "templates": "data/user_policies/data/flight_hotel_attraction_rental/populated_flight_hotel_attraction_rental_user_policy_templates.json",
    },
    "flight_hotel_bar": {
        "domains": ["flight", "hotel", "bar"],
        "templates": "data/user_policies/data/flight_hotel_bar/populated_flight_hotel_bar_user_policy_templates.json",
    },
    "food_and_dining_hotel": {
        "domains": ["food_and_dining", "hotel"],
        "templates": "data/user_policies/data/food_and_dining_hotel/populated_food_and_dining_hotel_user_policy_templates.json",
    },
    "hotel_attraction_rental": {
        "domains": ["hotel", "attraction", "rental"],
        "templates": "data/user_policies/data/hotel_attraction_rental/populated_hotel_attraction_rental_user_policy_templates.json",
    },
    "hotel_rental": {
        "domains": ["hotel", "rental"],
        "templates": "data/user_policies/data/hotel_rental/populated_hotel_rental_user_policy_templates.json",
    },
    "hotel_rental_food_bar": {
        "domains": ["hotel", "rental", "food_and_dining", "bar"],
        "templates": "data/user_policies/data/hotel_rental_food_bar/populated_hotel_rental_food_bar_user_policy_templates.json",
    },
    "live_show_food_dining": {
        "domains": ["live_show", "food_and_dining"],
        "templates": "data/user_policies/data/live_show_food_dining/populated_live_show_food_dining_user_policy_templates.json",
    },
    "vehicle_rental_attraction": {
        "domains": ["rental", "attraction"],
        "templates": "data/user_policies/data/vehicle_rental_attraction/populated_vehicle_rental_attraction_user_policy_templates.json",
    },
    "vehicle_rental_food_and_dining_hotel": {
        "domains": ["rental", "food_and_dining", "hotel"],
        "templates": "data/user_policies/data/vehicle_rental_food_and_dining_hotel/populated_vehicle_rental_food_and_dining_hotel_user_policy_templates.json",
    },
}

# Allow "vehicle_rental" as an alias for "rental" in the registry
DOMAIN_REGISTRY["vehicle_rental"] = DOMAIN_REGISTRY["rental"]

# Mapping from name fragments used in directory names to DOMAIN_REGISTRY keys.
_FRAGMENT_TO_DOMAIN = {
    "vehicle_rental": "rental",
    "food_and_dining": "food_and_dining",
    "food_dining": "food_and_dining",
    "food": "food_and_dining",
    "kayak_rental": "kayak_rental",
    "live_show": "live_show",
    "attraction": "attraction",
    "hotel": "hotel",
    "flight": "flight",
    "cruise": "cruise",
    "rental": "rental",
    "bar": "bar",
    "cafe": "cafe",
    "dessert": "dessert",
}
# Sort by length descending so greedy matching picks the longest fragment first.
_SORTED_FRAGMENTS = sorted(_FRAGMENT_TO_DOMAIN.keys(), key=len, reverse=True)


def resolve_domain_alias(name: str) -> dict | None:
    """Auto-discover a multi-domain alias by matching against data/user_policies/data/.

    Returns {"domains": [...], "templates": "..."} or None if not resolvable.
    """
    # Check if a directory exists for this name
    data_dir = os.path.join(_repo_root, "data/user_policies", "data", name)
    if not os.path.isdir(data_dir):
        return None

    # Find the populated templates JSON
    templates_path = None
    for fname in os.listdir(data_dir):
        if fname.startswith("populated_") and fname.endswith(".json"):
            templates_path = os.path.join("data/user_policies", "data", name, fname)
            break
    if not templates_path:
        return None

    # Parse domain names from the directory name using greedy fragment matching
    remaining = name
    domains = []
    while remaining:
        remaining = remaining.lstrip("_")
        matched = False
        for fragment in _SORTED_FRAGMENTS:
            if remaining.startswith(fragment):
                domain_key = _FRAGMENT_TO_DOMAIN[fragment]
                if domain_key not in domains:
                    domains.append(domain_key)
                remaining = remaining[len(fragment) :]
                matched = True
                break
        if not matched:
            # Skip one character and try again (handles separators like '_')
            remaining = remaining[1:]

    if not domains:
        return None

    return {"domains": domains, "templates": templates_path}


# ---------------------------------------------------------------------------
# Helper: discover general tools from the general tools folder
# ---------------------------------------------------------------------------


def _get_general_tools() -> dict:
    """Return a {tool_name: module_path} dict for every .py file in the general
    tools folder, excluding __init__.py and cache.py (cache is handled per-domain)."""
    general_dir = os.path.join(_repo_root, "src", "t1_plus_plus", "tools", "general")
    tools = {}
    for fname in os.listdir(general_dir):
        if fname.endswith(".py") and fname not in ("__init__.py", "cache.py"):
            tool_name = fname[:-3]  # strip .py
            tools[tool_name] = f"t1_plus_plus.tools.general.{tool_name}"
    return tools


def build_combined_domain_cfg(
    domains: list[str], templates_override: str | None = None
) -> dict:
    """Merge multiple domain configs into a single combined config.

    Tools, policy files, and filter/search tools are merged from all domains.
    The templates path must be provided via --templates for combined domains.
    """
    merged_tools = {}
    policy_files = []
    filter_tools = []
    search_tools = []
    assistant_names = []
    schema_notes = []
    greetings = []
    user_intros = []
    hallucination_examples = []

    for domain_name in domains:
        cfg = DOMAIN_REGISTRY[domain_name]
        merged_tools.update(cfg["tools"])
        if cfg.get("policy_file"):
            policy_files.append(cfg["policy_file"])
        if cfg.get("filter_tool"):
            filter_tools.append(cfg["filter_tool"])
        if cfg.get("search_tool"):
            search_tools.append(cfg["search_tool"])
        assistant_names.append(cfg.get("assistant_name", domain_name))
        if cfg.get("schema_note"):
            schema_notes.append(cfg["schema_note"])
        if cfg.get("greeting"):
            greetings.append(cfg["greeting"])
        if cfg.get("user_intro"):
            user_intros.append(cfg["user_intro"])
        if cfg.get("hallucination_examples"):
            hallucination_examples.append(cfg["hallucination_examples"])

    combined_name = " + ".join(assistant_names)
    domain_label = "_".join(domains)

    return {
        "tools": merged_tools,
        "policy_files": policy_files,
        "policy_file": policy_files[0] if len(policy_files) == 1 else None,
        "templates": templates_override,
        "greeting": (
            f"Hello! Welcome to {combined_name}. How can I help you today? "
            "To get started, could you let me know which city you are in?"
        ),
        "user_intro": " and ".join(user_intros),
        "assistant_name": combined_name,
        "schema_note": "; ".join(schema_notes),
        "filter_tool": filter_tools[0] if len(filter_tools) == 1 else None,
        "filter_tools": filter_tools,
        "search_tool": search_tools[0] if len(search_tools) == 1 else None,
        "search_tools": search_tools,
        "hallucination_examples": ", ".join(hallucination_examples),
        "_domain_label": domain_label,
        "_constituent_domains": list(domains),
    }


# ---------------------------------------------------------------------------
# Helper: load a tool function from its module path
# ---------------------------------------------------------------------------


def _load_tool(module_path: str):
    """Import a module and return the callable with the same name as the last segment."""
    module = importlib.import_module(module_path)
    func_name = module_path.split(".")[-1]
    return getattr(module, func_name)


# ---------------------------------------------------------------------------
# Helper: build tool registry for a domain
# ---------------------------------------------------------------------------


def build_tool_registry(domain_cfg: dict) -> dict:
    registry = {}
    all_tools = {**domain_cfg["tools"], **_get_general_tools()}
    for tool_name, module_path in all_tools.items():
        try:
            module = importlib.import_module(module_path)
            # The function may be named differently from the module (e.g. cache module
            # exposes get_results_from_cache and save_to_cache under the same module path).
            if hasattr(module, tool_name):
                registry[tool_name] = getattr(module, tool_name)
            else:
                func_name = module_path.split(".")[-1]
                registry[tool_name] = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            print(f"  [WARNING] Could not load tool '{tool_name}': {e}")
    return registry


def load_all_tools() -> dict[str, list]:
    """Pre-load and convert tools for every domain to OpenAI format.

    Returns a dict mapping domain name -> list of OpenAI-format tool dicts.
    Missing or unimportable tools are silently skipped.
    """
    cache: dict[str, list] = {}
    for domain, cfg in DOMAIN_REGISTRY.items():
        registry = build_tool_registry(cfg)
        if registry:
            cache[domain] = convert_tools_to_openai_format(registry)
    return cache


# ---------------------------------------------------------------------------
# Helper: load policy text via domain classifier
# ---------------------------------------------------------------------------


def load_policy(
    domain_cfg: dict,
    tools_cache: dict[str, list],
    query: str | None = None,
    chat_history: list | None = None,
    policy_cache: dict | None = None,
    model_name: str | None = None,
    classifier_client=None,
) -> tuple[str, list, list]:
    """Classify relevant domains from the query and load their policy files and tools.

    Returns (policy_text, domains, relevant_tools).
    """
    classify_query = query or domain_cfg.get("assistant_name", "")
    classify_kwargs = {"chat_history": chat_history}
    if model_name:
        classify_kwargs["model"] = model_name
    if classifier_client is not None:
        classify_kwargs["client"] = classifier_client
    domains = classify_domains(classify_query, **classify_kwargs)
    print(f"  [CLASSIFIER] Domains selected: {domains}")

    policy_text = ""
    if domains:
        policy_text = load_policies_for_domains(
            domains, _policies_dir, policy_cache=policy_cache
        )

    if not policy_text:
        policy_text = f"# {domain_cfg['assistant_name']} Policy"

    # Collect tools for the classified domains from the pre-loaded cache
    relevant_tools: list = []
    seen_names: set = set()
    for d in domains or []:
        for tool in tools_cache.get(d, []):
            name = tool.get("function", {}).get("name")
            if name and name not in seen_names:
                relevant_tools.append(tool)
                seen_names.add(name)

    policy_text += f"\n\n## Tools Schema\n\n{str(relevant_tools)}\n"
    return policy_text, domains, relevant_tools


# ---------------------------------------------------------------------------
# Helper: load user template
# ---------------------------------------------------------------------------


def load_user_template(domain_cfg: dict, conversation_id: int) -> str:
    path = domain_cfg.get("templates")
    # Fall back to data/user_policies/data/ if no template path is configured
    if not path:
        domain_key = (
            domain_cfg.get("assistant_name", "")
            .lower()
            .replace(" assistant", "")
            .replace(" ", "_")
        )
        candidate = os.path.join(
            _repo_root,
            "data/user_policies",
            "data",
            f"populated_{domain_key}_user_policy_templates.json",
        )
        if os.path.exists(candidate):
            path = candidate
    if path:
        if not os.path.isabs(path):
            path = os.path.join(_repo_root, path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Support both {"user_template": ...} and plain string entries
            idx = (conversation_id - 1) % len(data)
            entry = data[idx]
            if isinstance(entry, dict):
                return entry.get("user_template", str(entry))
            return str(entry)
        else:
            print(f"  [WARNING] Templates file not found: {path}")
    return (
        f"You are a customer of a {domain_cfg['assistant_name'].lower()}. "
        "Ask questions and complete your task naturally."
    )


# ---------------------------------------------------------------------------
# Policy builders
# ---------------------------------------------------------------------------


def build_user_policy(domain_cfg: dict, user_template: str, max_turns: int) -> str:
    return f"""
You are playing a role-playing game. You are a HUMAN CUSTOMER chatting in a LIVE INSTANT MESSAGING APP {domain_cfg["user_intro"]}.
The user you are chatting with is actually the AI {domain_cfg["assistant_name"]} that specializes in this domain.

YOUR PERSONA AND CONTEXT:
{user_template}

CRITICAL RULES:
1. Act exactly like a human customer in a live chat interface. Never offer to help.
2. Avoid subject lines, greetings (e.g., “Dear”), or sign-offs (e.g., “Sincerely”). Keep responses to 1–3 sentences, like a casual text message.
3. Stay strictly within scope: only ask about {domain_cfg["schema_note"]}. Do not ask about features outside this schema.
4. If the assistant provides a list of options, do not end the conversation—select one and continue.
5. Pace the conversation carefully: you have a maximum of {max_turns} turns to achieve your goal.
6. Be decisive. If options are limited, choose one rather than prolonging negotiation. Do not go beyond your goal.
7. Use natural, human-like phrasing. Always speak the way a real person would text in a casual chat — never like someone reading instructions out loud. Follow the intent of your user template, but rephrase everything in your own natural voice: use contractions, everyday vocabulary, and the tone of a regular customer. Do not echo schema or field names from the template verbatim.
8. Anytime you are listing any dates, ensure you use natural language format. Give the date in the form MM DD, YYYY. MM is in word and DD is a number (e.g., March 1, 2021).
9. Finish the conversation as fast as possible, don't go beyond the GOAL.
10. If you are asking a question, ask in one time.
11. Always pay with the first registered credit card.
12. You always need to pass all arguments that are relevant to the tools.
""".strip()


def build_assistant_policy(domain_cfg: dict, base_policy: str) -> str:
    search_tools = domain_cfg.get("search_tools", [])
    filter_tools = domain_cfg.get("filter_tools", [])
    search_tool = domain_cfg.get("search_tool") or (
        search_tools[0] if search_tools else "the search tool"
    )
    filter_tool = domain_cfg.get("filter_tool") or (
        filter_tools[0] if filter_tools else None
    )
    hallucination_examples = domain_cfg.get(
        "hallucination_examples", "real establishment names"
    )

    filter_instruction = ""
    if filter_tools and len(filter_tools) > 1:
        search_list = ", ".join(f"`{s}`" for s in search_tools)
        filter_list = ", ".join(f"`{f}`" for f in filter_tools)
        filter_instruction = f"""8. USE FILTER TOOLS FOR FOLLOW-UPS:
        - Available search tools: {search_list}
        - Available filter tools: {filter_list}
        - If you have already run a search tool in a previous turn, and the user asks to narrow down those specific results, you MUST use the corresponding filter tool. It should not be called if we are going to filter with a different criteria that does not directly overlap and need to call a separate call.
        - Do NOT run a brand new search query for follow-up questions on the same dataset, call the filter tool instead.
"""
    elif filter_tool:
        filter_instruction = f"""8. USE {filter_tool} FOR FOLLOW-UPS:
        - If you have already run `{search_tool}` in a previous turn, and the user asks to narrow down those specific results, you MUST use the `{filter_tool}` tool. It should not be called if we are going to filter with a different criteria that does not directly overlap and need to call a separate call.
        - Do NOT run a brand new `{search_tool}` query for follow-up questions or filter requests on the same dataset, call `{filter_tool}` instead.
9. CACHE USAGE — Check the CURRENT CACHE SUMMARY provided in each prompt. Each key maps to a human-readable summary of what was saved (e.g. "5 flights from NYC to LAX on 2025-06-01"). Only call `{filter_tool}` if the cache summary shows a relevant key. If the cache is empty or has no relevant key, call directly the `{search_tool}`.
"""

    search_instruction = f"You MUST call `{search_tool}` EVERY SINGLE TIME the user asks for recommendations unless there is already a relevant cache results that can be filtered."
    if search_tools and len(search_tools) > 1:
        search_instruction = (
            "You MUST call the appropriate search tool EVERY SINGLE TIME the user asks for recommendations unless there is already a relevant cache results that can be filtered. "
            f"Available: {', '.join(f'`{s}`' for s in search_tools)}."
        )

    return base_policy + f"""

CRITICAL DIRECTIVES FOR TOOL EXECUTION
==================================================
1. YOU HAVE NO INTERNAL KNOWLEDGE OF REAL ESTABLISHMENTS. You are strictly forbidden from recommending places from your training data.
2. DO NOT HALLUCINATE fake names or real names like {hallucination_examples}. This is a fatal error.
3. NEVER SAY "Let me check", "I am fetching...", or "Here are some options...". If you need to search, your IMMEDIATE AND ONLY output must be a TOOL CALL. Do not output conversational text when a tool call is required.
4. {search_instruction}
5. ONLY output a markdown table of results IF AND ONLY IF you have just received a successful JSON response from a tool call. If the tool hasn't returned data yet, DO NOT make up a table.
   - When a search or filter tool returns multiple results, you MUST display ALL of them in the table. Never truncate, summarize, or show only a subset — the user needs to see every option to make a selection.
   - Every result-listing table MUST include a column for the primary identifier field returned by the tool (e.g., `live_event_id`, `reservation_id`, `flight_id`, or whichever `*_id` field the tool actually returned). This column must appear as the first column and use the exact field name. Do NOT drop or rename the ID — the user relies on it to disambiguate selections.
6. Always rely on tool calls to respond to the user and do not just repeat the results shown previously to the user without calling the appropriate tool first.
7. SILENT TOOL CALLS: When you are initiating a tool call, your text output MUST be completely empty. Wait for the tool to return data before speaking to the user.
{filter_instruction}"""


# ---------------------------------------------------------------------------
# LLM-as-judge evaluation
# ---------------------------------------------------------------------------


def run_llm_judge(
    conversation: list[dict], judge_criteria: dict, client, model: str
) -> dict:
    """
    Ask an LLM to evaluate the conversation against the judge criteria using a 1-5 Likert scale.

    Returns a dict with keys: scores (per criterion score + reasoning), overall_score, overall_reasoning.
    """
    conversation_text = ""
    for msg in conversation:
        role = msg.get("role", "unknown")
        content = msg.get("content") or ""
        if role == "tool":
            tool_name = msg.get("tool_name", "tool")
            conversation_text += f"[TOOL: {tool_name}]\n{content}\n\n"
        elif msg.get("tool_calls"):
            tool_calls_summary = ", ".join(
                f"{tc['name']}({json.dumps(tc.get('args', {}))})"
                for tc in msg["tool_calls"]
            )
            conversation_text += (
                f"[{role.upper()}] (tool calls: {tool_calls_summary})\n{content}\n\n"
            )
        else:
            conversation_text += f"[{role.upper()}]\n{content}\n\n"

    criteria_text = json.dumps(judge_criteria, indent=2)

    prompt = f"""You are an objective evaluator of AI assistant conversations.

Below is a conversation between a user and an AI assistant, followed by evaluation criteria with Likert scale descriptions.

## CONVERSATION
{conversation_text.strip()}

## EVALUATION CRITERIA
{criteria_text}

## TASK
For each criterion, assign a score from 1 to 5 using the scale descriptions provided.
Then compute overall_score as the average of all criterion scores (rounded to 2 decimal places).
Respond with a JSON object in this exact format:
{{
  "scores": {{
    "<criterion_name>": {{
      "score": <integer 1-5>,
      "reasoning": "brief explanation referencing the scale"
    }}
  }},
  "overall_score": <float, average of all scores>,
  "overall_reasoning": "brief summary"
}}

Respond ONLY with the JSON object, no other text."""

    try:
        for _attempt in range(1, 4):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                )
                break
            except Exception as exc:
                if _attempt == 3:
                    raise
                print(
                    f"   [WARN] LLM-as-judge API call failed (attempt {_attempt}/3): {exc}. Retrying in 5s..."
                )
                time.sleep(5)
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e), "overall_score": None}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Generic simulation runner for any supported domain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--domain",
        nargs="+",
        required=True,
        help=(
            "Domain(s) to simulate. Pass one for single-domain mode, or multiple "
            "for combined mode (e.g., --domain live_show food_and_dining). "
            f"Available: {', '.join(DOMAIN_REGISTRY.keys())}"
        ),
    )
    parser.add_argument(
        "--templates",
        type=str,
        default=None,
        help=(
            "Path to the populated templates JSON file. Required for multi-domain "
            "mode. Overrides the domain's default templates path."
        ),
    )
    parser.add_argument(
        "--conversation_id",
        type=int,
        default=1,
        help="1-based ID of the user-policy template to use (default: 1). Pass -1 to run all IDs.",
    )
    parser.add_argument(
        "--resume_from",
        type=int,
        default=1,
        help="When --conversation_id is -1, start from this 1-based ID (default: 1, i.e. run all).",
    )
    parser.add_argument(
        "--max_turns",
        type=int,
        default=20,
        help="Maximum number of conversation turns (default: 20).",
    )
    parser.add_argument(
        "--user_model_name",
        type=str,
        default="google/gemma-4-26B-A4B-it",
        help="Model name for the simulated user role (default: google/gemma-4-26B-A4B-it).",
    )
    parser.add_argument(
        "--assistant_model_name",
        type=str,
        default="openai/gpt-oss-120b",
        help="Model name for the assistant role (default: openai/gpt-oss-120b).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=True,
        help="Save the simulated conversation to disk (default: True).",
    )
    parser.add_argument(
        "--eval-debug",
        action="store_true",
        help=(
            "Enable DEBUG-level logging from the eval module, printing per-tool "
            "and per-param evaluation decisions to stderr."
        ),
    )
    parser.add_argument(
        "--run_dir",
        type=str,
        default=None,
        help=(
            "Folder to save the conversation + metrics JSON into. Relative "
            "paths resolve under simulated_conversation/<model>/<domain>/. "
            "Defaults to writing files directly in simulated_conversation/<model>/<domain>/."
        ),
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help=(
            "Launch a background bash loop that runs this script for every "
            "conversation_id in [--start, --end], up to --parallel at a time. "
            "stdout+stderr are redirected to --log. The parent exits after "
            "printing the PID."
        ),
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="(batch mode) First conversation_id, inclusive (default: 1).",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=50,
        help="(batch mode) Last conversation_id, inclusive (default: 50).",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help=(
            "(batch mode) Number of conversations to run concurrently (default: 4). Use 1 for sequential."
        ),
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help=(
            "Dev mode: write output files directly into "
            "simulated_conversation/<model>/<domain>/ without creating a "
            "timestamped run_<timestamp>/ subfolder."
        ),
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help=(
            "Directory for run log files. Defaults to <repo_root>/logs/. "
            "Logs are written to <log-dir>/run_<NNN>_<domain>.log."
        ),
    )
    args = parser.parse_args()

    # Handle --domain all: run all aliases
    if len(args.domain) == 1 and args.domain[0] == "all":
        all_domain_sets = _discover_all_runnable_domains()
        print(f"[ALL MODE] {len(all_domain_sets)} alias(es):")
        for entry in all_domain_sets:
            print(f"  {entry['label']:<45} ({len(entry['domains'])} domain(s))")
        print()
        for entry in all_domain_sets:
            print(f"\n{'#' * 70}")
            print(f"# Running: {entry['label']}")
            print(f"{'#' * 70}")
            import copy
            sub_args = copy.deepcopy(args)
            sub_args.domain = entry["domains"]
            sub_args.templates = entry["templates"]
            sub_args.domain_label = entry["label"]
            _run_domain_set(sub_args, parser)
        return

    _run_domain_set(args, parser)


def _discover_all_runnable_domains() -> list[dict]:
    """Return all entries from DOMAIN_ALIASES whose templates file exists."""
    results = []
    for label, alias in DOMAIN_ALIASES.items():
        templates_path = os.path.join(_repo_root, alias["templates"])
        if os.path.exists(templates_path):
            results.append({"label": label, "domains": alias["domains"], "templates": alias["templates"]})
        else:
            print(f"  [SKIP] {label} — templates not found: {alias['templates']}")
    return results


def _run_domain_set(args, parser):
    """Run simulation for a single domain set (the original main() logic)."""
    alias_name = getattr(args, "domain_label", None)
    if (
        not alias_name
        and len(args.domain) == 1
        and args.domain[0] not in DOMAIN_REGISTRY
    ):
        raw_name = args.domain[0]
        if raw_name in DOMAIN_ALIASES:
            alias = DOMAIN_ALIASES[raw_name]
            alias_name = raw_name
            args.domain = alias["domains"]
            if not args.templates:
                args.templates = alias["templates"]
        else:
            parser.error(f"Unknown domain or alias: '{raw_name}'. Available: {', '.join(DOMAIN_REGISTRY.keys())}, {', '.join(DOMAIN_ALIASES.keys())}")

    # Validate domain names
    for d in args.domain:
        if d not in DOMAIN_REGISTRY:
            parser.error(
                f"Unknown domain: '{d}'. Available: {', '.join(DOMAIN_REGISTRY.keys())}, {', '.join(DOMAIN_ALIASES.keys())}"
            )

    # Build domain config: single domain or combined
    if len(args.domain) == 1:
        domain_cfg = DOMAIN_REGISTRY[args.domain[0]]
        if args.templates:
            domain_cfg = dict(domain_cfg)
            domain_cfg["templates"] = args.templates
        domain_label = args.domain[0]
    else:
        if not args.templates:
            parser.error("--templates is required when using multiple domains.")
        domain_cfg = build_combined_domain_cfg(
            args.domain, templates_override=args.templates
        )
        domain_label = alias_name or domain_cfg["_domain_label"]

    if args.batch:
        extra = []
        if args.templates:
            extra.extend(["--templates", args.templates])
        if args.dev:
            extra.append("--dev")
        extra.extend(["--assistant_model_name", args.assistant_model_name])
        launch_batch(
            script="scripts/run_simulation.py",
            domain=args.domain,
            model=args.user_model_name,
            model_flag="--user_model_name",
            start=args.start,
            end=args.end,
            parallel=args.parallel,
            max_turns=args.max_turns,
            save=args.save,
            log_name=None,
            run_dir_name=args.run_dir,
            extra_flags=extra,
            model_dir=args.assistant_model_name,
            dev=args.dev,
        )
        return

    logging.basicConfig(
        level=logging.DEBUG if args.eval_debug else logging.WARNING,
        format="%(message)s",
        stream=sys.stderr,
    )

    # Setup run logging (tee to file)
    setup_run_logging(domain_label, log_dir=args.log_dir)

    # Store the resolved domain label on args for use in _run_single
    args.domain_label = domain_label

    # Resolve the full list of conversation IDs to run
    if args.conversation_id == -1:
        templates_path = domain_cfg.get("templates")
        if templates_path:
            if not os.path.isabs(templates_path):
                templates_path = os.path.join(_repo_root, templates_path)
            if os.path.exists(templates_path):
                with open(templates_path, "r", encoding="utf-8") as f:
                    _all_entries = json.load(f)
                conversation_ids = [
                    e["id"] for e in _all_entries if isinstance(e, dict) and "id" in e
                ]
                if args.resume_from > 1:
                    conversation_ids = [
                        cid for cid in conversation_ids if cid >= args.resume_from
                    ]
                    print(
                        f"  Resuming from conversation ID {args.resume_from} ({len(conversation_ids)} remaining)"
                    )
            else:
                print(f"ERROR: Templates file not found: {templates_path}")
                sys.exit(1)
        else:
            print("ERROR: No templates configured for this domain; cannot run all IDs.")
            sys.exit(1)
    else:
        conversation_ids = [args.conversation_id]

    # 1. Build tool registry once (shared across all conversation IDs)
    print("[1/4] Loading tools...")
    tool_registry = build_tool_registry(domain_cfg)
    if not tool_registry:
        print("ERROR: No tools could be loaded. Exiting.")
        sys.exit(1)
    print(f"      Loaded: {list(tool_registry.keys())}")

    # 2. Pre-load all domains' tools into OpenAI format once
    print("[2/4] Converting tools to OpenAI format...")
    print("      Pre-loading all domain tools...")
    _all_tools = load_all_tools()
    print(f"      Loaded tools for domains: {list(_all_tools.keys())}")
    openai_tools = convert_tools_to_openai_format(tool_registry)

    for conversation_id in conversation_ids:
        _run_single(
            args=args,
            domain_cfg=domain_cfg,
            tool_registry=tool_registry,
            openai_tools=openai_tools,
            all_tools=_all_tools,
            conversation_id=conversation_id,
        )


def _run_single(
    args, domain_cfg, tool_registry, openai_tools, all_tools, conversation_id
):
    """Run simulation and evaluation for a single conversation_id."""
    domain_label = args.domain_label
    print(f"\n{'=' * 60}")
    print(f"  Domain       : {domain_label}")
    print(f"  Conversation : {conversation_id}")
    print(f"  Max Turns    : {args.max_turns}")
    print(f"  Model (user) : {args.user_model_name}")
    print(f"  Model (asst) : {args.assistant_model_name}")
    print(f"{'=' * 60}\n")

    # 3. Build policies
    print("[3/4] Building policies...")
    user_template = load_user_template(domain_cfg, conversation_id)
    user_policy = build_user_policy(domain_cfg, user_template, args.max_turns)

    domain_log: list = []

    def _policy_loader(user_text: str, chat_history: list) -> tuple[str, list]:
        base, domains, relevant_tools = load_policy(
            domain_cfg,
            all_tools,
            query=user_text,
            chat_history=chat_history,
            model_name=args.user_model_name,
        )
        domain_log.append({"turn": len(domain_log) + 1, "domains": domains})
        return build_assistant_policy(domain_cfg, base), relevant_tools

    assistant_policy = build_assistant_policy(
        domain_cfg, f"# {domain_cfg['assistant_name']} Policy"
    )

    # 4. Run simulation
    print("[4/4] Starting simulation...\n")

    run_dir = (
        resolve_run_dir(
            args.run_dir, domain_label, args.assistant_model_name, dev=args.dev
        )
        if args.save
        else None
    )
    if run_dir:
        print(f"      Run dir: {run_dir}")

    run_simulation(
        user_policy=user_policy,
        assistant_policy=assistant_policy,
        assistant_initial_greeting=domain_cfg["greeting"],
        openai_format_tools=openai_tools,
        tool_registry=tool_registry,
        domain_name=domain_label,
        conversation_id=conversation_id,
        max_turns=args.max_turns,
        filter_tool=domain_cfg.get("filter_tool"),
        policy_loader=_policy_loader,
        user_model_name=args.user_model_name,
        assistant_model_name=args.assistant_model_name,
        save=args.save,
        output_dir=run_dir,
        domain_log=domain_log,
        domains=args.domain,
    )

    # 5. Compute metrics (exact match + LLM-as-judge)
    output_dir = (
        run_dir or f"simulated_conversation/{args.assistant_model_name}/{domain_label}"
    )
    sim_file = os.path.join(output_dir, f"{domain_label}_{conversation_id}.json")

    templates_path = domain_cfg.get("templates")
    if templates_path and not os.path.isabs(templates_path):
        templates_path = os.path.join(_repo_root, templates_path)

    benchmark_entry = None
    if templates_path and os.path.exists(templates_path):
        with open(templates_path, "r", encoding="utf-8") as f:
            all_templates = json.load(f)
        idx = (conversation_id - 1) % len(all_templates)
        entry = all_templates[idx]
        if isinstance(entry, dict) and "benchmark_success_criteria" in entry:
            benchmark_entry = entry

    if not args.save:
        print("\n[METRICS] Skipping eval (no --save flag).")
    elif not benchmark_entry:
        print("\n[METRICS] No benchmark entry found — skipping eval.")
    else:
        print(f"\n{'=' * 60}")
        print("  METRICS EVALUATION")
        print(f"{'=' * 60}")

        with open(sim_file, "r", encoding="utf-8") as f:
            sim_data = json.load(f)

        # --- Tool prediction vs gold labels ---
        expected_tool_calls = get_expected_tool_calls(benchmark_entry)
        actual_tool_log = get_actual_tool_log(sim_data)

        # Inject tool_calls into the conversation JSON (gold + predicted)
        turn_to_domains_pre = {
            e["turn"]: e.get("domains") or [] for e in (sim_data.get("domains") or [])
        }
        predicted_entries_print = [
            e
            for e in actual_tool_log
            if e.get("tool_name") and e["tool_name"] != "None"
        ]

        print("\n[Tool Calls: Gold vs Predicted]")
        print("  GOLD (expected):")
        if expected_tool_calls:
            for entry in expected_tool_calls:
                params = entry.get("parameters", {})
                print(f"    {entry['name']}({json.dumps(params)})")
        else:
            print("    (none)")
        print("  PREDICTED (actual):")
        if predicted_entries_print:
            for entry in predicted_entries_print:
                print(
                    f"    turn={entry['turn']} {entry['tool_name']}({json.dumps(entry.get('parameters', {}))})"
                )
        else:
            print("    (none)")

        # --- Exact match ---
        if expected_tool_calls:
            exact_match_result = evaluate_single_conversation(
                expected_tool_calls,
                actual_tool_log,
            )

            tl = exact_match_result["tool_level"]
            pl = exact_match_result["parameter_level"]

            print("\n[Exact Match]")
            print(
                f"  Tool-level  — P={tl['precision']:.4f}  R={tl['recall']:.4f}  F1={tl['f1']:.4f}"
            )
            print(
                f"  Param-level — P={pl['precision']:.4f}  R={pl['recall']:.4f}  F1={pl['f1']:.4f}"
            )
            print(f"  Expected tools  : {tl['expected_tools']}")
            if tl["false_negatives"]:
                print(f"  Missed tools    : {tl['false_negatives']}")
            if tl["false_positives"]:
                print(f"  Extra tools     : {tl['false_positives']}")
            for tool_name, detail in exact_match_result["per_tool_detail"].items():
                status = (
                    "OK"
                    if detail["all_params_matched"]
                    else ("NOT CALLED" if not detail["tool_called"] else "PARTIAL")
                )
                print(f"  [{tool_name}] {status}  param F1={detail['param_f1']:.3f}")
                if detail.get("missing_params"):
                    print(f"    missing: {detail['missing_params']}")
        else:
            exact_match_result = {}
            print(
                "\n[Exact Match] No exact_match criteria in benchmark entry — skipped."
            )

        # --- Tool Output Exact Match ---
        tool_output_match_result = {}
        if expected_tool_calls:
            tool_output_match_result = evaluate_tool_output_exact_match(
                expected_tool_calls,
                sim_data.get("conversation", []),
                tool_registry,
            )
            print(f"\n[Tool Output Exact Match]")
            print(
                f"  Score: {tool_output_match_result['score']:.4f}  "
                f"({tool_output_match_result['matches']}/{tool_output_match_result['total']})"
            )
            for detail in tool_output_match_result["per_tool_detail"]:
                status = "MATCH" if detail["matched"] else "MISS"
                err = f" (error: {detail['error']})" if detail.get("error") else ""
                print(f"  [{detail['tool_name']}] {status}{err}")
        else:
            print("\n[Tool Output Exact Match] No expected tool calls — skipped.")

        # Add tool_output gold/predicted to tool_calls_block, then write conversation JSON
        # Build gold with outputs from tool output eval
        gold_with_output = []
        if expected_tool_calls:
            for detail in tool_output_match_result.get("per_tool_detail", []):
                gold_with_output.append(
                    {
                        "tool_name": detail["tool_name"],
                        "parameters": detail.get("parameters", {}),
                        "output": detail.get("expected_output"),
                    }
                )
        else:
            gold_with_output = [
                {
                    "tool_name": e["name"],
                    "parameters": e.get("parameters", {}),
                    "output": None,
                }
                for e in expected_tool_calls
            ]

        # Merge predicted tool calls with their outputs (matched by position)
        actual_outputs = [
            msg.get("content", "")
            for msg in sim_data.get("conversation", [])
            if msg.get("role") == "tool" and msg.get("content", "")
        ]
        predicted_entries = [
            e
            for e in actual_tool_log
            if e.get("tool_name") and e["tool_name"] != "None"
        ]
        predicted_with_output = []
        for i, e in enumerate(predicted_entries):
            predicted_with_output.append(
                {
                    "turn": e["turn"],
                    "domain": turn_to_domains_pre.get(e["turn"]),
                    "tool_name": e["tool_name"],
                    "parameters": e.get("parameters", {}),
                    "output": actual_outputs[i] if i < len(actual_outputs) else None,
                }
            )

        tools_block = {
            "gold": gold_with_output,
            "predicted": predicted_with_output,
        }

        # Rebuild with tools inserted before "conversation"
        ordered = {}
        for k, v in sim_data.items():
            if k == "conversation":
                ordered["tools"] = tools_block
            if k not in ("tool_calls", "tools"):
                ordered[k] = v
        if "tools" not in ordered:
            ordered["tools"] = tools_block
        sim_data = ordered
        with open(sim_file, "w", encoding="utf-8") as f:
            json.dump(sim_data, f, indent=4, ensure_ascii=False)

        # --- LLM-as-judge ---
        judge_criteria = LLM_JUDGE_RUBRIC
        if judge_criteria:
            print("\n[LLM-as-Judge]")
            print(f"  Criteria: {judge_criteria}")

            from openai import OpenAI

            client = OpenAI(
                base_url=os.getenv(
                    "LLM_BASE_URL",
                    "http://mc-router.llm-pretraining.svc.cluster.local:8000/v1",
                ),
                api_key=os.getenv("LLM_API_KEY", "unused"),
            )
            judge_model = args.user_model_name

            judge_result = run_llm_judge(
                conversation=sim_data.get("conversation", []),
                judge_criteria=judge_criteria,
                client=client,
                model=judge_model,
            )

            if "error" in judge_result:
                print(f"  Error: {judge_result['error']}")
            else:
                overall = judge_result.get("overall_score")
                print(f"  Overall score: {overall}/5")
                print(f"  Reasoning    : {judge_result.get('overall_reasoning', '')}")
                for criterion, verdict in judge_result.get("scores", {}).items():
                    print(
                        f"  [{criterion}] score={verdict.get('score')}/5: {verdict.get('reasoning', '')}"
                    )
        else:
            judge_result = {}
            print(
                "\n[LLM-as-Judge] No llm_as_judge criteria in benchmark entry — skipped."
            )

        # --- Save metrics alongside sim output ---
        metrics_file = os.path.join(
            output_dir, f"metrics_{domain_label}_{conversation_id}.json"
        )

        _tl = exact_match_result.get("tool_level", {})
        _pl = exact_match_result.get("parameter_level", {})
        _to = tool_output_match_result

        metrics_output = {
            "conversation_id": conversation_id,
            "tool_call": {
                "precision": _tl.get("precision"),
                "recall": _tl.get("recall"),
                "f1": _tl.get("f1"),
                "accuracy": _tl.get("accuracy"),
            },
            "parameter": {
                "precision": _pl.get("precision"),
                "recall": _pl.get("recall"),
                "f1": _pl.get("f1"),
                "accuracy": _pl.get("accuracy"),
            },
            "tool_output": {
                "exact_match": _to.get("score"),
            },
            "pass": compute_pass(exact_match_result, tool_output_match_result),
            "llm_as_judge": (
                {
                    "overall_score": judge_result.get("overall_score"),
                    "overall_reasoning": judge_result.get("overall_reasoning"),
                    "scores": {
                        criterion: {
                            "score": verdict.get("score"),
                            "reasoning": verdict.get("reasoning"),
                        }
                        for criterion, verdict in judge_result.get("scores", {}).items()
                    },
                    "error": judge_result.get("error"),
                }
                if judge_result
                else {}
            ),
        }
        if args.save:
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics_output, f, indent=4, ensure_ascii=False)
            print(f"\n💾 Metrics saved to: {metrics_file}")


if __name__ == "__main__":
    main()
