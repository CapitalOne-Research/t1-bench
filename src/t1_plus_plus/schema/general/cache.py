import json
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel


class GetCacheInputModel(BaseModel):
    key: str = Field(
        default=None,
        description="The input key",
    )
    prior_search_query: Optional[str] = Field(
        default=None,
        description="The original search query string that produced the cached results.",
    )
    model_config = ConfigDict(extra="forbid")


class SaveCacheInputModel(BaseModel):
    key: str = Field(
        default=None,
        description="The input key",
    )
    value: SearchResultsOutputModel = Field(
        default=None,
        description="The resulting value of the key to put into the cache.",
    )
    summary: str = Field(
        default=None,
        description="A human-readable summary of what is being saved to the cache.",
    )
    prior_search_query: Optional[str] = Field(
        default=None,
        description="The original search query string that produced the results being cached.",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator("value", mode="before")
    @classmethod
    def parse_value(cls, v):
        if isinstance(v, str):
            return SearchResultsOutputModel.model_validate(json.loads(v))
        if isinstance(v, BaseModel):
            return SearchResultsOutputModel.model_validate(v.model_dump())
        return v


class GetCacheOutputModel(BaseModel):
    result: SearchResultsOutputModel = Field(
        default=None, description="The result of the cache query."
    )
    model_config = ConfigDict(extra="forbid")
