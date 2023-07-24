import json
import os
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
with open(config_path, 'r') as config_file:
    keys: dict = json.load(config_file)
my_client_id: str = keys["client_id"]
my_client_secret: str = keys["client_secret"]
my_user_agent: str = keys["user_agent"]
my_refresh_token: str = keys["refresh_token"]
openapi_key: str = keys["openapi_key"]
application_password: str = keys["application_password"]
api_base_url: str = keys["api_base_url"]
username: str = keys["username"]