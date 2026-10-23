from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.schema.cruise.search_cruises import SearchCruisesInputModel

class FilterCruisesInputModel(SearchCruisesInputModel):
    cache_key: str = Field(
        ..., description="The cache key from a previous search_cruises call (e.g. 'search_cruises_results_0')."
    )
    model_config = ConfigDict(extra="forbid")
