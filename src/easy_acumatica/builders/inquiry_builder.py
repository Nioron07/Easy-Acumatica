"""
InquiryBuilder and get_inquiry_results
--------------------------------------

This module provides a chainable builder for Acumatica generic-inquiry calls
and a client method to execute those inquiries via the contract-based REST API.

Classes:
    InquiryBuilder: Fluent builder for inquiry parameters and expands.

Functions:
    get_inquiry_results: Execute a PUT on a generic inquiry endpoint and return results.
"""
from typing import Any, Dict, List

__all__ = ["InquiryBuilder", "get_inquiry_results"]

class InquiryBuilder:
    """
    Fluent builder for generic inquiry calls.

    Allows setting request body parameters and $expand clauses in a chainable manner.

    Methods:
        param(field, value): Add or overwrite an inquiry parameter.
        expand(*entities): Specify detail entities to expand in the response.
        to_query_params(): Build the query-string dict (e.g. {'$expand': 'Results'}).
        to_body(): Build the JSON body dict for the inquiry parameters.
    """

    def __init__(self) -> None:
        self._parameters: Dict[str, Dict[str, Any]] = {}
        self._expand: List[str] = []

    def param(self, field: str, value: Any) -> "InquiryBuilder":
        """
        Add or overwrite an inquiry parameter in the request body.

        Args:
            field (str): Name of the inquiry parameter (e.g. "InventoryID").
            value (Any): Value to assign to the parameter.

        Returns:
            InquiryBuilder: self, to allow chaining.
        """
        self._parameters[field] = {"value": value}
        return self

    def expand(self, *entities: str) -> "InquiryBuilder":
        """
        Specify one or more detail entities to expand in the response.

        Args:
            *entities (str): Names of the detail entities to expand (e.g. "Results").

        Returns:
            InquiryBuilder: self, to allow chaining.
        """
        self._expand.extend(entities)
        return self

    def to_query_params(self) -> Dict[str, str]:
        """
        Build the query-string parameters for the PUT request.

        Returns:
            Dict[str, str]: e.g. {'$expand': 'Results,AnotherDetail'}.
        """
        qs: Dict[str, str] = {}
        if self._expand:
            qs["$expand"] = ",".join(self._expand)
        return qs

    def to_body(self) -> Dict[str, Dict[str, Any]]:
        """
        Build the JSON body payload for the PUT request.

        Returns:
            Dict[str, Dict[str, Any]]: Mapping of field names to {{'value': ...}}.

        Raises:
            ValueError: If no parameters have been set.
        """
        if not self._parameters:
            return {}
        return self._parameters