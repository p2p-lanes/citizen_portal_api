"""Common schema definitions used across the API."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class PaginationMetadata(BaseModel):
    """
    Metadata for pagination results.

    Attributes:
        skip: The number of items to skip
        limit: The number of items per page
        total: The total number of items across all pages
    """

    skip: int
    limit: int
    total: int


class PaginatedResponse(BaseModel, Generic[T]):
    """
    A generic pagination response that can be used across all API endpoints that require pagination.

    Attributes:
        items: The list of items for the current page
        pagination: Information about the current page and total results
    """

    items: List[T]
    pagination: PaginationMetadata
