from datetime import datetime
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.live_show.live_show_reservation import (
    ModifyLiveShowReservationInputModel,
    ModifyLiveShowReservationOutputModel,
)

from t1_plus_plus.schema.live_show.live_show_reservation_db import global_show_reservations_db


# Load the merged dataset for availability validation
SHOWS_CSV = Path(__file__).resolve().parents[4] / "datasets" / "data_live_events.csv"
shows_df = pd.read_csv(SHOWS_CSV)


def modify_live_show_reservation(**kwargs: ModifyLiveShowReservationInputModel) -> ModifyLiveShowReservationOutputModel:
    """
    Description:
        Use this tool to modify an existing show reservation. Can update seat locations or ticket quantities. It validates the new requirements against the show's availability and recalculates the total price.

    Examples:
    >>> # Usage Example:
    modify_live_show_reservation(user_id="user_123", reservation_id="SHOW-A1B2C3D4", new_seat_location="front", new_number_tickets=3)

    >>> # Usage Example:
    modify_live_show_reservation(user_id="user_456", reservation_id="SHOW-E5F6G7H8", new_number_tickets=2)

    Returns:
        ModifyLiveShowReservationOutputModel: Output object which contains the modification status, message, reservation ID, and updated total price.
    """
    input_data = ModifyLiveShowReservationInputModel.model_validate(kwargs)

    # 1. Retrieve the reservation from the global database
    res = global_show_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return ModifyLiveShowReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    # 2. Ownership and Status Checks
    if res.user_id != input_data.user_id:
        return ModifyLiveShowReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status != "Active":
        return ModifyLiveShowReservationOutputModel(
            status="error",
            message="Cannot modify an inactive or cancelled reservation.",
        )

    # 3. Handle Proposed Changes
    # If seat location or number of tickets changes, we must validate availability
    if input_data.new_seat_location or input_data.new_number_tickets:
        # Find the specific show data
        show_mask = (shows_df["Venue_ID"] == res.venue_id) & (
            shows_df["Show_Name"] == res.show_name
        )
        matching_shows = shows_df[show_mask]

        if matching_shows.empty:
            return ModifyLiveShowReservationOutputModel(
                status="error",
                message="Modification failed. The associated show data is no longer available.",
            )

        show = matching_shows.iloc[0]
        
        # Determine updated values
        updated_location = input_data.new_seat_location or res.seat_location
        updated_tickets = input_data.new_number_tickets or res.number_tickets

        # Validate Seat Section Columns
        location_key = updated_location.lower()
        avail_col = f"{location_key.capitalize()}_Seats_Avail"
        price_col = f"{location_key.capitalize()}_Price_USD"

        if avail_col not in shows_df.columns or price_col not in shows_df.columns:
            return ModifyLiveShowReservationOutputModel(
                status="error",
                message=f"Invalid seat section: '{updated_location}'.",
            )

        # Check availability
        available_seats = show[avail_col]
        unit_price = show[price_col]

        if updated_tickets > available_seats:
            return ModifyLiveShowReservationOutputModel(
                status="error",
                message=f"Insufficient availability. Only {available_seats} seats left in the {updated_location} section.",
            )

        # Apply the updates
        res.seat_location = updated_location
        res.number_tickets = updated_tickets
        res.total_price = float(unit_price * updated_tickets)

    # 4. Save to the database
    global_show_reservations_db.add_reservation(res)

    return ModifyLiveShowReservationOutputModel(
        status="success",
        message="Reservation successfully modified.",
        reservation_id=res.reservation_id,
        new_total_price=res.total_price,
    )