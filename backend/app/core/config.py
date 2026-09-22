from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / '.env'


class Settings(BaseSettings):
    database_url:str='sqlite:///./trinetra.db'
    cors_origins:list[str]=['http://localhost:5173']
    kafka_bootstrap_servers:str='localhost:9092'
    vahan_api_base_url:str=''
    vahan_api_key:str=''
    auth_secret:str='change-this-local-secret'
    admin_operator_id:str='admin'
    admin_access_key:str='trinetra2026'
    model_config=SettingsConfigDict(env_file=ROOT_ENV_FILE, extra='ignore')
settings=Settings()
