import hashlib

import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.cafe.cafe_order import (
    CafeOrder,
    OrderItem,
    PlaceCafeOrderInputModel,
    PlaceCafeOrderOutputModel,
)
from t1_plus_plus.schema.cafe.cafe_order_db import global_cafe_orders_db

data_dir = Path(__file__).resolve().parents[4] / "datasets"

COFFEE_CSV = str(data_dir / "data_coffee_shop.csv")
BOBA_CSV = str(data_dir / "data_bubble_tea.csv")
MENU_CSV = str(data_dir / "data_cafe_menus.csv")

try:
    coffee_df = pd.read_csv(COFFEE_CSV)
    coffee_df["cafe_type"] = "Coffee Shop"
except FileNotFoundError:
    coffee_df = pd.DataFrame()

try:
    boba_df = pd.read_csv(BOBA_CSV)
    boba_df["cafe_type"] = "Bubble Tea"
except FileNotFoundError:
    boba_df = pd.DataFrame()

cafes_df = pd.concat([coffee_df, boba_df], ignore_index=True)

try:
    cafe_menus_df = pd.read_csv(MENU_CSV)
except FileNotFoundError:
    cafe_menus_df = pd.DataFrame()

TAX_RATE = 0.08875


def place_cafe_order(**kwargs: PlaceCafeOrderInputModel) -> PlaceCafeOrderOutputModel:
    """
    Description:
        Places a new order at a cafe. Validates items against the cafe's menu,
        calculates the total with promo codes and tax (8.875%), and stores the order.
    """
    try:
        input_data = PlaceCafeOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return PlaceCafeOrderOutputModel(status="error", message=f"Invalid input data: {str(e)}")

    # Verify cafe exists
    if cafes_df.empty or input_data.cafe_id not in cafes_df["id"].values:
        return PlaceCafeOrderOutputModel(
            status="error",
            message=f"Order failed. Cafe with ID {input_data.cafe_id} not found.",
        )

    venue = cafes_df[cafes_df["id"] == input_data.cafe_id].iloc[0]
    chain_name = venue["name"]

    # Get menu for this chain
    chain_menu = cafe_menus_df[cafe_menus_df["chain_name"] == chain_name]

    # Validate items and calculate totals
    subtotal = 0.0
    final_order_items = []

    for item_req in input_data.items:
        item_match = chain_menu[chain_menu["item_id"] == item_req.item_id]
        if item_match.empty:
            return PlaceCafeOrderOutputModel(
                status="error",
                message=f"Order failed. Item {item_req.item_id} is not available at {chain_name}.",
            )

        menu_item = item_match.iloc[0]
        unit_price = float(menu_item["base_price"])
        line_total = round(unit_price * item_req.quantity, 2)
        subtotal += line_total

        final_order_items.append(
            OrderItem(
                item_id=item_req.item_id,
                quantity=item_req.quantity,
                line_total=line_total,
            )
        )

    # Apply promo code
    discount = 0.0
    if input_data.promo_code:
        code = input_data.promo_code.upper()
        if code == "CAFE10":
            discount = round(subtotal * 0.10, 2)
        elif code == "CAFE5":
            discount = round(subtotal * 0.05, 2)
        else:
            return PlaceCafeOrderOutputModel(
                status="error",
                message=f"Order failed. Promo code '{input_data.promo_code}' is invalid.",
            )

    after_discount = round(subtotal - discount, 2)
    tax = round(after_discount * TAX_RATE, 2)
    final_total = round(after_discount + tax, 2)

    # Create order
    seed = f"{input_data.user_id}:{input_data.cafe_id}:{input_data.payment_method}"
    order_id = f"CAF-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"

    new_order = CafeOrder(
        order_id=order_id,
        user_id=input_data.user_id,
        cafe_id=input_data.cafe_id,
        items=final_order_items,
        payment_method=input_data.payment_method,
        promo_code=input_data.promo_code,
        subtotal=after_discount,
        tax=tax,
        total=final_total,
        status="Placed",
    )

    global_cafe_orders_db.add_order(new_order)

    return PlaceCafeOrderOutputModel(
        status="success",
        message=f"Cafe order placed successfully at {chain_name}. "
        f"Subtotal: ${after_discount:.2f}, Tax: ${tax:.2f}, Total: ${final_total:.2f}.",
        order_id=order_id,
        subtotal=after_discount,
        tax=tax,
        total_charged=final_total,
        order_status="Placed",
    )
