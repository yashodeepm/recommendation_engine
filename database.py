import motor.motor_asyncio

MONGO_SERVER = "<Connection_string>"

async def get_client(db_name: str):
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_SERVER, serverSelectionTimeoutMS=5000)
        return client[db_name]

    except Exception:
        print("Unable to connect!")

