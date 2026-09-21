from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url:str='sqlite:///./trinetra.db'
    cors_origins:list[str]=['http://localhost:5173']
    kafka_bootstrap_servers:str='localhost:9092'
    vahan_api_base_url:str=''
    vahan_api_key:str=''
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
