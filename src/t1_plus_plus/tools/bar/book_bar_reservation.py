import hashlib
from datetime import datetime
import pandas as pd
from pathlib import Path
from t1_plus_plus.schema.bar.bar_reservation import (
    BarReservation,
    BookBarReservationInputModel,
    BookBarReservationOutputModel,
)
from t1_plus_plus.schema.bar.bar_reservation_db import global_bar_reservations_db

data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_BARS = str(data_dir / "data_bar_lounge.csv")
all_bars_df = pd.read_csv(ALL_BARS)


def book_bar_reservation(
    **kwargs: BookBarReservationInputModel,
) -> BookBarReservationOutputModel:
    """
    Description:
        Use this tool to book a new reservation at a bar. Validates ID requirements, occupancy limits, and stores the reservation details.

    Examples:
    >>> # Usage Example:
    book_bar_reservation(user_id="U123", venue_id="BAR456", primary_guest_name="Jane Doe", number_guests=4, event_datetime="2026-05-10 20:00", credit_card_last_four="1234", has_drivers_license=True)

    >>> # Usage Example:
    book_bar_reservation(user_id="U789", venue_id="BAR101", primary_guest_name="John Smith", number_guests=2, event_datetime="2026-06-15 21:30", credit_card_last_four="5678", has_drivers_license=True)

    Returns:
        BookBarReservationOutputModel: Output object which contains the reservation status, reservation ID, and charge details.
    """
    input_data = BookBarReservationInputModel.model_validate(kwargs)

    if not input_data.has_drivers_license:
        return BookBarReservationOutputModel(
            status="error",
            message="Booking failed. A valid driver's license must be verified.",
        )

    event_dt = datetime.strptime(input_data.event_datetime, "%Y-%m-%d %H:%M")

    # Occupancy Check
    try:
        venue = all_bars_df[all_bars_df["id"] == input_data.venue_id].iloc[0]
        if (
            "event_occupancy" in venue
            and input_data.number_guests > venue["event_occupancy"]
        ):
            return BookBarReservationOutputModel(
                status="error",
                message=f"Booking failed. Number of guests exceeds venue max occupancy of {venue['event_occupancy']}.",
            )
    except (NameError, IndexError):
        pass  # Fallback if dataframe is missing or venue_id is mocked

    seed = f"{input_data.user_id}:{input_data.venue_id}:{input_data.event_datetime}"
    res_id = f"RES-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"
    base_charge = 50.00

    new_reservation = BarReservation(
        reservation_id=res_id,
        user_id=input_data.user_id,
        venue_id=input_data.venue_id,
        primary_guest_name=input_data.primary_guest_name,
        number_guests=input_data.number_guests,
        event_datetime=event_dt,
        credit_card_last_four=input_data.credit_card_last_four,
        is_vip_room=False,
        reservation_charge=base_charge,
        latest_refund_date_days=2,  # 48-hour policy
        status="Active",
    )

    # Add to the global shared database instance
    global_bar_reservations_db.add_reservation(new_reservation)

    return BookBarReservationOutputModel(
        status="success",
        message=f"Reservation successfully booked for {input_data.primary_guest_name}.",
        reservation_id=res_id,
        reservation_charge=base_charge,
    )
