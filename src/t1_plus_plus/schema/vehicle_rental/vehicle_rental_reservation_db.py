from typing import Dict, Optional

from pydantic import BaseModel, Field

from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation import RentalReservation


class RentalReservationDB(BaseModel):
    """An in-memory database for managing vehicle rental reservations."""

    reservations: Dict[str, RentalReservation] = Field(
        default_factory=dict,
        description="A dictionary mapping reservation IDs to RentalReservation objects.",
    )

    def add_reservation(self, reservation: RentalReservation) -> None:
        """Adds a new rental reservation to the database."""
        self.reservations[reservation.reservation_id] = reservation

    def get_reservation(self, reservation_id: str) -> Optional[RentalReservation]:
        """Retrieves a reservation by its ID, returns None if not found."""
        return self.reservations.get(reservation_id)

    def delete_reservation(self, reservation_id: str) -> bool:
        """Deletes a reservation and returns True if successful."""
        if reservation_id in self.reservations:
            del self.reservations[reservation_id]
            return True
        return False


# Global instance to be imported by tools
global_rental_reservations_db = RentalReservationDB()
