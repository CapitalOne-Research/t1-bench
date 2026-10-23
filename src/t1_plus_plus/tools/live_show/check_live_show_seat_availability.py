import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.live_show.check_live_show_seat_availability import (
    CheckSeatAvailabilityInputModel,
    CheckSeatAvailabilityOutputModel,
)

SHOWS_CSV = Path(__file__).resolve().parents[4] / "datasets" / "data_live_events.csv"
shows_df = pd.read_csv(SHOWS_CSV)

SECTION_MAP = {
    "front": {"avail_col": "Front_Seats_Avail"},
    "middle": {"avail_col": "Middle_Seats_Avail"},
    "back": {"avail_col": "Back_Seats_Avail"},
}


def check_live_show_seat_availability(**kwargs) -> CheckSeatAvailabilityOutputModel:
    """
    Description:
        Check seat availability for a specific live show. Use this tool before booking or modifying a reservation to verify that the requested number of tickets is available in the desired section(s).
        If seat_location is not provided, returns availability for all sections.

    Examples:
    >>> # Usage Example: Check specific section
    check_live_show_seat_availability(live_event_id="LE294", seat_location=["front"], number_tickets=2)

    >>> # Usage Example: Check multiple sections
    check_live_show_seat_availability(live_event_id="LE50", seat_location=["front", "middle"], number_tickets=4)

    >>> # Usage Example: Check all sections
    check_live_show_seat_availability(live_event_id="LE100", number_tickets=6)

    Returns:
        CheckSeatAvailabilityOutputModel: status, message, and per-section availability details.
    """
    try:
        input_data = CheckSeatAvailabilityInputModel.model_validate(kwargs)
    except Exception as e:
        return CheckSeatAvailabilityOutputModel(
            status="error",
            message=f"Invalid input: {str(e)}"
        )

    target_show = shows_df[shows_df["live_event_id"] == input_data.live_event_id]
    if target_show.empty:
        return CheckSeatAvailabilityOutputModel(
            status="error",
            message=f"No show found with live_event_id '{input_data.live_event_id}'."
        )

    show_row = target_show.iloc[0]

    sections_to_check = input_data.seat_location if input_data.seat_location else list(SECTION_MAP.keys())

    for sec in sections_to_check:
        if sec not in SECTION_MAP:
            return CheckSeatAvailabilityOutputModel(
                status="error",
                message=f"Invalid seat_location '{sec}'. Must be 'front', 'middle', or 'back'."
            )

    sections = {}
    for sec in sections_to_check:
        cols = SECTION_MAP[sec]
        seats_remaining = int(show_row[cols["avail_col"]])
        available = seats_remaining >= input_data.number_tickets
        sections[sec] = {
            "available": available,
            "seats_remaining": seats_remaining,
        }

    all_available = any(s["available"] for s in sections.values())
    if all_available:
        message = f"Seats available for {input_data.number_tickets} ticket(s)."
    else:
        message = f"Insufficient seats for {input_data.number_tickets} ticket(s) in the requested section(s)."

    return CheckSeatAvailabilityOutputModel(
        status="success",
        message=message,
        sections=sections,
    )
