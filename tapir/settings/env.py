import os
import environ

from pathlib import Path

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

environ.Env.read_env(os.environ.get('ENV_FILE_PATH', os.path.join(BASE_DIR, ".env")))