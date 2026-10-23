import json

import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.cafe.cafe_order import (
    GetCafeMenuInputModel,
    GetCafeMenuOutputModel,
    CafeMenuItem,
)

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


def get_cafe_menu(**kwargs: GetCafeMenuInputModel) -> GetCafeMenuOutputModel:
    """
    Description:
        Retrieves the menu for a specific cafe location.
        Looks up the cafe name using the cafe_id, then fetches the menu for that chain.
    """
    try:
        input_data = GetCafeMenuInputModel.model_validate(kwargs)
    except Exception as e:
        return GetCafeMenuOutputModel(status="error", message=f"Invalid input: {str(e)}")

    if cafes_df.empty:
        return GetCafeMenuOutputModel(status="error", message="Cafe database is empty or unavailable.")

    location_row = cafes_df[cafes_df["id"] == input_data.cafe_id]
    if location_row.empty:
        return GetCafeMenuOutputModel(
            status="error", message=f"No cafe found with ID: {input_data.cafe_id}"
        )

    target_chain = location_row.iloc[0]["name"]
    cafe_type = location_row.iloc[0]["cafe_type"]

    if cafe_menus_df.empty:
        return GetCafeMenuOutputModel(status="error", message="Menu database is currently unavailable.")

    chain_menu = cafe_menus_df[cafe_menus_df["chain_name"] == target_chain]
    if chain_menu.empty:
        return GetCafeMenuOutputModel(
            status="error", message=f"No menu data available for: {target_chain}."
        )

    parsed_items = []
    for _, row in chain_menu.iterrows():
        try:
            dietary = json.loads(row["dietary_tags"]) if pd.notna(row["dietary_tags"]) else []
        except Exception:
            dietary = []
        try:
            allergens = json.loads(row["allergens"]) if pd.notna(row["allergens"]) else []
        except Exception:
            allergens = []

        parsed_items.append(
            CafeMenuItem(
                item_id=str(row["item_id"]),
                item_name=str(row["item_name"]),
                description=str(row["description"]),
                base_price=float(row["base_price"]),
                dietary_tags=dietary,
                allergens=allergens,
            )
        )

    return GetCafeMenuOutputModel(
        status="success",
        message=f"Successfully retrieved menu for {target_chain}.",
        cafe_name=target_chain,
        cafe_type=cafe_type,
        menu_items=parsed_items,
    )
