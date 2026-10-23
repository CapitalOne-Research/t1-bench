from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.hotel.hotel_reservation import (
    CancelHotelReservationInputModel,
    CancelHotelReservationOutputModel,
)
from t1_plus_plus.schema.hotel.hotel_reservation_db import global_hotel_reservations_db

# Load Rooms CSV to check the Price Tier ($ = Non-refundable)
_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_ROOMS = str(_data_dir / "data_hotel_rooms.csv")

try:
    hotel_rooms_df = pd.read_csv(CSV_ROOMS)
except FileNotFoundError:
    hotel_rooms_df = pd.DataFrame()


def cancel_hotel_reservation(
    **kwargs: CancelHotelReservationInputModel,
) -> CancelHotelReservationOutputModel:
    """
    Description:
        Cancels a hotel reservation. Applies the 48-hour cancellation policy:
        - Full refund if >= 48 hours before check-in.
        - One night's stay fee if < 48 hours.
        - 100% fee if the room belongs to the Non-Refundable ($) price tier.

    Examples:
    >>> # Usage Example: Canceling a standard reservation
    cancel_hotel_reservation(user_id="user_123", reservation_id="RES-A1B2C3D4")

    >>> # Usage Example: Canceling another user's reservation
    cancel_hotel_reservation(user_id="user_456", reservation_id="RES-E5F6G7H8")

    Returns:
        CancelHotelReservationOutputModel: Output object containing the status of the cancellation, a descriptive message, the resulting refund status, and the fee charged (if any).
    """
    input_data = CancelHotelReservationInputModel.model_validate(kwargs)

    # 1. Retrieve from global db
    res = global_hotel_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return CancelHotelReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return CancelHotelReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status == "Cancelled":
        return CancelHotelReservationOutputModel(
            status="error", message="Reservation is already cancelled."
        )

    # 2. Check for Non-Refundable Price Tier ($)
    is_non_refundable = False
    one_night_rate = 0.0
    
    if not hotel_rooms_df.empty and res.room_id in hotel_rooms_df["room_id"].values:
        room = hotel_rooms_df[hotel_rooms_df["room_id"] == res.room_id].iloc[0]
        # Policy: Price Tier "$" receive no refund
        if str(room.get("price_tier", "")) == "$":
            is_non_refundable = True
        
        # Determine the "one night's stay" fee (Cash or Points)
        if "reward_points" in str(res.payment_method).lower():
            one_night_rate = float(room.get("points_price", 0))
        else:
            one_night_rate = float(room.get("cash_price", 0))

    # 3. Apply Cancellation Logic
    # Check-in is 3:00 PM (15:00) local time on the check_in_date
    check_in_dt = datetime.strptime(f"{res.check_in_date} 15:00", "%Y-%m-%d %H:%M")
    time_until_checkin = check_in_dt - datetime.now()
    cutoff_timedelta = timedelta(hours=48)

    if is_non_refundable:
        refund_status = "Non-Refundable Tier - No Refund"
        fee_charged = res.total  # Charge the full stay amount
    elif time_until_checkin < cutoff_timedelta:
        refund_status = "Late Cancellation Fee Applied"
        fee_charged = one_night_rate # Fee is "one night's stay"
    else:
        refund_status = "Full Refund"
        fee_charged = 0.0

    # 4. Update status and save
    res.status = "Cancelled"
    global_hotel_reservations_db.add_reservation(res)

    return CancelHotelReservationOutputModel(
        status="success",
        message=f"Reservation {res.reservation_id} successfully cancelled.",
        refund_status=refund_status,
        fee_charged=fee_charged
    )