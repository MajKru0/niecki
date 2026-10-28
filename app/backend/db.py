from sqlalchemy import create_engine
from config import Config

engine = create_engine(
    Config.DB_TYPE + "+psycopg2://" + Config.DB_TYPE + ":" + Config.DB_PASS + "@" + Config.DB_HOST + "/" + Config.DB_NAME,
                        pool_pre_ping=True)