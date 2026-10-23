import pandas as pd
from pathlib import Path
from typing import Any

from t1_plus_plus.schema.live_show.get_live_show_details import (
    GetShowDetailsInputModel,
    GetShowDetailsOutputModel,
)

# Load the merged dataset
SHOWS_CSV = Path(__file__).resolve().parents[4] / "datasets" / "data_live_events.csv"

shows_df = pd.read_csv(SHOWS_CSV)


def get_live_show_details(**kwargs: GetShowDetailsInputModel) -> GetShowDetailsOutputModel:
    """
    Description:
        Use this tool to provide the user with comprehensive information about a specific live show, including descriptions, performers, venue details, show length, and full pricing/availability breakdowns for all seating sections. Either 'live_event_id' OR both 'venue_id' and 'show_name' MUST be provided.

    Examples:
    >>> # Usage Example:
    get_live_show_details(live_event_id="LE0")

    >>> # Usage Example:
    get_live_show_details(venue_id="venue_show_01", show_name="Jazz Night Live")

    Returns:
        GetShowDetailsOutputModel: Output object which contains the status, message, and detailed show information.
    """
    try:
        input_data = GetShowDetailsInputModel.model_validate(kwargs)
    except Exception as e:
        return GetShowDetailsOutputModel(
            status="error",
            message=f"Invalid input: {str(e)}"
        )

    # Filter for the specific show
    if input_data.live_event_id:
        target_show = shows_df[shows_df["live_event_id"] == input_data.live_event_id]
    elif input_data.venue_id and input_data.show_name:
        target_show = shows_df[
            (shows_df["Venue_ID"] == input_data.venue_id) &
            (shows_df["Show_Name"] == input_data.show_name)
        ]
    else:
        return GetShowDetailsOutputModel(
            status="error",
            message="Either 'live_event_id' or both 'venue_id' and 'show_name' must be provided."
        )

    if target_show.empty:
        return GetShowDetailsOutputModel(
            status="error",
            message=f"No show found matching the provided criteria."
        )

    show_row = target_show.iloc[0]

    # Construct the detailed response
    details = {
        "live_event_id": show_row["live_event_id"],
        "show_name": show_row["Show_Name"],
        "description": show_row["Description"],
        "performer": show_row["Performer"],
        "venue": {
            "name": show_row["Venue_Name"],
            "id": show_row["Venue_ID"],
            "city": show_row["City"],
            "neighborhood": show_row["Neighborhood"]
        },
        "event_date": str(show_row["Event_Date"]),
        "start_time": str(show_row["Start_Time"]),
        "show_length_mins": int(show_row["Show_Length_Mins"]),
        "intermission_mins": int(show_row["Intermission_Mins"]),
        "family_friendly": bool(show_row["Family_Friendly"]),
        "pricing": {
            "front": float(show_row["Front_Price_USD"]),
            "middle": float(show_row["Middle_Price_USD"]),
            "back": float(show_row["Back_Price_USD"])
        },
        "availability": {
            "front_seats": int(show_row["Front_Seats_Avail"]),
            "middle_seats": int(show_row["Middle_Seats_Avail"]),
            "back_seats": int(show_row["Back_Seats_Avail"])
        }
    }

    return GetShowDetailsOutputModel(
        status="success",
        message=f"Successfully retrieved details for '{input_data.show_name}'.",
        details=details
    )