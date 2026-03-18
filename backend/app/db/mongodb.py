from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

settings = get_settings()
_client: AsyncIOMotorClient | None = None


def connect_to_mongo() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    client = connect_to_mongo()
    return client[settings.mongodb_db]


async def get_db_dependency() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield get_db()


def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
