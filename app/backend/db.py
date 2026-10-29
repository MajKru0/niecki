from sqlalchemy import create_engine, URL
from config import Config

#engine = create_engine(
#    Config.DB_TYPE + "+psycopg2://" + Config.DB_TYPE + ":" + Config.DB_PASS + "@" + Config.DB_HOST + "/" + Config.DB_NAME,
#                        pool_pre_ping=True)

url_obj = URL.create(
    Config.DB_TYPE,
    username=Config.DB_USERNAME,
    password=Config.DB_PASS,
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME
)

engine = create_engine(url_obj, 
                       pool_pre_ping=True,
    connect_args={"options": "-c lc_messages=C"})