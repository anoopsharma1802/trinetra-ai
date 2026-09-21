import httpx
from ..core.config import settings
class VahanClient:
    async def lookup_vehicle(self,plate_number):
        if not settings.vahan_api_base_url: return {'plate_number':plate_number,'status':'integration_not_configured'}
        h={'Authorization':f'Bearer {settings.vahan_api_key}'} if settings.vahan_api_key else {}
        async with httpx.AsyncClient(timeout=10) as c:
            r=await c.get(f'{settings.vahan_api_base_url}/vehicles/{plate_number}',headers=h); r.raise_for_status(); return r.json()
