import hashlib
from datetime import datetime
from pathlib import Path
import pandas as pd

from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation import (
    RentalReservation,
    BookRentalReservationInputModel,
    BookRentalReservationOutputModel,
)
from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation_db import (
    global_rental_reservations_db,
)

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_RENTALS = str(_data_dir / "data_rental_vehicles.csv")
all_rentals_df = pd.read_csv(ALL_RENTALS)


def book_vehicle_rental_reservation(
    **kwargs: BookRentalReservationInputModel,
) -> BookRentalReservationOutputModel:
    """
    Description:
        Books a new vehicle rental. Validates license requirements,
        availability status, and calculates charges based on duration.

    Examples:
    >>> # Usage Example:
    book_vehicle_rental_reservation(user_id="U123", vehicle_id="VEH-001", primary_driver_name="Jane Doe", start_date="2026-05-01", end_date="2026-05-05", has_drivers_license=True)

    >>> # Usage Example:
    book_vehicle_rental_reservation(user_id="U456", vehicle_id="VEH-042", primary_driver_name="John Smith", start_date="2026-06-10", end_date="2026-06-15", has_drivers_license=True)

    Returns:
        BookRentalReservationOutputModel: Output object containing status, message, reservation_id, and reservation_charge.
    """
    input_data = BookRentalReservationInputModel.model_validate(kwargs)

    # 1. Driver's License Policy Check
    if not input_data.has_drivers_license:
        return BookRentalReservationOutputModel(
            status="error",
            message="Booking failed. A valid driver's license must be verified.",
        )

    # 2. Date Parsing and Duration Calculation
    start_dt = datetime.strptime(input_data.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(input_data.end_date, "%Y-%m-%d")
    duration_days = (end_dt - start_dt).days

    if duration_days <= 0:
        return BookRentalReservationOutputModel(
            status="error",
            message="Booking failed. End date must be after the start date.",
        )

    # 3. Vehicle Lookup and Availability Check
    try:
        vehicle = all_rentals_df[all_rentals_df["id"] == input_data.vehicle_id].iloc[0]

        daily_rate = vehicle["base_price_per_day"]
    except (IndexError, KeyError):
        return BookRentalReservationOutputModel(
            status="error",
            message="Booking failed. Vehicle ID not found.",
        )

    # 4. Generate deterministic Reservation ID
    seed = f"{input_data.user_id}:{input_data.vehicle_id}:{input_data.start_date}"
    res_id = f"REN-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"
    total_charge = float(daily_rate * duration_days)

    new_reservation = RentalReservation(
        reservation_id=res_id,
        user_id=input_data.user_id,
        vehicle_id=input_data.vehicle_id,
        primary_driver_name=input_data.primary_driver_name,
        start_date=start_dt,
        end_date=end_dt,
        reservation_charge=total_charge,
        latest_refund_date_days=1,  # 24-hour policy
        status="Active",
        service_provider=vehicle["service_provider"],
        make=vehicle["make"],
        model=vehicle["model"],
        category=vehicle["category"],
        base_price_per_day=daily_rate,
    )

    global_rental_reservations_db.add_reservation(new_reservation)

    return BookRentalReservationOutputModel(
        status="success",
        message=f"Rental successfully booked for {input_data.primary_driver_name}.",
        reservation_id=res_id,
        reservation_charge=total_charge,
    )
