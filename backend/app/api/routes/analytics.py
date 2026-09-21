from fastapi import APIRouter
from ...schemas.api import AnalyticsOut
router=APIRouter()
@router.get('/summary',response_model=AnalyticsOut)
def summary(): return AnalyticsOut(active_cameras=4,vehicles_today=18472,alerts_open=7,congestion_index=63.5)
@router.get('/heatmap')
def heatmap(): return {'points':[{'lat':25.4484,'lng':81.8333,'weight':.9},{'lat':25.4358,'lng':81.8463,'weight':.7},{'lat':25.429,'lng':81.883,'weight':.8},{'lat':25.4185,'lng':81.858,'weight':.6}]}
