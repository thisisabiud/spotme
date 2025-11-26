import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    from .production import *
else:
    from .development import *