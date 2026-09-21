from fastapi import APIRouter
from .routes import cameras,vehicles,analytics,alerts,enforcement
api_router=APIRouter()
api_router.include_router(cameras.router,prefix='/cameras',tags=['cameras'])
api_router.include_router(vehicles.router,prefix='/vehicles',tags=['vehicles'])
api_router.include_router(analytics.router,prefix='/analytics',tags=['analytics'])
api_router.include_router(alerts.router,prefix='/alerts',tags=['alerts'])
api_router.include_router(enforcement.router,prefix='/enforcement',tags=['enforcement'])
