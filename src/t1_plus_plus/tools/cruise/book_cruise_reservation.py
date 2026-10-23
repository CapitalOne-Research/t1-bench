import os
from datetime import datetime
from pathlib import Path
import pandas as pd

from t1_plus_plus.schema.cruise.cruise_reservation import (
    CruiseReservation,
    BookCruiseReservationInputModel,
    BookCruiseReservationOutputModel,
)
from t1_plus_plus.schema.cruise.cruise_reservation_db import global_cruise_reservations_db

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_CRUISES = os.getenv("ALL_CRUISES", str(_data_dir / "data_cruises.csv"))
all_cruises_df = pd.read_csv(ALL_CRUISES) if Path(ALL_CRUISES).exists() else pd.DataFrame()

def book_cruise_reservation(**kwargs: BookCruiseReservationInputModel) -> BookCruiseReservationOutputModel:
    """
    Description:
        Books a new cruise reservation. Validates passport requirements,
        calculates base charge, and stores the reservation details.
    """
    # 2. Validate Agent Input with Error Catching
    try:
        input_data = BookCruiseReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return BookCruiseReservationOutputModel(
            status="error",
            message=f"Invalid input data: {str(e)}",
        )

    if not input_data.has_passport:
        return BookCruiseReservationOutputModel(
            status="error",
            message="Booking failed. A valid passport must be verified for all cruise passengers.",
        )

    dep_dt = datetime.strptime(input_data.departure_date, "%Y-%m-%d")

    # Optional Occupancy Check against dataframe
    if not all_cruises_df.empty:
        try:
            cruise = all_cruises_df[all_cruises_df["cruise_id"] == input_data.cruise_id].iloc[0]
            if "passenger_capacity" in cruise and input_data.number_guests > cruise["passenger_capacity"]:
                return BookCruiseReservationOutputModel(
                    status="error",
                    message=f"Booking failed. Exceeds remaining capacity on this cruise.",
                )
        except (NameError, IndexError):
            pass

    res_id = f"RES-{input_data.cruise_id}"
    base_charge = 850.00 * input_data.number_guests  # Mock base charge

    new_reservation = CruiseReservation(
        reservation_id=res_id,
        user_id=input_data.user_id,
        cruise_id=input_data.cruise_id,
        primary_guest_name=input_data.primary_guest_name,
        number_guests=input_data.number_guests,
        departure_date=dep_dt,
        cabin_type=input_data.cabin_type,
        credit_card_last_four=input_data.credit_card_last_four,
        is_upgraded=False,
        reservation_charge=base_charge,
        latest_refund_date_days=14,  # 14-day policy for cruises
        status="Active",
    )

    global_cruise_reservations_db.add_reservation(new_reservation)

    return BookCruiseReservationOutputModel(
        status="success",
        message=f"Cruise reservation successfully booked for {input_data.primary_guest_name}.",
        reservation_id=res_id,
        reservation_charge=base_charge,
    )
