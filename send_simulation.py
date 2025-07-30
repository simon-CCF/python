import asyncio
import base64
import httpx

rawdata_list = [
    bytearray(b'\x7f\xe9o?\x00\x00'),
    bytearray(b'\x99\xea^?\x01\x00'),
    bytearray(b'\x99\xea^?\x02\x00'),
    bytearray(b'\xa1\xaa\xea>\x03\x00'),
    bytearray(b'\x94\xc8\xde>\x04\x00'),
    bytearray(b'\x02\xac\xf6?\x05\x00'),
    bytearray(b'J\xd1\xd8>\x06\x00'),
    bytearray(b'Ef\xc1?\x07\x00'),
    bytearray(b'T=\xe8>\x08\x00'),
    bytearray(b'\xfb\x8d\xea;\t\x00'),
    bytearray(b'\x7f\xe9o?\x00\x00'),
    bytearray(b'\x99\xea^?\x01\x00'),
    bytearray(b'\x99\xea^?\x02\x00'),
    bytearray(b'\xa1\xaa\xea>\x03\x00'),
    bytearray(b'\x94\xc8\xde>\x04\x00'),
    bytearray(b'\x02\xac\xf6?\x05\x00'),
    bytearray(b'J\xd1\xd8>\x06\x00'),
    bytearray(b'Ef\xc1?\x07\x00'),
    bytearray(b'T=\xe8>\x08\x00'),
    bytearray(b'\xfb\x8d\xea;\t\x00'),
    bytearray(b'\x7f\xe9o?\x00\x00'),
    bytearray(b'\x99\xea^?\x01\x00'),
    bytearray(b'\x99\xea^?\x02\x00'),
    bytearray(b'\xa1\xaa\xea>\x03\x00'),
    bytearray(b'\x94\xc8\xde>\x04\x00'),
    bytearray(b'\x02\xac\xf6?\x05\x00'),
    bytearray(b'J\xd1\xd8>\x06\x00'),
    bytearray(b'Ef\xc1?\x07\x00'),
    bytearray(b'T=\xe8>\x08\x00'),
    bytearray(b'\xfb\x8d\xea;\t\x00'),
    bytearray(b'\x7f\xe9o?\x00\x00'),
    bytearray(b'\x99\xea^?\x01\x00'),
    bytearray(b'\x99\xea^?\x02\x00'),
    bytearray(b'\xa1\xaa\xea>\x03\x00'),
    bytearray(b'\x94\xc8\xde>\x04\x00'),
    bytearray(b'\x02\xac\xf6?\x05\x00'),
    bytearray(b'J\xd1\xd8>\x06\x00'),
    bytearray(b'Ef\xc1?\x07\x00'),
    bytearray(b'T=\xe8>\x08\x00'),
    bytearray(b'\xfb\x8d\xea;\t\x00'),
    bytearray(b'\x7f\xe9o?\x00\x00'),
    bytearray(b'\x99\xea^?\x01\x00'),
    bytearray(b'\x99\xea^?\x02\x00'),
    bytearray(b'\xa1\xaa\xea>\x03\x00'),
    bytearray(b'\x94\xc8\xde>\x04\x00'),
    bytearray(b'\x02\xac\xf6?\x05\x00'),
    bytearray(b'J\xd1\xd8>\x06\x00'),
    bytearray(b'Ef\xc1?\x07\x00'),
    bytearray(b'T=\xe8>\x08\x00'),
    bytearray(b'\xfb\x8d\xea;\t\x00'),

]

API_URL = "http://127.0.0.1:8001/send/"
EMAIL = "321@gmail.com"

async def send_data():
    async with httpx.AsyncClient() as client:
        while True:  # 無限重複
            for raw_bytes in rawdata_list:
                data_b64 = base64.b64encode(raw_bytes).decode()
                payload = {
                    "email": EMAIL,
                    "data": data_b64,
                }
                try:
                    response = await client.post(API_URL, json=payload)
                    print(f"Sent data: {raw_bytes} Response: {response.status_code} {response.text}")
                except Exception as e:
                    print(f"Error sending data: {e}")
                await asyncio.sleep(0.1)  # 每次發送間隔0.1秒
if __name__ == "__main__":
    asyncio.run(send_data())
