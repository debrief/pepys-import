from flask_cachebuster import CacheBuster
from flask_cors import CORS

cors = CORS()

cache_buster = CacheBuster(config={"extensions": [".js", ".css", ".csv"], "hash_size": 5})
