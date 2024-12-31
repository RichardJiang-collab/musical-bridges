import logging
import os

logging.basicConfig(level=logging.INFO)

def log_env_variables():
    logging.info(f"SPOTIFY_SCOPES: {os.environ.get('SPOTIFY_SCOPES')}")
    logging.info(f"Other Variable: {os.environ.get('OTHER_VARIABLE')}")

log_env_variables()