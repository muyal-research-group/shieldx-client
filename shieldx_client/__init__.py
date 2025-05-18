import httpx
from typing import Optional, Dict
from shieldx_client.models import EventTypeId


class ShieldXClient:
    """
    Client for interacting with the ShieldX API, specifically for managing event types (`event-types`).

    This client supports asynchronous operations for creating and deleting event types using httpx.
    It also allows injecting additional custom headers (e.g., for tracing or extended authentication).
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize a new instance of the ShieldXClient.

        :param base_url: Base URL of the ShieldX API server (e.g., http://localhost:8000).
        :param token: Optional Bearer token for authentication. If provided, it will be included in request headers.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def create_event_type(self, event_type: str, headers: Dict[str, str] = {}) -> EventTypeId:
        """
        Create a new event type in the ShieldX system.

        :param event_type: The name or label of the event type to be created.
        :param headers: Optional dictionary of additional headers to include in the request.
        :return: The ID of the newly created event type.
        :raises httpx.HTTPStatusError: If the API returns an HTTP error response.
        """
        payload = {"event_type": event_type}
        __headers = {**self.headers, **headers}

        async with httpx.AsyncClient(headers=__headers) as client:
            response = await client.post(f"{self.base_url}/event-types", json=payload)
            response.raise_for_status()
            response_json = await response.json()
            return response_json.get("event_type_id", "")

    async def delete_event_type(self, event_type_id: str, headers: Dict[str, str] = {}) -> EventTypeId:
        """
        Delete an existing event type by its ID.

        :param event_type_id: The ID of the event type to be deleted.
        :param headers: Optional dictionary of additional headers to include in the request.
        :return: The ID of the deleted event type (as returned by the API).
        :raises httpx.HTTPStatusError: If the API returns an HTTP error response.
        """
        __headers = {**self.headers, **headers}
        async with httpx.AsyncClient(headers=__headers) as client:
            response = await client.delete(f"{self.base_url}/event-types/{event_type_id}")
            response.raise_for_status()
            response_json = await response.json()
            return response_json.get("event_type_id", "")
