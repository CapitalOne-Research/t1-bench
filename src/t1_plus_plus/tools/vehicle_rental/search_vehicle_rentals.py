import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.vehicle_rental.search_vehicle_rentals import SearchRentalsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
# Load the CSV
CSV_PATH = str(_data_dir / "data_rental_vehicles.csv")
try:
    all_rentals_df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    all_rentals_df = pd.DataFrame()


def summarize_rental_query(search_input_filtered):
    result = []

    # Core Location
    if "city" in search_input_filtered:
        result.append(
            "Rental search results in {},".format(search_input_filtered["city"])
        )

    # Identifiers
    if "vehicle_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["vehicle_id"])
        result.append("with ID(s) [{}],".format(ids))

    if "make" in search_input_filtered:
        makes = ", ".join(search_input_filtered["make"])
        result.append("for make(s) [{}],".format(makes))

    if "model" in search_input_filtered:
        models = ", ".join(search_input_filtered["model"])
        result.append("for model(s) [{}],".format(models))

    if "year" in search_input_filtered:
        years = ", ".join(map(str, search_input_filtered["year"]))
        result.append("from year(s) [{}],".format(years))

    if "category" in search_input_filtered:
        result.append("category {},".format(search_input_filtered["category"]))

    if "subcategory" in search_input_filtered:
        result.append("subcategory {},".format(search_input_filtered["subcategory"]))

    if "price_tier" in search_input_filtered:
        result.append("price tier {},".format(search_input_filtered["price_tier"]))

    # Numeric Ranges & Constraints
    if "rating" in search_input_filtered:
        r = search_input_filtered["rating"]
        result.append("rating between {} and {},".format(r[0], r[1]))

    if "base_price_per_day" in search_input_filtered:
        result.append(
            "base price up to ${},".format(search_input_filtered["base_price_per_day"])
        )

    if "odometer" in search_input_filtered:
        result.append("odometer under {},".format(search_input_filtered["odometer"]))

    if "seats" in search_input_filtered:
        result.append("minimum {} seats,".format(search_input_filtered["seats"]))

    if "fuel_type" in search_input_filtered:
        result.append("fuel type {},".format(search_input_filtered["fuel_type"]))

    # Collect and format boolean features (has_gps, is_automatic, etc.)
    features = [
        k
        for k, v in search_input_filtered.items()
        if (k.startswith("has_") or k.startswith("is_")) and v is True
    ]
    if features:
        feature_names = ", ".join(
            [
                f.replace("has_", "").replace("is_", "").replace("_", " ")
                for f in features
            ]
        )
        result.append("with features: [{}],".format(feature_names))

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_vehicle_rentals(**kwargs) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for rental vehicles based on criteria such as city,
        make, model, year, category, price tier, and various features
        (like GPS, automatic transmission, pet-friendly, etc.). Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_vehicle_rentals(city="New York", category="car", price_tier="budget", is_automatic=True)

    >>> # Usage Example:
    search_vehicle_rentals(city="Los Angeles", make=["Toyota", "Honda"], rating=[4.0, 5.0], is_pet_friendly=True)

    >>> # Usage Example:
    search_vehicle_rentals(city="Chicago", fuel_type="electric", seats=5, has_gps=True, has_unlimited_mileage=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting rental vehicles as well as the summary.
    """
    try:
        search_input = SearchRentalsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_rentals_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_rentals_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "city":
            mask &= all_rentals_df["city"].str.lower() == search_query_parameters.lower()

        elif col == "make":
            mask &= all_rentals_df["make"].isin(search_query_parameters)

        elif col == "model":
            mask &= all_rentals_df["model"].isin(search_query_parameters)

        elif col == "vehicle_id":
            # Map input 'vehicle_id' to dataframe 'id'
            mask &= all_rentals_df["id"].isin(search_query_parameters)

        elif col == "year":
            mask &= all_rentals_df["year"].isin(search_query_parameters)

        elif col == "category":
            mask &= all_rentals_df["category"] == search_query_parameters

        elif col == "subcategory":
            mask &= all_rentals_df["subcategory"] == search_query_parameters

        elif col == "price_tier":
            mask &= all_rentals_df["price_tier"] == search_query_parameters

        elif col == "base_price_per_day":
            mask &= all_rentals_df["base_price_per_day"] <= search_query_parameters

        elif col == "odometer":
            mask &= all_rentals_df["odometer"] <= search_query_parameters

        elif col == "seats":
            mask &= all_rentals_df["seats"] >= search_query_parameters

        elif col == "fuel_type":
            mask &= all_rentals_df["fuel_type"] == search_query_parameters

        elif col == "rating":
            mask &= (all_rentals_df["rating"] >= search_query_parameters[0]) & (
                all_rentals_df["rating"] <= search_query_parameters[1]
            )

        # Dynamic Boolean Flags (handles all has_gps, is_automatic, is_pet_friendly, etc.)
        elif col.startswith("has_") or col.startswith("is_"):
            if col in all_rentals_df.columns:
                mask &= all_rentals_df[col] == search_query_parameters

    resulting_rentals = (all_rentals_df[mask]).to_dict(orient="records")
    summarized_query = summarize_rental_query(search_input_filtered)

    if len(resulting_rentals) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_rentals,
            query_summary=f"{summarized_query}\nThere are 0 vehicle(s) that matched this query!",
        )

    top_10 = resulting_rentals[:10]

    extracted_results = [
        {
            "vehicle_id": item.get(
                "id"
            ),  # <-- FIXED: Pull from 'id' to populate 'vehicle_id'
            "make": item.get("make"),
            "model": item.get("model"),
            "year": item.get("year"),
            "city": item.get("city"),
            "category": item.get("category"),
            "price_tier": item.get("price_tier"),
            "base_price_per_day": item.get("base_price_per_day"),
            "rating": item.get("rating"),
        }
        for item in top_10
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{summarized_query}\nThere are {len(extracted_results)} vehicle(s) that matched this query!",
    )
