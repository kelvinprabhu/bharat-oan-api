from typing import Dict
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from app.config import settings

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
    reraise=True
)
async def send_telemetry(telemetry_data: Dict) -> Dict:
    """Background task to send telemetry events to the API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.telemetry_api_url,
            headers={
                "Accept": "*/*",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "dataType": "json"
            },
            json=telemetry_data,
            timeout=httpx.Timeout(30.0, read=60.0)
        )
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        } 