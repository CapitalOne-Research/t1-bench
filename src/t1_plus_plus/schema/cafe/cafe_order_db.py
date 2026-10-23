from typing import Dict, Optional

from pydantic import BaseModel, Field

from t1_plus_plus.schema.cafe.cafe_order import CafeOrder


class CafeOrderDB(BaseModel):
    """An in-memory database for managing cafe orders."""

    orders: Dict[str, CafeOrder] = Field(
        default_factory=dict,
        description="A dictionary mapping order IDs to CafeOrder objects.",
    )

    def add_order(self, order: CafeOrder) -> None:
        self.orders[order.order_id] = order

    def get_order(self, order_id: str) -> Optional[CafeOrder]:
        return self.orders.get(order_id)

    def delete_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = new_status
            return True
        return False


global_cafe_orders_db = CafeOrderDB()
