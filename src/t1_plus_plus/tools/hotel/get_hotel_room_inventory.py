from datetime import datetime
import pandas as pd
from pathlib import Path
from typing import List

from t1_plus_plus.schema.hotel.hotel_reservation import (
    GetHotelRoomInventoryInputModel,
    GetHotelRoomInventoryOutputModel,
    HotelRoomItem,
)

# 1. Configuration: Load data source paths
current_dir = Path(__file__).resolve().parent
data_dir = current_dir.parent.parent.parent.parent / "datasets"
ALL_HOTELS = str(data_dir / "data_hotel.csv")
ALL_HOTEL_ROOMS = str(data_dir / "data_hotel_rooms.csv")


try:
    hotels_df = pd.read_csv(ALL_HOTELS)
    hotel_rooms_df = pd.read_csv(ALL_HOTEL_ROOMS)
except FileNotFoundError:
    # Initialize empty dataframes if files are missing to prevent crashes
    hotels_df = pd.DataFrame()
    hotel_rooms_df = pd.DataFrame()


def get_hotel_room_inventory(**kwargs: GetHotelRoomInventoryInputModel) -> GetHotelRoomInventoryOutputModel:
    """
    Description:
        Retrieves the available room inventory for a specific hotel location.
        Validates the hotel_id exists, then fetches all rooms associated with that hotel 
        that match the optional occupancy requirement and are currently 'Available'.

    Examples:
    >>> # Usage Example: Fetching all available rooms for a specific hotel
    get_hotel_room_inventory(hotel_id="hotel_101")

    >>> # Usage Example: Fetching available rooms for a specific hotel that fit an occupancy of 4
    get_hotel_room_inventory(hotel_id="hotel_101", occupancy=4)

    Returns:
        GetHotelRoomInventoryOutputModel: Output object containing the status of the operation, a descriptive message, the name of the hotel, and a list of available rooms.
    """
    # 1. Validate Input
    try:
        input_data = GetHotelRoomInventoryInputModel.model_validate(kwargs)
    except Exception as e:
        return GetHotelRoomInventoryOutputModel(
            status="error",
            message=f"Invalid input parameters: {str(e)}",
        )

    # 2. Step One: Verify the Hotel exists
    if hotels_df.empty:
        return GetHotelRoomInventoryOutputModel(
            status="error",
            message="Hotel database is empty or unavailable.",
        )

    hotel_row = hotels_df[hotels_df["hotel_id"] == input_data.hotel_id]

    if hotel_row.empty:
        return GetHotelRoomInventoryOutputModel(
            status="error",
            message=f"No hotel found with ID: {input_data.hotel_id}",
        )

    hotel_name = hotel_row.iloc[0]["hotel_name"]

    # 3. Step Two: Filter the Room Inventory
    if hotel_rooms_df.empty:
        return GetHotelRoomInventoryOutputModel(
            status="error",
            message="Room inventory database is currently unavailable.",
        )

    check_in = datetime.strptime(input_data.check_in_date, "%Y-%m-%d")
    check_out = datetime.strptime(input_data.check_out_date, "%Y-%m-%d")

    # Support both old (status-based) and new (date-window-based) CSV formats.
    if "available_from" in hotel_rooms_df.columns and "available_until" in hotel_rooms_df.columns:
        # New format: room row is available if the requested stay fits within the window.
        avail_from = pd.to_datetime(hotel_rooms_df["available_from"], errors="coerce")
        avail_until = pd.to_datetime(hotel_rooms_df["available_until"], errors="coerce")
        mask = (
            (hotel_rooms_df["hotel_id"] == input_data.hotel_id)
            & (avail_from <= check_in)
            & (avail_until >= check_out)
        )
    else:
        # Legacy format: fall back to static status column.
        mask = (hotel_rooms_df["hotel_id"] == input_data.hotel_id) & \
               (hotel_rooms_df["status"].str.lower() == "available")
    
    if input_data.occupancy:
        mask &= (hotel_rooms_df["occupancy"] >= input_data.occupancy)

    available_rooms = hotel_rooms_df[mask]

    if available_rooms.empty:
        return GetHotelRoomInventoryOutputModel(
            status="success",
            message=f"No available rooms found at {hotel_name} for the requested criteria.",
            hotel_name=hotel_name,
            rooms=[],
        )

    # 4. Data Processing: Convert CSV rows to Schema objects
    parsed_rooms = []
    for _, row in available_rooms.iterrows():
        # New date-window format has no status column; report "Available" for any matched row.
        status_val = str(row["status"]) if "status" in row.index else "Available"
        parsed_rooms.append(
            HotelRoomItem(
                room_id=str(row["room_id"]),
                room_type=str(row["room_type"]),
                view_type=str(row["view_type"]),
                occupancy=int(row["occupancy"]),
                cash_price=float(row["cash_price"]),
                points_price=int(row["points_price"]),
                resort_fees=float(row["resort_fees"]),
                price_tier=str(row["price_tier"]),
                status=status_val,
            )
        )

    # 5. Return the finalized inventory
    return GetHotelRoomInventoryOutputModel(
        status="success",
        message=f"Successfully retrieved available room inventory for {hotel_name}.",
        hotel_name=hotel_name,
        rooms=parsed_rooms,
    )