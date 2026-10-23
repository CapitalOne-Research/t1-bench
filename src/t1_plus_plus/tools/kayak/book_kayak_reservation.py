import pandas as pd
from pathlib import Path
from typing import Any

from t1_plus_plus.schema.kayak.book_kayak_reservation import BookKayakReservationInputModel, BookKayakReservationOutputModel
from t1_plus_plus.schema.kayak.kayak_reservation_db import global_kayak_reservation_db, KayakReservation

# Load the CSV — resolve relative to this file so it works regardless of cwd or import path
_data_dir = Path(__file__).resolve().parents[4] / "datasets"
_CSV_PATH = str(_data_dir / "data_kayak_rental.csv")
try:
    all_kayak_df = pd.read_csv(_CSV_PATH)
except FileNotFoundError:
    all_kayak_df = pd.DataFrame()


def book_kayak_reservation(**kwargs: Any) -> BookKayakReservationOutputModel:
    """
    Dynamically book a kayak reservation and calculate total cost.
    """
    try:
        booking_data = BookKayakReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return BookKayakReservationOutputModel(
            status="error", message=f"Validation error: {str(e)}"
        )

    if all_kayak_df.empty:
        return BookKayakReservationOutputModel(
            status="error", message="Database is currently unavailable."
        )

    # Check if rental_id exists and get its details
    rental_row = all_kayak_df[all_kayak_df["rental_id"] == booking_data.rental_id]

    if rental_row.empty:
        return BookKayakReservationOutputModel(
            status="error", message=f"Rental ID {booking_data.rental_id} does not exist."
        )

    # Extract the hourly price
    hourly_rate = float(rental_row.iloc[0]["price_per_hour"])

    # Calculate Total
    total_cost = hourly_rate * booking_data.duration

    # Generate a unique Booking ID
    new_booking_id = f"RES-{booking_data.rental_id}"

    # Create Database Entry
    new_reservation = KayakReservation(
        booking_id=new_booking_id,
        user_id=booking_data.user_id,
        rental_id=booking_data.rental_id,
        vessel_type=booking_data.vessel_type,
        date=booking_data.date,
        start_time=booking_data.start_time,
        duration=booking_data.duration,
        total_cost=total_cost,
        status="Confirmed"
    )

    # Save to In-Memory DB
    global_kayak_reservation_db.add_reservation(new_reservation)

    return BookKayakReservationOutputModel(
        status="success",
        message=f"Successfully booked {booking_data.vessel_type} at {rental_row.iloc[0]['business_name']}.",
        booking_id=new_booking_id,
        total_cost=total_cost
    )
