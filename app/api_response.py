from typing import Any, Dict, Optional


class ApiResponse:
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
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
        response = {
            "success": False,
            "message": message,
        }
        if details is not None:
            response["details"] = details
        if error_code is not None:
            response["error_code"] = error_code
        return response
