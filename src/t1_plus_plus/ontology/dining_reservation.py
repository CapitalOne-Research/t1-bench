from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reservation:
    """Represents a booked reservation."""

    reservation_id: str
    user_id: str
    venue_id: str
    primary_guest_name: str
    number_guests: int
    event_datetime: datetime
    credit_card_last_four: str
    is_vip_room: bool = False
    reservation_charge: float
    latest_refund_date_days: int
    status: str = "Active"
