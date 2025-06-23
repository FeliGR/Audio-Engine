"""
API Response Module

This module provides standardized response formatting for the TTS Service API.
It ensures consistent response structure across all endpoints.
"""

from typing import Any, Dict, Optional


class ApiResponse:
    """
    Standardized API response formatter.

    This class provides static methods to create consistent response formats
    for success and error scenarios across the API.
    """

    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """
        Create a standardized success response.

        Args:
            data: The response data to include.
            message: Success message. Defaults to "Success".

        Returns:
            Dict containing the standardized success response.
        """
        response = {
            "success": True,
            "message": message,
        }
        if data is not None:
            response["data"] = data
        return response

    @staticmethod
    def error(
        message: str = "An error occurred",
        details: Optional[Any] = None,
        error_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.

        Args:
            message: Error message.
            details: Additional error details.
            error_code: Optional error code for categorization.

        Returns:
            Dict containing the standardized error response.
        """
        response = {
            "success": False,
            "message": message,
        }
        if details is not None:
            response["details"] = details
        if error_code is not None:
            response["error_code"] = error_code
        return response
