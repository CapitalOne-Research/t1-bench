from typing import Dict, Optional
from pydantic import BaseModel, Field

class KayakReservation(BaseModel):
    """Represents a finalized kayak reservation."""
    booking_id: str = Field(..., description="Unique ID for the booking.")
    user_id: str = Field(..., description="ID of the user who made the booking.")
    rental_id: str = Field(..., description="ID of the rental location.")
    vessel_type: str = Field(..., description="The type of watercraft reserved.")
    date: str = Field(..., description="Reservation date (YYYY-MM-DD).")
    start_time: str = Field(..., description="Reservation start time (HH:MM).")
    duration: int = Field(..., description="Duration in hours.")
    total_cost: float = Field(..., description="Total calculated cost.")
    status: str = Field(default="Confirmed", description="Status of the reservation.")

class KayakReservationDB(BaseModel):
    """An in-memory database for managing kayak reservations."""
    reservations: Dict[str, KayakReservation] = Field(
        default_factory=dict,
        description="A dictionary mapping booking IDs to KayakReservation objects.",
    )

    def add_reservation(self, reservation: KayakReservation) -> None:
        """Adds a new reservation to the database."""
        self.reservations[reservation.booking_id] = reservation

    def get_reservation(self, booking_id: str) -> Optional[KayakReservation]:
        """Retrieves a reservation by its ID, returns None if not found."""
        return self.reservations.get(booking_id)

    def delete_reservation(self, booking_id: str) -> bool:
        """Deletes a reservation entirely and returns True if successful."""
        if booking_id in self.reservations:
            del self.reservations[booking_id]
            return True
        return False

    def update_reservation_status(self, booking_id: str, new_status: str) -> bool:
        """Updates the status of an existing reservation (e.g., 'Cancelled')."""
        if booking_id in self.reservations:
            self.reservations[booking_id].status = new_status
            return True
        return False

# Create the global instance to be imported by your tools
global_kayak_reservation_db = KayakReservationDB()