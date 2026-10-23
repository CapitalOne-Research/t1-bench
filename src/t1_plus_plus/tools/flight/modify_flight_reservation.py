from datetime import datetime
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.flight.flight_reservation import (
    ModifyFlightReservationInputModel,
    ModifyFlightReservationOutputModel,
)
from t1_plus_plus.schema.flight.flight_reservation_db import (
    global_flight_reservations_db,
)

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FLIGHTS = str(_data_dir / "data_flights.csv")
all_flights_df = (
    pd.read_csv(ALL_FLIGHTS) if Path(ALL_FLIGHTS).exists() else pd.DataFrame()
)


def modify_flight_reservation(
    **kwargs: ModifyFlightReservationInputModel,
) -> ModifyFlightReservationOutputModel:
    """
    Description:
        Modifies an existing flight reservation. Can update the departure date,
        number of passengers, departure city, arrival city, or passenger names, recalculating the total charge accordingly.

    Examples:
    >>> # Usage Example:
    modify_flight_reservation(user_id="user_123", reservation_id="RES-ABC12345", new_departure_date="2026-06-01")

    >>> # Usage Example:
    modify_flight_reservation(user_id="user_456", reservation_id="RES-DEF67890", new_number_passengers=3)

    >>> # Usage Example:
    modify_flight_reservation(user_id="user_789", reservation_id="RES-GHI11111", new_departure_date="2026-07-15", new_number_passengers=2)

    >>> # Usage Example:
    modify_flight_reservation(user_id="user_789", reservation_id="RES-GHI11111", departure_city="Los Angeles", arrival_city="New York")

    >>> # Usage Example:
    modify_flight_reservation(user_id="user_789", reservation_id="RES-GHI11111", passenger_names=["Alice Smith", "Bob Jones"], new_number_passengers=2)

    Returns:
        ModifyFlightReservationOutputModel: Output object containing modification status, reservation ID, and updated charge.
    """
    input_data = ModifyFlightReservationInputModel.model_validate(kwargs)
    res = global_flight_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return ModifyFlightReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return ModifyFlightReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status != "Active":
        return ModifyFlightReservationOutputModel(
            status="error",
            message="Cannot modify an inactive or cancelled reservation.",
        )

    # Look up the original flight to get the per-person price
    try:
        flight = all_flights_df[all_flights_df["flight_id"] == res.flight_id].iloc[0]
        price_per_person = float(flight["price"])
    except (IndexError, KeyError):
        return ModifyFlightReservationOutputModel(
            status="error",
            message=f"Could not retrieve flight details for flight ID '{res.flight_id}'.",
        )

    if input_data.new_departure_date:
        new_date = datetime.strptime(input_data.new_departure_date, "%Y-%m-%d")
        if new_date < datetime.now():
            return ModifyFlightReservationOutputModel(
                status="error",
                message="Cannot modify to a departure date that has already passed.",
            )
        res.departure_date = new_date

    if input_data.new_number_passengers:
        res.number_passengers = input_data.new_number_passengers

    if input_data.departure_city is not None:
        res.departure_city = input_data.departure_city

    if input_data.arrival_city is not None:
        res.arrival_city = input_data.arrival_city

    if input_data.passenger_names is not None:
        res.passenger_names = input_data.passenger_names

    res.reservation_charge = price_per_person * res.number_passengers

    global_flight_reservations_db.add_reservation(res)

    return ModifyFlightReservationOutputModel(
        status="success",
        message="Flight reservation successfully modified.",
        reservation_id=res.reservation_id,
        new_charge=res.reservation_charge,
    )
