from datetime import datetime
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.live_show.live_show_reservation import (
    BookLiveShowReservationInputModel,
    BookLiveShowReservationOutputModel,
    ShowReservation,
)

from t1_plus_plus.schema.live_show.live_show_reservation_db import global_show_reservations_db

# Load the merged dataset
SHOWS_CSV = Path(__file__).resolve().parents[4] / "datasets" / "data_live_events.csv"

shows_df = pd.read_csv(SHOWS_CSV)


def book_live_show_reservation(**kwargs: BookLiveShowReservationInputModel) -> BookLiveShowReservationOutputModel:
    """
    Description:
        Use this tool to book a new reservation for a live show. Validates seat availability in the requested section (front, middle, or back), calculates total price, and stores the reservation details.

    Examples:
    >>> # Usage Example:
    book_live_show_reservation(user_id="user_123", live_event_id="LE0", seat_location="middle", number_tickets=2, primary_guest_name="Jane Smith", credit_card_last_four="4242")

    >>> # Usage Example:
    book_live_show_reservation(user_id="user_456", live_event_id="LE12", seat_location="front", number_tickets=4, primary_guest_name="John Doe", credit_card_last_four="1234")

    Returns:
        BookLiveShowReservationOutputModel: Output object which contains the booking status, message, reservation ID, and total price.
    """
    # 1. Validate Input
    try:
        input_data = BookLiveShowReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return BookLiveShowReservationOutputModel(
            status="error",
            message=f"Booking failed. Validation error: {str(e)}",
        )

    # 2. Retrieve Show and Venue Data
    try:
        matching_shows = shows_df[shows_df["live_event_id"] == input_data.live_event_id]

        if matching_shows.empty:
            return BookLiveShowReservationOutputModel(
                status="error",
                message=f"Booking failed. No show found for live_event_id '{input_data.live_event_id}'.",
            )

        show = matching_shows.iloc[0]

        # 3. Seat Availability and Pricing Logic
        # Map seat_location to the specific column names in the dataset
        location = input_data.seat_location.lower()
        avail_col = f"{location.capitalize()}_Seats_Avail"
        price_col = f"{location.capitalize()}_Price_USD"

        if avail_col not in shows_df.columns or price_col not in shows_df.columns:
            return BookLiveShowReservationOutputModel(
                status="error",
                message=f"Booking failed. Seat section '{input_data.seat_location}' is not valid for this show.",
            )

        available_seats = show[avail_col]
        unit_price = show[price_col]

        # 4. Availability Check
        if input_data.number_tickets > available_seats:
            return BookLiveShowReservationOutputModel(
                status="error",
                message=f"Booking failed. Only {available_seats} seats are available in the {input_data.seat_location} section.",
            )

        # 5. Finalize Calculation and Metadata
        total_price = float(unit_price * input_data.number_tickets)
        event_dt = datetime.strptime(
            f"{show['Event_Date']} {show['Start_Time']}",
            "%Y-%m-%d %I:%M %p",
        )
        res_id = f"RES-{show['live_event_id']}"

        # Create Reservation Object
        new_reservation = ShowReservation(
            reservation_id=res_id,
            user_id=input_data.user_id,
            venue_id=show["Venue_ID"],
            show_name=show["Show_Name"],
            event_datetime=event_dt,
            seat_location=input_data.seat_location,
            number_tickets=input_data.number_tickets,
            primary_guest_name=input_data.primary_guest_name,
            total_price=total_price,
            credit_card_last_four=input_data.credit_card_last_four,
            latest_refund_date_days=2,  # Standard 48-hour refund policy
            status="Active",
        )

        # 6. Persist to Database
        global_show_reservations_db.add_reservation(new_reservation)

        # Note: In a production environment, we would also update the shows_df availability here.

        return BookLiveShowReservationOutputModel(
            status="success",
            message=f"Reservation successfully booked for '{show['Show_Name']}' at {show['Venue_ID']}.",
            reservation_id=res_id,
            total_price=total_price,
        )

    except Exception as e:
        return BookLiveShowReservationOutputModel(
            status="error",
            message=f"An unexpected error occurred during booking: {str(e)}",
        )