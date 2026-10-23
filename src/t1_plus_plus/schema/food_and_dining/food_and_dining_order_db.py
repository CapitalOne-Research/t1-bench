from typing import Dict, Optional
from pydantic import BaseModel


class PickupOrder(BaseModel):
    order_id: str
    user_id: str
    restaurant_id: str
    items: list
    payment_methods: list
    promo_code: Optional[str] = None
    total: float
    status: str


class PickupOrderDB:
    def __init__(self):
        self.orders: Dict[str, PickupOrder] = {}

    def add_order(self, order: PickupOrder) -> None:
        self.orders[order.order_id] = order

    def get_order(self, order_id: str) -> Optional[PickupOrder]:
        return self.orders.get(order_id)

    def delete_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        order = self.orders.get(order_id)
        if order:
            order.status = new_status
            return True
        return False

    def update_order(self, order_id: str, **fields) -> bool:
        order = self.orders.get(order_id)
        if order:
            for k, v in fields.items():
                setattr(order, k, v)
            return True
        return False


global_pickup_orders_db = PickupOrderDB()


class Reservation(BaseModel):
    reservation_id: str
    user_id: str
    restaurant_id: str
    primary_guest_name: str
    number_guests: int
    price_per_person: float
    reservation_date: str
    reservation_time: str
    has_private_dining: bool
    reservation_charge: float
    status: str


class ReservationDB:
    def __init__(self):
        self.reservations: Dict[str, Reservation] = {}

    def add_reservation(self, reservation: Reservation) -> None:
        self.reservations[reservation.reservation_id] = reservation

    def get_reservation(self, reservation_id: str) -> Optional[Reservation]:
        return self.reservations.get(reservation_id)

    def update_status(self, reservation_id: str, new_status: str) -> bool:
        res = self.reservations.get(reservation_id)
        if res:
            res.status = new_status
            return True
        return False

    def update_reservation(self, reservation_id: str, **fields) -> bool:
        res = self.reservations.get(reservation_id)
        if res:
            for k, v in fields.items():
                setattr(res, k, v)
            return True
        return False


global_reservations_db = ReservationDB()


class DeliveryOrder(BaseModel):
    order_id: str
    user_id: str
    restaurant_id: str
    delivery_address: str
    items: list
    special_instructions: Optional[str] = None
    payment_methods: list
    promo_code: Optional[str] = None
    total: float
    status: str


class DeliveryOrderDB:
    def __init__(self):
        self.orders: Dict[str, DeliveryOrder] = {}

    def add_order(self, order: DeliveryOrder) -> None:
        self.orders[order.order_id] = order

    def get_order(self, order_id: str) -> Optional[DeliveryOrder]:
        return self.orders.get(order_id)

    def delete_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        order = self.orders.get(order_id)
        if order:
            order.status = new_status
            return True
        return False

    def update_order(self, order_id: str, **fields) -> bool:
        order = self.orders.get(order_id)
        if order:
            for k, v in fields.items():
                setattr(order, k, v)
            return True
        return False


global_delivery_orders_db = DeliveryOrderDB()
