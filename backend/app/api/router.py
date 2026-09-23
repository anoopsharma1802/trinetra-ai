from fastapi import APIRouter
from .routes import auth, cameras, vehicles, analytics, alerts, enforcement, copilot, cities, vehicle_intelligence

api_router=APIRouter()
api_router.include_router(auth.router,prefix='/auth',tags=['auth'])
api_router.include_router(cameras.router,prefix='/cameras',tags=['cameras'])
api_router.include_router(vehicles.router,prefix='/vehicles',tags=['vehicles'])
api_router.include_router(analytics.router,prefix='/analytics',tags=['analytics'])
api_router.include_router(alerts.router,prefix='/alerts',tags=['alerts'])
api_router.include_router(enforcement.router,prefix='/enforcement',tags=['enforcement'])
api_router.include_router(copilot.router,prefix='/copilot',tags=['copilot'])
api_router.include_router(cities.router,prefix='/cities',tags=['cities'])
api_router.include_router(vehicle_intelligence.router,prefix='/vehicles',tags=['vehicle-intelligence'])
