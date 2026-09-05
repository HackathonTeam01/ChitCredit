"""
Data integration layer and provider interfaces for Person A2.
"""

from backend.a2.integration.data_provider import (
    DataProvider,
    MockDataProvider,
    get_default_data_provider,
)
from backend.a2.integration.http_data_provider import HttpDataProvider

__all__ = [
    "DataProvider",
    "MockDataProvider",
    "HttpDataProvider",
    "get_default_data_provider",
]
