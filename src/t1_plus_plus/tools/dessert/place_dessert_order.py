import hashlib

import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.dessert.dessert_order import (
    DessertOrder,
    OrderItem,
    PlaceDessertOrderInputModel,
    PlaceDessertOrderOutputModel,
)
from t1_plus_plus.schema.dessert.dessert_order_db import global_dessert_orders_db

current_dir = Path(__file__).resolve().parent
data_dir = current_dir.parent.parent.parent.parent / "datasets"

DESSERT_CSV = str(data_dir / "data_dessert_shop.csv")
BAKERY_CSV = str(data_dir / "data_bakery.csv")
MENU_CSV = str(data_dir / "data_dessert_menus.csv")

try:
    dessert_df = pd.read_csv(DESSERT_CSV)
    dessert_df["shop_type"] = "Dessert Shop"
except FileNotFoundError:
    dessert_df = pd.DataFrame()

try:
    bakery_df = pd.read_csv(BAKERY_CSV)
    bakery_df["shop_type"] = "Bakery"
except FileNotFoundError:
    bakery_df = pd.DataFrame()

shops_df = pd.concat([dessert_df, bakery_df], ignore_index=True)

try:
    dessert_menus_df = pd.read_csv(MENU_CSV)
except FileNotFoundError:
    dessert_menus_df = pd.DataFrame()

TAX_RATE = 0.08875


def place_dessert_order(**kwargs: PlaceDessertOrderInputModel) -> PlaceDessertOrderOutputModel:
    """
    Description:
        Places a standard pickup order at a dessert shop or bakery. Validates items
        against the shop's menu, calculates the total with promo codes and tax (8.875%),
        and stores the order.
    """
    try:
        input_data = PlaceDessertOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return PlaceDessertOrderOutputModel(status="error", message=f"Invalid input data: {str(e)}")

    # Verify shop exists
    if shops_df.empty or input_data.shop_id not in shops_df["id"].values:
        return PlaceDessertOrderOutputModel(
            status="error",
            message=f"Order failed. Shop with ID {input_data.shop_id} not found.",
        )

    venue = shops_df[shops_df["id"] == input_data.shop_id].iloc[0]
    chain_name = venue["name"]

    # Get menu for this chain
    chain_menu = dessert_menus_df[dessert_menus_df["chain_name"] == chain_name]

    # Validate items and calculate totals
    subtotal = 0.0
    final_order_items = []

    for item_req in input_data.items:
        item_match = chain_menu[chain_menu["item_id"] == item_req.item_id]
        if item_match.empty:
            return PlaceDessertOrderOutputModel(
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
        if code == "SWEET10":
            discount = round(subtotal * 0.10, 2)
        elif code == "SWEET5":
            discount = round(subtotal * 0.05, 2)
        else:
            return PlaceDessertOrderOutputModel(
                status="error",
                message=f"Order failed. Promo code '{input_data.promo_code}' is invalid.",
            )

    after_discount = round(subtotal - discount, 2)
    tax = round(after_discount * TAX_RATE, 2)
    final_total = round(after_discount + tax, 2)

    # Create order
    seed = f"{input_data.user_id}:{input_data.shop_id}:{input_data.payment_method}"
    order_id = f"DST-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"

    new_order = DessertOrder(
        order_id=order_id,
        user_id=input_data.user_id,
        shop_id=input_data.shop_id,
        order_type="Standard_Pickup",
        items=final_order_items,
        payment_method=input_data.payment_method,
        promo_code=input_data.promo_code,
        subtotal=after_discount,
        tax=tax,
        total=final_total,
        status="Placed",
    )

    global_dessert_orders_db.add_order(new_order)

    return PlaceDessertOrderOutputModel(
        status="success",
        message=f"Dessert order placed successfully at {chain_name}. "
        f"Subtotal: ${after_discount:.2f}, Tax: ${tax:.2f}, Total: ${final_total:.2f}.",
        order_id=order_id,
        subtotal=after_discount,
        tax=tax,
        total_charged=final_total,
        order_status="Placed",
    )
