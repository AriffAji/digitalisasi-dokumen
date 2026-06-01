from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache

csrf  = CSRFProtect()
cache = Cache()
