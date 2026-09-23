import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / '.env'


class Settings(BaseSettings):
    database_url:str='sqlite:///./trinetra.db'
    cors_origins:list[str]=['http://localhost:5173']
    kafka_bootstrap_servers:str='localhost:9092'
    vahan_api_base_url:str=''
    vahan_api_key:str=''
    vahan_provider_mode:str='not_configured'
    stolen_provider_mode:str='not_configured'
    vehicle_verification_rate_limit:int=30
    auth_secret:str='change-this-local-secret'
    admin_operator_id:str='admin'
    admin_access_key:str='trinetra2026'
    openai_api_key:str=''
    gemini_api_key:str=''
    copilot_model:str='gemini-3.6-flash'
    seed_demo_data:bool=False
    model_config=SettingsConfigDict(env_file=ROOT_ENV_FILE, extra='ignore')

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, value):
        if value in (None, ''):
            return ['http://localhost:5173']
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ['http://localhost:5173']
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [item.strip() for item in value.split(',') if item.strip()]
        return value

settings=Settings()
