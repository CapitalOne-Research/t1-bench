from typing import Dict, Optional
from pydantic import BaseModel, Field

class ToolOutputCache(BaseModel):
    """An in-memory cache to store Pydantic models returned from tool outputs."""
    
    storage: Dict[str, BaseModel] = Field(
        default_factory=dict,
        description="A dictionary mapping string keys to Pydantic model instances.",
    )

    def update_cache(self, key: str, value: BaseModel) -> None:
        """Updates the cache with a new key-value pair."""
        self.storage[key] = value

    def retrieve_cache(self, key: str) -> Optional[BaseModel]:
        """Retrieves a Pydantic model from the cache by its key."""
        return self.storage.get(key)