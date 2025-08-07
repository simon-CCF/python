# 第一版
# import asyncio
# import hashlib
# import aioredis
# import struct

# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy import create_engine, MetaData, Table, select, func
# from sqlalchemy.orm import sessionmaker


# DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/raw_data_db?charset=utf8mb4"
# engine = create_engine(DATABASE_URL)
# metadata = MetaData()
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# app = FastAPI()

# origins = [
#     "http://localhost:8080",
#     "http://127.0.0.1:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


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

#     # 先取得最小的 id，作為起點
#     query_min = select(table.c.id).order_by(table.c.id.asc()).limit(1)
#     min_row = session.execute(query_min).fetchone()
#     last_id = min_row[0] if min_row else 0
#     print(f"Connected to table {table_name}, starting from min id {last_id}")

#     try:
#         while True:
#             # 撈出 id >= last_id 的資料，一筆一筆送出
#             query = (
#                 select(table)
#                 .where(table.c.id >= last_id)
#                 .order_by(table.c.id.asc())
#                 .limit(1)
#             )
#             result = session.execute(query).fetchone()

#             if result:
#                 current_id = result.id
#                 if current_id == last_id or current_id > last_id:
#                     last_id = current_id + 1  # 送完後往下一筆

#                 raw_bytes = result.raw_content
#                 print(f"Sending row id={result.id}, raw_bytes len={len(raw_bytes)}")

#                 if len(raw_bytes) >= 6:
#                     angle = struct.unpack("<f", raw_bytes[0:4])[0]
#                     seq = raw_bytes[4]
#                     tail = raw_bytes[5]
#                     await websocket.send_json({
#                         "id": result.id,
#                         "angle_deg": round(angle, 2),
#                         "seq": seq,
#                         "tail": tail,
#                         "hex": raw_bytes.hex()
#                     })

#                 await asyncio.sleep(0.01)
#             else:
#                 # 已讀到最新資料，等待新資料進來
#                 await asyncio.sleep(0.3)

#     except WebSocketDisconnect:
#         print(f"Client {email} disconnected.")
#     finally:
#         session.close()@app.websocket("/ws/{email}")




# 第二版
# import asyncio
# import hashlib
# import redis.asyncio as redis
# import struct
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware

# def parse_data(hex_str: str):
#     data_bytes = bytes.fromhex(hex_str)
#     angle, = struct.unpack('<f', data_bytes[0:4])
#     angle = round(angle, 2)
#     seq, = struct.unpack('<H', data_bytes[4:6])
#     return {
#         "angle_deg": angle,
#         "seq": seq,
#         "hex": hex_str
#     }
# app = FastAPI()

# redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# origins = [
#     "http://localhost:8080",
#     "http://127.0.0.1:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# def email_to_channel(email: str) -> str:
#     return f"sensor_{hashlib.md5(email.encode('utf-8')).hexdigest()}"

# @app.websocket("/ws/{channel}")
# async def websocket_endpoint(websocket: WebSocket, channel: str):
#     await websocket.accept()
#     print(f"監控病人，已訂閱 Redis 頻道: {channel}")

#     pubsub = redis_client.pubsub()
#     await pubsub.subscribe(channel)

#     try:
#         while True:
#             message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
#             if message and "data" in message:
#                 data = message["data"]
#                 if isinstance(data, bytes):
#                     data = data.decode()

#                 try:
#                     await websocket.send_text(data)
#                 except Exception:
#                     print("WebSocket 已斷線，跳出監聽迴圈")
#                     break

#             await asyncio.sleep(0.1)

#     except WebSocketDisconnect:
#         print("WebSocket Disconnect")

#     finally:
#         print(f"取消訂閱 Redis 頻道 {channel}")
#         await pubsub.unsubscribe(channel)
#         await pubsub.close()

#     # 不要在這裡呼叫 await websocket.close()



import asyncio
import hashlib
import redis.asyncio as redis
import struct
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

def parse_data(hex_str: str):
    data_bytes = bytes.fromhex(hex_str)
    angle, = struct.unpack('<f', data_bytes[0:4])
    angle = round(angle, 2)
    seq, = struct.unpack('<H', data_bytes[4:6])
    return {
        "angle_deg": angle,
        "seq": seq,
        "hex": hex_str
    }

app = FastAPI()

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def email_to_channel(email: str) -> str:
    return f"sensor_{hashlib.md5(email.encode('utf-8')).hexdigest()}"

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await websocket.accept()
    print(f"監控病人，已訂閱 Redis 頻道: {channel}")

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and "data" in message:
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()

                parsed = parse_data(data)

                try:
                    await websocket.send_json(parsed)
                except Exception:
                    print("WebSocket 已斷線，跳出監聽迴圈")
                    break

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("WebSocket Disconnect")

    finally:
        print(f"取消訂閱 Redis 頻道 {channel}")
        await pubsub.unsubscribe(channel)
        await pubsub.close()
# ..