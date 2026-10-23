from typing import Dict
from t1_plus_plus.schema.flight.flight_reservation import FlightReservation


class FlightReservationsDB:
    """In-memory database for flight reservations."""

    def __init__(self):
        self._reservations: Dict[str, FlightReservation] = {}

    @property
    def reservations(self) -> Dict[str, FlightReservation]:
        return self._reservations

    def add_reservation(self, reservation: FlightReservation) -> None:
        """Add or update a reservation in the database."""
        self._reservations[reservation.reservation_id] = reservation

    def get_reservation(self, reservation_id: str) -> FlightReservation:
        """Retrieve a reservation by ID."""
        return self._reservations.get(reservation_id)

    def remove_reservation(self, reservation_id: str) -> None:
        """Remove a reservation from the database."""
        if reservation_id in self._reservations:
            del self._reservations[reservation_id]


global_flight_reservations_db = FlightReservationsDB()
