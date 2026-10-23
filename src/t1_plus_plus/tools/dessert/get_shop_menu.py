import json

import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.dessert.dessert_order import (
    GetShopMenuInputModel,
    GetShopMenuOutputModel,
    DessertMenuItem,
)

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


def get_shop_menu(**kwargs: GetShopMenuInputModel) -> GetShopMenuOutputModel:
    """
    Description:
        Retrieves the menu for a specific dessert shop or bakery location.
        Looks up the shop name using the shop_id, then fetches the menu for that chain.
    """
    try:
        input_data = GetShopMenuInputModel.model_validate(kwargs)
    except Exception as e:
        return GetShopMenuOutputModel(status="error", message=f"Invalid input: {str(e)}")

    if shops_df.empty:
        return GetShopMenuOutputModel(status="error", message="Shop database is empty or unavailable.")

    location_row = shops_df[shops_df["id"] == input_data.shop_id]
    if location_row.empty:
        return GetShopMenuOutputModel(
            status="error", message=f"No shop found with ID: {input_data.shop_id}"
        )

    target_chain = location_row.iloc[0]["name"]
    shop_type = location_row.iloc[0]["shop_type"]

    if dessert_menus_df.empty:
        return GetShopMenuOutputModel(status="error", message="Menu database is currently unavailable.")

    chain_menu = dessert_menus_df[dessert_menus_df["chain_name"] == target_chain]
    if chain_menu.empty:
        return GetShopMenuOutputModel(
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
            DessertMenuItem(
                item_id=str(row["item_id"]),
                item_name=str(row["item_name"]),
                description=str(row["description"]),
                base_price=float(row["base_price"]),
                dietary_tags=dietary,
                allergens=allergens,
            )
        )

    return GetShopMenuOutputModel(
        status="success",
        message=f"Successfully retrieved menu for {target_chain}.",
        shop_name=target_chain,
        shop_type=shop_type,
        menu_items=parsed_items,
    )
