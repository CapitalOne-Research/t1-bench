from typing import Dict, Optional
from pydantic import BaseModel, Field
from t1_plus_plus.schema.cruise.cruise_reservation import CruiseReservation

class CruiseReservationDB(BaseModel):
    """An in-memory database for managing cruise reservations."""

    reservations: Dict[str, CruiseReservation] = Field(
        default_factory=dict,
        description="A dictionary mapping reservation IDs to CruiseReservation objects.",
    )

    def add_reservation(self, reservation: CruiseReservation) -> None:
        """Adds a new reservation to the database."""
        self.reservations[reservation.reservation_id] = reservation

    def get_reservation(self, reservation_id: str) -> Optional[CruiseReservation]:
        """Retrieves a reservation by its ID, returns None if not found."""
        return self.reservations.get(reservation_id)

    def delete_reservation(self, reservation_id: str) -> bool:
        """Deletes a reservation and returns True if successful."""
        if reservation_id in self.reservations:
            del self.reservations[reservation_id]
            return True
        return False

global_cruise_reservations_db = CruiseReservationDB()
