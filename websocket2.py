import asyncio
import hashlib
import struct

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/raw_data_db?charset=utf8mb4"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()


@app.websocket("/ws/{email}")
async def websocket_endpoint(websocket: WebSocket, email: str):
    await websocket.accept()
    table_name = "sensor_" + hashlib.md5(email.encode()).hexdigest()

    session = SessionLocal()
    try:
        table = Table(table_name, metadata, autoload_with=engine)
    except Exception:
        await websocket.send_json({"error": f"Table {table_name} not found."})
        await websocket.close()
        return

    # 一開始抓目前資料庫的最大ID，作為 last_id 起點
    query_max = table.select().order_by(table.c.id.desc()).limit(1)
    max_row = session.execute(query_max).fetchone()
    last_id = max_row.id if max_row else 0

    try:
        while True:
            query = table.select().where(table.c.id > last_id).order_by(table.c.id.asc()).limit(1)
            result = session.execute(query).fetchone()

            if result:
                last_id = result.id
                raw_bytes = result.raw_content
                if len(raw_bytes) >= 6:
                    angle = struct.unpack("<f", raw_bytes[0:4])[0]
                    seq = raw_bytes[4]
                    tail = raw_bytes[5]
                    await websocket.send_json({
                        "id": last_id,
                        "angle_deg": round(angle, 2),
                        "seq": seq,
                        "tail": tail,
                        "hex": raw_bytes.hex()
                    })
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(0.3)

    except WebSocketDisconnect:
        print(f"Client {email} disconnected.")
    finally:
        session.close()