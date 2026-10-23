from t1_plus_plus.schema.general.cache import (
    GetCacheInputModel,
    GetCacheOutputModel,
    SaveCacheInputModel,
)
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

cache = {}
cache_summaries = {}
cache_prior_search_queries = {}


def get_results_from_cache(**kwargs: GetCacheInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to get items from the cache

    Examples:
    >>> # Usage Example:
    get_results_from_cache(key=previous_flights)

    >>> # Usage Example:
    get_results_from_cache(key=previous_hotels)

    >>> # Usage Example:
    get_results_from_cache(key=previous_restaurants)

    >>> # Usage Example:
    get_results_from_cache(key=previous_attractions)

    Returns:
        GetCacheOutputModel: Output object which contains the result of the cache query.
    """
    global cache
    input_key = GetCacheInputModel.model_validate(kwargs)
    return cache.get(input_key.key, None)


def save_to_cache(**kwargs: SaveCacheInputModel) -> None:
    """
    Description:
        Use this tool to get items from the cache

    Examples:
    >>> # Usage Example:
    save_to_cache(key="previous_flights", value=previous_flights)

    >>> # Usage Example:
    save_to_cache(key="previous_hotels", value=previous_hotels)

    >>> # Usage Example:
    save_to_cache(key="previous_restaurants", value="previous_restaurants")

    >>> # Usage Example:
    save_to_cache(key="previous_attractions", value="previous_attractions")
    """
    parameters = SaveCacheInputModel.model_validate(kwargs)
    cache[parameters.key] = parameters.value
    cache_summaries[parameters.key] = parameters.summary
    cache_prior_search_queries[parameters.key] = parameters.prior_search_query

    count = len(getattr(parameters.value, "search_results", []) or [])
    print(
        f"   💾 [CACHE SAVE] key='{parameters.key}' | items={count} | summary={parameters.summary!r} | prior_search_query={parameters.prior_search_query!r}"
    )


def reset_cache():
    global cache, cache_summaries, cache_prior_search_queries
    cache = {}
    cache_summaries = {}
    cache_prior_search_queries = {}


def dump_entire_cache():
    global cache
    return cache


def dump_cache_query():
    global cache
    # Since python 3.7 dict is by default ordereddict
    try:
        return {k: v.query_summary for k, v in cache.items()}
    except Exception as e:
        for k, v in cache.items():
            print(k)
            print(v)
        print("unable to dump data")


def get_cache_for_current_turn():
    global cache, cache_summaries, cache_prior_search_queries
    # Since python 3.7 dict is by default ordereddict
    result = {}
    for k, v in cache.items():
        count = len(getattr(v, "search_results", []) or [])
        summary = cache_summaries.get(k) or getattr(v, "query_summary", None)
        prior_search_query = cache_prior_search_queries.get(k)
        result[k] = {"items": count, "summary": summary, "prior_search_query": prior_search_query}
    return result


def get_cache(arg1):
    return {k: v.query_summary for k, v in arg1.items()}


def retrieve_ground_truth_cache(row):
    global cache
    cache = row["entire_cache_before_current_turn"]

    return cache
