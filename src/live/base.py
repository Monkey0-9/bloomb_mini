from abc import ABC, abstractmethod
from typing import Any

class SeedProvider(ABC):
    """
    Base class for all intelligence seeds in SatTrade.
    Inspired by the Provider pattern in GodMode.
    """
    
    @abstractmethod
    async def fetch(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch raw data from the external source."""
        pass

    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process raw data into a format suitable for the swarm."""
        pass
