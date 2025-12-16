import requests
import json
from typing import Optional, Dict, Any, Union

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token = None
        # User info can be stored here if needed
        self.user = None

    def set_token(self, token: str):
        self.token = token

    def get_headers(self, content_type: Optional[str] = "application/json") -> Dict[str, str]:
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def check_connection(self) -> bool:
        """Checks if the backend API is reachable."""
        try:
            requests.get(f"{self.base_url}/", timeout=5)
            # Even 404 or 401 means it's reachable
            return True
        except requests.RequestException:
            return False

    def login(self, email, password) -> Optional[Dict[str, Any]]:
        """Authenticates the user and returns the token data."""
        url = f"{self.base_url}/auth/login"
        data = {"email": email, "password": password}
        try:
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                token_data = response.json()
                self.set_token(token_data.get("access_token"))
                return token_data
            else:
                # Log or handle login failure
                return None
        except requests.RequestException:
            return None

    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handles API response, raising exceptions for errors and returning JSON for success.
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            # Try to get more specific error message from the API response
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "detail" in error_data:
                    # Raise a custom exception or just include the detail in the error message
                    raise Exception(f"API Error: {error_data['detail']}")
                else:
                    raise e
            except ValueError:
                # If response is not JSON, raise the original HTTPError
                raise e
        except Exception as e:
            raise e

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, params=params, headers=self.get_headers())
            return self._handle_response(response)
        except Exception as e:
            # In a real app, might want to re-raise or return an error object
            raise e

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(url, json=data, headers=self.get_headers())
            return self._handle_response(response)
        except Exception as e:
            raise e

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.put(url, json=data, headers=self.get_headers())
            return self._handle_response(response)
        except Exception as e:
            raise e

    def delete(self, endpoint: str) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.delete(url, headers=self.get_headers())
            return self._handle_response(response)
        except Exception as e:
            raise e

    def upload_file(self, endpoint: str, file_obj, extra_data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        # For file upload, Content-Type header should not be set manually (requests does it)
        headers = self.get_headers(content_type=None)
        files = {"file": file_obj}
        try:
            response = requests.post(url, files=files, data=extra_data, headers=headers)
            return self._handle_response(response)
        except Exception as e:
            raise e