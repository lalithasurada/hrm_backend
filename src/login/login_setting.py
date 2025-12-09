import os
from dotenv import load_dotenv
load_dotenv()


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # use `openssl rand -hex 32` in prod [web:2]
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))          # short-lived access token [web:2][web:13]
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")