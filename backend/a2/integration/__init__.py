"""
Data integration layer and provider interfaces for Person A2.
"""

from backend.a2.integration.data_provider import DataProvider, MockDataProvider

__all__ = ["DataProvider", "MockDataProvider"]
