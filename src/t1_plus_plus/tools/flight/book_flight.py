import uuid
from datetime import datetime
from pathlib import Path
import pandas as pd

from t1_plus_plus.schema.flight.flight_reservation import (
    FlightReservation,
    BookFlightReservationInputModel,
    BookFlightReservationOutputModel,
)
from t1_plus_plus.schema.flight.flight_reservation_db import global_flight_reservations_db

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FLIGHTS = str(_data_dir / "data_flights.csv")
all_flights_df = pd.read_csv(ALL_FLIGHTS) if Path(ALL_FLIGHTS).exists() else pd.DataFrame()

def book_flight(**kwargs: BookFlightReservationInputModel) -> BookFlightReservationOutputModel:
    """
    Description:
        Books a new flight reservation. Validates flight availability,
        calculates total charge based on number of passengers, and stores the reservation details.

    Examples:
    >>> # Usage Example:
    book_flight(user_id="user_123", flight_id="FL-001", passenger_names=["Jane Doe"], number_passengers=1, credit_card_last_four="4242")

    >>> # Usage Example:
    book_flight(user_id="user_456", flight_id="FL-089", passenger_names=["John Smith", "Mary Smith"], number_passengers=2, credit_card_last_four="1234", departure_city="Los Angeles", arrival_city="New York")

    Returns:
        BookFlightReservationOutputModel: Output object containing booking status, reservation ID, and total charge.
    """
    input_data = BookFlightReservationInputModel.model_validate(kwargs)

    # Validate flight exists
    try:
        flight = all_flights_df[all_flights_df["flight_id"] == input_data.flight_id].iloc[0]
        departure_date = datetime.strptime(str(flight["departure_date"]), "%Y-%m-%d")
        price_per_person = float(flight["price"])
        airline = str(flight["airline"])
        departure_airport = str(flight["departure_airport"])
        arrival_airport = str(flight["arrival_airport"])
        ticket_class = str(flight["ticket_class"]) if "ticket_class" in flight and pd.notna(flight["ticket_class"]) else None
    except (IndexError, KeyError):
        return BookFlightReservationOutputModel(
            status="error",
            message=f"Booking failed. Flight ID '{input_data.flight_id}' not found.",
        )

    # Check if flight is in the past
    # if departure_date < datetime.now():
    #     return BookFlightReservationOutputModel(
    #         status="error",
    #         message=f"Booking failed. Cannot book a flight that has already departed.",
    #     )

    res_id = f"RES-{input_data.flight_id}"
    total_charge = price_per_person * input_data.number_passengers

    new_reservation = FlightReservation(
        reservation_id=res_id,
        user_id=input_data.user_id,
        flight_id=input_data.flight_id,
        passenger_names=input_data.passenger_names,
        number_passengers=input_data.number_passengers,
        departure_date=departure_date,
        departure_city=input_data.departure_city,
        arrival_city=input_data.arrival_city,
        ticket_class=ticket_class,
        credit_card_last_four=input_data.credit_card_last_four,
        reservation_charge=total_charge,
        latest_refund_date_days=7,  # 7-day refund policy for flights
        status="Active",
    )

    global_flight_reservations_db.add_reservation(new_reservation)

    return BookFlightReservationOutputModel(
        status="success",
        message=f"Flight reservation successfully booked for {', '.join(input_data.passenger_names)}. {airline} flight from {departure_airport} to {arrival_airport} on {departure_date.strftime('%Y-%m-%d')}.",
        reservation_id=res_id,
        reservation_charge=total_charge,
    )
