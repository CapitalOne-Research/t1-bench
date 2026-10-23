import hashlib
import os
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    BookReservationInputModel,
    BookReservationOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import (
    Reservation,
    global_reservations_db,
)
from t1_plus_plus.ontology.food_and_dining import PRIVATE_DINING_UPGRADE_FEE

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FOOD_AND_DINING = os.getenv("ALL_FOOD_AND_DINING", str(_data_dir / "data_food_and_dining.csv"))

try:
    food_and_dining_df = pd.read_csv(ALL_FOOD_AND_DINING)
except FileNotFoundError:
    food_and_dining_df = pd.DataFrame()


def book_food_and_dining_reservation(**kwargs) -> BookReservationOutputModel:
    """
    Description:
        Book a dine-in reservation at a food and dining establishment.
        Reservation charge = price_per_person × number_guests.
        Private dining upgrade adds a flat $50.00 fee.

    Examples:
    >>> # Usage Example:
    book_food_and_dining_reservation(user_id="USR-DFEDBA29", restaurant_id="FAD-205956", primary_guest_name="Emily Davis", number_guests=2, price_per_person=93.0, reservation_date="2026-06-15", reservation_time="19:00")

    >>> # Usage Example: with private dining upgrade
    book_food_and_dining_reservation(user_id="USR-58E33E81", restaurant_id="FAD-265982", primary_guest_name="James Brown", number_guests=2, price_per_person=32.0, reservation_date="2026-07-04", reservation_time="18:30", has_private_dining=True)

    Returns:
        BookReservationOutputModel: status, reservation_id, reservation_charge.
    """
    try:
        input_data = BookReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return BookReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    if food_and_dining_df.empty or input_data.restaurant_id not in food_and_dining_df["id"].values:
        return BookReservationOutputModel(
            status="error",
            message=f"Reservation failed. Establishment with ID {input_data.restaurant_id} not found.",
        )

    charge = round(input_data.price_per_person * input_data.number_guests, 2)
    if input_data.has_private_dining:
        charge = round(charge + PRIVATE_DINING_UPGRADE_FEE, 2)

    seed = f"{input_data.user_id}:{input_data.restaurant_id}:{input_data.number_guests}:{input_data.price_per_person}"
    reservation_id = f"RES-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"

    new_reservation = Reservation(
        reservation_id=reservation_id,
        user_id=input_data.user_id,
        restaurant_id=input_data.restaurant_id,
        primary_guest_name=input_data.primary_guest_name,
        number_guests=input_data.number_guests,
        price_per_person=input_data.price_per_person,
        reservation_date=input_data.reservation_date,
        reservation_time=input_data.reservation_time,
        has_private_dining=input_data.has_private_dining,
        reservation_charge=charge,
        status="Active",
    )

    global_reservations_db.add_reservation(new_reservation)

    private_note = " (includes private dining upgrade)" if input_data.has_private_dining else ""
    return BookReservationOutputModel(
        status="success",
        message=f"Reservation {reservation_id} booked successfully for {input_data.reservation_date} at {input_data.reservation_time}. Total charge: ${charge:.2f}{private_note}.",
        reservation_id=reservation_id,
        reservation_date=input_data.reservation_date,
        reservation_time=input_data.reservation_time,
        reservation_charge=charge,
        has_private_dining=input_data.has_private_dining,
    )
