import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.hotel.hotel_reservation import (
    BookHotelReservationInputModel,
    BookHotelReservationOutputModel,
    HotelReservation,
)
from t1_plus_plus.schema.hotel.hotel_reservation_db import global_hotel_reservations_db

# Load necessary CSVs to calculate pricing and check user balances
_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_ROOMS = str(_data_dir / "data_hotel_rooms.csv")
CSV_USERS = str(_data_dir / "data_combined_users.csv")

try:
    hotel_rooms_df = pd.read_csv(CSV_ROOMS)
    hotel_users_df = pd.read_csv(CSV_USERS)
except FileNotFoundError:
    hotel_rooms_df = pd.DataFrame()
    hotel_users_df = pd.DataFrame()


def book_hotel_reservation(
    **kwargs: BookHotelReservationInputModel,
) -> BookHotelReservationOutputModel:
    """
    Description:
        Books a new reservation at a hotel. Validates room availability, calculates
        the total stay cost (cash + resort fees OR points), verifies user point balances,
        and stores the reservation details.

    Examples:
    >>> # Usage Example: Booking a room using standard currency (e.g., credit card)
    book_hotel_reservation(user_id="user_101", hotel_id="hotel_202", room_id="room_303", check_in_date="2026-05-01", check_out_date="2026-05-04", payment_method="credit_card")

    >>> # Usage Example: Booking a room using reward points
    book_hotel_reservation(user_id="user_101", hotel_id="hotel_202", room_id="room_305", check_in_date="2026-06-10", check_out_date="2026-06-12", payment_method="reward_points")

    Returns:
        BookHotelReservationOutputModel: Output object containing the status of the booking, a descriptive message, the generated reservation ID, the total amount charged, and the currency type.
    """
    try:
        input_data = BookHotelReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return BookHotelReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    # 1. Calculate length of stay
    check_in = datetime.strptime(input_data.check_in_date, "%Y-%m-%d")
    check_out = datetime.strptime(input_data.check_out_date, "%Y-%m-%d")
    nights = (check_out - check_in).days

    if nights <= 0:
        return BookHotelReservationOutputModel(
            status="error",
            message="Booking failed. Check-out date must be after the check-in date.",
        )

    # 2. Fetch Room & Check Availability
    if (
        hotel_rooms_df.empty
        or input_data.room_id not in hotel_rooms_df["room_id"].values
    ):
        return BookHotelReservationOutputModel(
            status="error",
            message=f"Booking failed. Room ID {input_data.room_id} not found in inventory.",
        )

    room = hotel_rooms_df[hotel_rooms_df["room_id"] == input_data.room_id].iloc[0]

    # Support both date-window format (available_from/available_until) and
    # legacy static-status format.
    if (
        "available_from" in hotel_rooms_df.columns
        and "available_until" in hotel_rooms_df.columns
    ):
        check_in_dt = datetime.strptime(input_data.check_in_date, "%Y-%m-%d")
        check_out_dt = datetime.strptime(input_data.check_out_date, "%Y-%m-%d")
        avail_from = datetime.strptime(str(room["available_from"]), "%Y-%m-%d")
        avail_until = datetime.strptime(str(room["available_until"]), "%Y-%m-%d")
        is_available = avail_from <= check_in_dt and avail_until >= check_out_dt
    else:
        is_available = str(room.get("status", "")).lower() == "available"

    if not is_available:
        return BookHotelReservationOutputModel(
            status="error",
            message="Booking failed. The selected room is currently not available for booking.",
        )

    # 3. Calculate Totals & Validate Payment (EITHER Cash OR Points)
    payment_method = str(input_data.payment_method).strip().lower()

    if payment_method == "reward_points":
        currency_type = "points"
        total_charged = float(room.get("points_price", 0)) * nights

        # Verify user has enough points
        if (
            not hotel_users_df.empty
            and input_data.user_id in hotel_users_df["user_id"].values
        ):
            user = hotel_users_df[hotel_users_df["user_id"] == input_data.user_id].iloc[
                0
            ]
            points_str = str(user.get("reward_points_balance", "None"))

            if points_str == "None":
                return BookHotelReservationOutputModel(
                    status="error",
                    message="Booking failed. You do not have an active rewards account to use points.",
                )

            try:
                # Parse format like "Aura: 25000"
                balance = int(points_str.split(":")[1].strip())
                if balance < total_charged:
                    return BookHotelReservationOutputModel(
                        status="error",
                        message=f"Booking failed. Insufficient points. Total is {int(total_charged)} points, but your balance is {balance}.",
                    )
            except (IndexError, ValueError):
                pass  # Fail gracefully if data is malformed
    else:
        # Standard Currency (Credit Card, Crypto, etc.)
        currency_type = "cash"
        base_cost = float(room.get("cash_price", 0)) * nights
        resort_fees_total = float(room.get("resort_fees", 0)) * nights
        total_charged = base_cost + resort_fees_total

    # 4. Generate Reservation Record (deterministic: same inputs → same ID)
    seed = f"{input_data.user_id}:{input_data.hotel_id}:{input_data.room_id}:{input_data.check_in_date}:{input_data.check_out_date}:{input_data.payment_method}"
    res_id = f"RES-{uuid.uuid5(uuid.NAMESPACE_DNS, seed).hex[:8].upper()}"

    new_reservation = HotelReservation(
        reservation_id=res_id,
        user_id=input_data.user_id,
        hotel_id=input_data.hotel_id,
        room_id=input_data.room_id,
        check_in_date=input_data.check_in_date,
        check_out_date=input_data.check_out_date,
        payment_method=input_data.payment_method,
        total=total_charged,
        status="Booked",
    )

    # Add to the global shared database instance
    global_hotel_reservations_db.add_reservation(new_reservation)

    return BookHotelReservationOutputModel(
        status="success",
        message=f"Hotel reservation successfully booked for {nights} night(s).",
        reservation_id=res_id,
        total_charged=total_charged,
        currency_type=currency_type,
    )
