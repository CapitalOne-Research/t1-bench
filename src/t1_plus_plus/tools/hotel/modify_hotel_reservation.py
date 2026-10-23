import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.hotel.hotel_reservation import (
    ModifyHotelReservationInputModel,
    ModifyHotelReservationOutputModel,
)
from t1_plus_plus.schema.hotel.hotel_reservation_db import global_hotel_reservations_db

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_ROOMS = str(_data_dir / "data_hotel_rooms.csv")

try:
    hotel_rooms_df = pd.read_csv(CSV_ROOMS)
except FileNotFoundError:
    hotel_rooms_df = pd.DataFrame()


def modify_hotel_reservation(
    **kwargs: ModifyHotelReservationInputModel,
) -> ModifyHotelReservationOutputModel:
    """
    Description:
        Modifies an existing hotel reservation. Allows updating check-in/check-out dates
        or switching to a different room (must belong to the same hotel). Recalculates the
        total charge based on the updated dates and/or room. The new room must be available
        for the full updated stay window.

    Examples:
    >>> # Usage Example: Change dates only
    modify_hotel_reservation(user_id="user_101", reservation_id="RES-A1B2C3D4", new_check_in_date="2026-06-01", new_check_out_date="2026-06-04")

    >>> # Usage Example: Switch to a different room
    modify_hotel_reservation(user_id="user_101", reservation_id="RES-A1B2C3D4", new_room_id="room_305")

    >>> # Usage Example: Change dates and switch room
    modify_hotel_reservation(user_id="user_101", reservation_id="RES-A1B2C3D4", new_check_in_date="2026-07-10", new_check_out_date="2026-07-13", new_room_id="room_306")

    Returns:
        ModifyHotelReservationOutputModel: Output object containing the modification status,
        updated reservation ID, new total charge, and currency type.
    """
    input_data = ModifyHotelReservationInputModel.model_validate(kwargs)

    # 1. Retrieve reservation
    res = global_hotel_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return ModifyHotelReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return ModifyHotelReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status != "Booked":
        return ModifyHotelReservationOutputModel(
            status="error",
            message="Cannot modify a cancelled or inactive reservation.",
        )

    # 2. Determine the effective check-in/check-out and room for the modification
    new_check_in = input_data.new_check_in_date or res.check_in_date
    new_check_out = input_data.new_check_out_date or res.check_out_date
    new_room_id = input_data.new_room_id or res.room_id

    check_in_dt = datetime.strptime(new_check_in, "%Y-%m-%d")
    check_out_dt = datetime.strptime(new_check_out, "%Y-%m-%d")
    nights = (check_out_dt - check_in_dt).days

    if nights <= 0:
        return ModifyHotelReservationOutputModel(
            status="error",
            message="Modification failed. Check-out date must be after the check-in date.",
        )

    # 3. Validate the room exists and belongs to the same hotel
    if hotel_rooms_df.empty or new_room_id not in hotel_rooms_df["room_id"].values:
        return ModifyHotelReservationOutputModel(
            status="error",
            message=f"Modification failed. Room ID {new_room_id} not found in inventory.",
        )

    room = hotel_rooms_df[hotel_rooms_df["room_id"] == new_room_id].iloc[0]

    if str(room.get("hotel_id", "")) != res.hotel_id:
        return ModifyHotelReservationOutputModel(
            status="error",
            message="Modification failed. The new room does not belong to the same hotel.",
        )

    # 4. Check availability of the (possibly new) room for the updated dates
    if (
        "available_from" in hotel_rooms_df.columns
        and "available_until" in hotel_rooms_df.columns
    ):
        avail_from = datetime.strptime(str(room["available_from"]), "%Y-%m-%d")
        avail_until = datetime.strptime(str(room["available_until"]), "%Y-%m-%d")
        is_available = avail_from <= check_in_dt and avail_until >= check_out_dt
    else:
        is_available = str(room.get("status", "")).lower() == "available"

    if not is_available:
        return ModifyHotelReservationOutputModel(
            status="error",
            message="Modification failed. The selected room is not available for the requested dates.",
        )

    # 5. Recalculate total
    payment_method = str(res.payment_method).strip().lower()

    if payment_method == "reward_points":
        currency_type = "points"
        new_total = float(room.get("points_price", 0)) * nights
    else:
        currency_type = "cash"
        base_cost = float(room.get("cash_price", 0)) * nights
        resort_fees_total = float(room.get("resort_fees", 0)) * nights
        new_total = base_cost + resort_fees_total

    # 6. Apply updates and save
    seed = f"{res.user_id}:{res.hotel_id}:{new_room_id}:{new_check_in}:{new_check_out}:{res.payment_method}"
    new_res_id = f"RES-{uuid.uuid5(uuid.NAMESPACE_DNS, seed).hex[:8].upper()}"

    res.reservation_id = new_res_id
    res.check_in_date = new_check_in
    res.check_out_date = new_check_out
    res.room_id = new_room_id
    res.total = new_total

    global_hotel_reservations_db.add_reservation(res)

    return ModifyHotelReservationOutputModel(
        status="success",
        message=f"Reservation successfully modified for {nights} night(s).",
        reservation_id=new_res_id,
        new_total=new_total,
        currency_type=currency_type,
    )
