import json
import os
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    GetFoodAndDiningMenuInputModel,
    GetFoodAndDiningMenuOutputModel,
    MenuItem,
)

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FOOD_AND_DINING = os.getenv("ALL_FOOD_AND_DINING", str(_data_dir / "data_food_and_dining.csv"))
ALL_FOOD_AND_DINING_MENUS = os.getenv(
    "ALL_FOOD_AND_DINING_MENUS", str(_data_dir / "data_food_and_dining_menus.csv")
)

try:
    food_and_dining_df = pd.read_csv(ALL_FOOD_AND_DINING)
    food_and_dining_menus_df = pd.read_csv(ALL_FOOD_AND_DINING_MENUS)
except FileNotFoundError:
    food_and_dining_df = pd.DataFrame()
    food_and_dining_menus_df = pd.DataFrame()


def get_food_and_dining_menu(**kwargs) -> GetFoodAndDiningMenuOutputModel:
    """
    Description:
        Retrieves the menu for a specific food and dining establishment by restaurant ID.

    Examples:
    >>> # Usage Example:
    get_food_and_dining_menu(restaurant_id="FAD-288417")

    Returns:
        GetFoodAndDiningMenuOutputModel: Restaurant name and list of menu items.
    """
    try:
        input_data = GetFoodAndDiningMenuInputModel.model_validate(kwargs)
    except Exception as e:
        return GetFoodAndDiningMenuOutputModel(
            status="error", message=f"Invalid input parameters: {str(e)}"
        )

    if food_and_dining_df.empty:
        return GetFoodAndDiningMenuOutputModel(
            status="error", message="Restaurant database is empty or unavailable."
        )

    location_row = food_and_dining_df[food_and_dining_df["id"] == input_data.restaurant_id]
    if location_row.empty:
        return GetFoodAndDiningMenuOutputModel(
            status="error",
            message=f"No establishment found with ID: {input_data.restaurant_id}",
        )

    row = location_row.iloc[0]
    restaurant_name = str(row["name"])

    if food_and_dining_menus_df.empty:
        return GetFoodAndDiningMenuOutputModel(
            status="error", message="Menu database is currently unavailable."
        )

    menu_rows = food_and_dining_menus_df[
        food_and_dining_menus_df["restaurant_id"] == input_data.restaurant_id
    ]

    if menu_rows.empty:
        return GetFoodAndDiningMenuOutputModel(
            status="error",
            message=f"No menu data available for establishment ID: {input_data.restaurant_id}",
        )

    items = []
    for _, item_row in menu_rows.iterrows():
        if "is_available" in item_row and str(item_row["is_available"]).lower() == "false":
            continue
        try:
            dietary = json.loads(item_row["dietary_tags"]) if pd.notna(item_row["dietary_tags"]) else []
        except Exception:
            dietary = []
        try:
            allergens = json.loads(item_row["allergens"]) if pd.notna(item_row["allergens"]) else []
        except Exception:
            allergens = []

        items.append(
            MenuItem(
                item_id=str(item_row["item_id"]),
                item_name=str(item_row["item_name"]),
                description=str(item_row["description"]),
                base_price=float(item_row["base_price"]),
                dietary_tags=dietary,
                allergens=allergens,
            )
        )

    return GetFoodAndDiningMenuOutputModel(
        status="success",
        message=f"Successfully retrieved menu for {restaurant_name}.",
        restaurant_name=restaurant_name,
        menu_items=items,
    )
