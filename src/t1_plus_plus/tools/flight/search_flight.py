import pandas as pd
from pathlib import Path
from t1_plus_plus.schema.flight.search_flights import SearchFlightsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from src.t1_plus_plus.ontology.flights import CITY_TO_AIRPORTS

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_PATH = str(_data_dir / "data_flights.csv")
all_flights_df = pd.read_csv(CSV_PATH) if Path(CSV_PATH).exists() else pd.DataFrame()

def summarize_flight_query(search_input_filtered):
    """
    Description:
        Build a human-readable summary string from the active flight search filters.

    Examples:
    >>> # Usage Example:
    summarize_flight_query({"departure_airport": "LAX", "arrival_airport": "JFK", "departure_date": "2026-05-01"})

    Returns:
        str: A sentence summarising the applied search filters.
    """
    result = []

    if "departure_city" in search_input_filtered:
        result.append(f"Flight search results departing from '{search_input_filtered['departure_city']}',")
    elif "departure_airport" in search_input_filtered:
        result.append(f"Flight search results departing from '{search_input_filtered['departure_airport']}',")
    if "arrival_city" in search_input_filtered:
        result.append(f"arriving at '{search_input_filtered['arrival_city']}',")
    elif "arrival_airport" in search_input_filtered:
        result.append(f"arriving at '{search_input_filtered['arrival_airport']}',")
    if "departure_date" in search_input_filtered:
        result.append(f"on date {search_input_filtered['departure_date']},")
    if "arrival_date" in search_input_filtered:
        result.append(f"arriving on {search_input_filtered['arrival_date']},")
    if "airline" in search_input_filtered:
        airlines = ", ".join(search_input_filtered["airline"])
        result.append(f"with airlines [{airlines}],")
    if "price_max" in search_input_filtered:
        result.append(f"max price ${search_input_filtered['price_max']},")
    if "departure_time_after" in search_input_filtered:
        result.append(f"departing after {search_input_filtered['departure_time_after']},")
    if "departure_time_before" in search_input_filtered:
        result.append(f"departing before {search_input_filtered['departure_time_before']},")
    if "ticket_class" in search_input_filtered:
        result.append(f"ticket class '{search_input_filtered['ticket_class']}',")

    final_result = " ".join(result)
    return final_result.rstrip(",") + "."

def search_flight(**kwargs: SearchFlightsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Search for flights based on departure/arrival cities or airports, dates, airlines, time preferences, and price.

    Examples:
    >>> # Usage Example:
    search_flight(departure_city="Los Angeles", arrival_city="New York")

    >>> # Usage Example:
    search_flight(departure_airport="LAX", arrival_airport="JFK", departure_date="2026-05-01")

    >>> # Usage Example:
    search_flight(departure_airport="SFO", arrival_airport="ORD", airline=["AeroOne", "Skylo"], price_max=300.0)

    >>> # Usage Example:
    search_flight(departure_airport="BOS", arrival_airport="MIA", departure_date="2026-06-15", departure_time_after="08:00", departure_time_before="18:00")

    Returns:
        SearchResultsOutputModel: Output object containing the matching flights and a query summary.
    """
    search_input = SearchFlightsInputModel.model_validate(kwargs)
    search_input_filtered = {k: v for k, v in search_input.model_dump().items() if v is not None}

    mask = pd.Series(True, index=all_flights_df.index)

    for col, val in search_input_filtered.items():
        if col == "departure_city":
            airports = CITY_TO_AIRPORTS.get(val.lower(), [val.upper()])
            mask &= all_flights_df["departure_airport"].str.upper().isin([a.upper() for a in airports])
        elif col == "arrival_city":
            airports = CITY_TO_AIRPORTS.get(val.lower(), [val.upper()])
            mask &= all_flights_df["arrival_airport"].str.upper().isin([a.upper() for a in airports])
        elif col == "departure_airport":
            mask &= all_flights_df["departure_airport"].str.upper() == val.upper()
        elif col == "arrival_airport":
            mask &= all_flights_df["arrival_airport"].str.upper() == val.upper()
        elif col == "departure_date":
            mask &= all_flights_df["departure_date"] == val
        elif col == "arrival_date":
            mask &= all_flights_df["arrival_date"] == val
        elif col == "airline":
            mask &= all_flights_df["airline"].isin(val)
        elif col == "price_max":
            mask &= all_flights_df["price"] <= val
        elif col == "departure_time_after":
            mask &= all_flights_df["departure_time"] >= val
        elif col == "departure_time_before":
            mask &= all_flights_df["departure_time"] <= val
        elif col == "ticket_class":
            mask &= all_flights_df["ticket_class"].str.lower() == val.lower()

    resulting_flights = all_flights_df[mask].to_dict(orient="records")
    summarized_query = summarize_flight_query(search_input_filtered)

    return SearchResultsOutputModel(
        search_results=resulting_flights,
        query_summary=f"{summarized_query}\nThere are {len(resulting_flights)} flight(s) that matched this query!"
    )
