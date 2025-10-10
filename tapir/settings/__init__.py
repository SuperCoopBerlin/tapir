
from .env import env

ENABLE_RIZOMA_CONTENT = env.bool("ENABLE_RIZOMA_CONTENT", default=False)
if ENABLE_RIZOMA_CONTENT:
    print("Loading rizoma settings module")
    from .rizoma import *
else:
    print("Loading default settings module")
    from .shared import *