# celery_worker.py
import logging
from celery import Celery
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, LargeBinary, TIMESTAMP, func, inspect
from sqlalchemy.orm import sessionmaker
from functools import lru_cache
import hashlib
import redis  # 新增同步 redis 客戶端

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/raw_data_db?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
metadata = MetaData()

inspector = inspect(engine)

# 初始化 redis 同步客戶端
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def email_to_table_name(email: str) -> str:
    hashed = hashlib.md5(email.encode()).hexdigest()
    return f"sensor_{hashed}"

@lru_cache(maxsize=128)
def get_sensor_table(table_name: str) -> Table:
    return Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("raw_content", LargeBinary, nullable=False),
        Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
        autoload_with=engine,
        extend_existing=True,
    )

@celery_app.task(name="celery_worker.process_sensor_data")
def process_sensor_data(log_data):
    session = SessionLocal()
    try:
        email = log_data.get("email")
        raw_list = log_data.get("data")

        if not email or not isinstance(raw_list, list):
            logger.warning("⚠️ Invalid data")
            return

        data_bytes = bytes(raw_list)
        table_name = email_to_table_name(email)

        if not inspector.has_table(table_name):
            logger.error(f"❌ Table {table_name} 不存在，請先用 auth 服務註冊")
            return

        sensor_table = get_sensor_table(table_name)
        insert_stmt = sensor_table.insert().values(raw_content=data_bytes)
        session.execute(insert_stmt)
        session.commit()
        logger.info(f"✅ Data written to {table_name}")

        # 寫入成功後 publish 到 redis 頻道
        channel = f"sensor_{hashlib.md5(email.encode('utf-8')).hexdigest()}"
        data_to_send = data_bytes.hex()
        redis_client.publish(channel, data_to_send)

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Exception: {e}")
    finally:
        session.close()
