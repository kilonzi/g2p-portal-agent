import httpx
from typing import Any, Dict, Optional
from loguru import logger
from app.settings import settings

class G2PClient:
    """
    A unified HTTP client for the G2P Portal API.
    Maintains a single session for connection pooling.
    """
    _instance = None
    _client: Optional[httpx.AsyncClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(G2PClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            headers = {
                "Accept": "application/json",
            }
            # User explicitly requested NO API KEY for public Broad portal
            # if settings.G2P_PORTAL_API_KEY:
            #     headers["Authorization"] = f"Bearer {settings.G2P_PORTAL_API_KEY}"
            
            logger.info(f"Initializing G2P HTTP Client with base URL: {settings.G2P_PORTAL_API_URL}")
            cls._client = httpx.AsyncClient(
                base_url=settings.G2P_PORTAL_API_URL,
                headers=headers,
                timeout=30.0
            )
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
            logger.info("G2P HTTP Client closed.")

    @classmethod
    async def get(cls, endpoint: str, params: Dict[str, Any] = None) -> Any:
        client = await cls.get_client()
        try:
            logger.debug(f"GET {endpoint} params={params}")
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            # Smart parsing: return JSON if possible, else text
            try:
                return response.json()
            except ValueError:
                return response.text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code} for {endpoint}: {e.response.text}")
            return f"Error: API returned {e.response.status_code}"
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return f"Error: Request failed - {str(e)}"

    @classmethod
    async def post(cls, endpoint: str, json: Dict[str, Any] = None) -> Any:
        client = await cls.get_client()
        try:
            logger.debug(f"POST {endpoint}")
            response = await client.post(endpoint, json=json)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return f"Error: API returned {e.response.status_code}"
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return f"Error: Request failed - {str(e)}"
