from fastapi import FastAPI, Request, HTTPException, Query
from celery_app import celery_app
import base64
import hashlib
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, LargeBinary, TIMESTAMP, func, inspect
from pydantic import BaseModel
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import struct

DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/raw_data_db?charset=utf8mb4"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

origins = [
    "http://localhost:8080",  # 你的前端地址
    "http://127.0.0.1:8080",
]




# @app.websocket("/ws/{email}")
# async def websocket_endpoint(websocket: WebSocket, email: str):
#     await websocket.accept()
#     table_name = "sensor_" + hashlib.md5(email.encode()).hexdigest()

#     session = SessionLocal()
#     try:
#         table = Table(table_name, metadata, autoload_with=engine)
#     except Exception:
#         await websocket.send_json({"error": f"Table {table_name} not found."})
#         await websocket.close()
#         return

#     # 一開始抓目前資料庫的最大ID，作為 last_id 起點
#     query_max = table.select().order_by(table.c.id.desc()).limit(1)
#     max_row = session.execute(query_max).fetchone()
#     last_id = max_row.id if max_row else 0

#     try:
#         while True:
#             query = table.select().where(table.c.id > last_id).order_by(table.c.id.asc()).limit(1)
#             result = session.execute(query).fetchone()

#             if result:
#                 last_id = result.id
#                 raw_bytes = result.raw_content
#                 if len(raw_bytes) >= 6:
#                     angle = struct.unpack("<f", raw_bytes[0:4])[0]
#                     seq = raw_bytes[4]
#                     tail = raw_bytes[5]
#                     await websocket.send_json({
#                         "id": last_id,
#                         "angle_deg": round(angle, 2),
#                         "seq": seq,
#                         "tail": tail,
#                         "hex": raw_bytes.hex()
#                     })
#                 await asyncio.sleep(0.01)
#             else:
#                 await asyncio.sleep(0.3)

#     except WebSocketDisconnect:
#         print(f"Client {email} disconnected.")
#     finally:
#         session.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 允許這些來源的跨域請求
    allow_credentials=True,
    allow_methods=["*"],        # 允許所有 HTTP 方法
    allow_headers=["*"],        # 允許所有 HTTP 標頭
)

def register_user(email: str) -> str:
    table_hash = hashlib.md5(email.encode()).hexdigest()
    table_name = f"sensor_{table_hash}"


    inspector = inspect(engine)
    if inspector.has_table(table_name):
        return table_name

    sensor_table = Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("raw_content", LargeBinary, nullable=False),
        Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    )
    metadata.create_all(engine, tables=[sensor_table])
    return table_name

@app.delete("/patient/{email}")
async def delete_patient(email: str):
    table_name = "sensor_" + hashlib.md5(email.encode()).hexdigest()
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        raise HTTPException(status_code=404, detail="資料表不存在")

    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
    return {"detail": f"已刪除資料表 {table_name}"}


@app.get("/data/{table_name}/")
async def get_raw_data_range(table_name: str, start_id: int = Query(1), end_id: int = Query(10)):
    session = SessionLocal()
    try:
        table = Table(table_name, metadata, autoload_with=engine)
        query = table.select().where(table.c.id.between(start_id, end_id))
        results = session.execute(query).fetchall()
        if not results:
            return {"detail": "No records found"}
        data_list = []
        for row in results:
            raw_bytes = row.raw_content
            hex_str = raw_bytes.hex()
            data_list.append({"id": row.id, "data_hex": hex_str})
        return {"records": data_list}
    finally:
        session.close()
class RegisterRequest(BaseModel):
    email: str

@app.post("/register/")
async def register(req: RegisterRequest):
    table_name = register_user(req.email)
    return {"table_name": table_name}

@app.post("/send/")
async def receive_data(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    email = data.get("email")
    data_b64 = data.get("data")  # 改成用 Base64 傳輸字串

    if not email or not isinstance(email, str):
        raise HTTPException(status_code=400, detail="Missing or invalid email")

    if not data_b64 or not isinstance(data_b64, str):
        raise HTTPException(status_code=400, detail="Missing or invalid data (expect base64 string)")

    try:
        raw_bytes = base64.b64decode(data_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 data")

    # 將 bytes 轉成 list[int]，給 Celery
    data_list = list(raw_bytes)

    celery_app.send_task("celery_worker.process_sensor_data", args=[{
        "email": email,
        "data": data_list
    }])

    return {"status": "Task sent to Celery"}

