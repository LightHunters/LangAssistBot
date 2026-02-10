import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import config

client = AsyncIOMotorClient(config.MONGODB_URI)
db = client.langassist

users = db.users
words = db.words

async def init_db():
    
    await users.create_index("telegram_id", unique=True)
    await words.create_index([("telegram_id", 1), ("phrase", 1)], unique=True)


async def upsert_user(telegram_id: int, native_lang: str, learning_lang: str, review_time: str = "09:00", tz: str = "Europe/Zurich"):
    doc = {
        "telegram_id": telegram_id,
        "native_lang": native_lang,
        "learning_lang": learning_lang,
        "review_time": review_time,
        "tz": tz
    }
    await users.update_one({"telegram_id": telegram_id}, {"$set": doc}, upsert=True)
    return await users.find_one({"telegram_id": telegram_id})

async def get_user_by_telegram(telegram_id: int):
    return await users.find_one({"telegram_id": telegram_id})

async def list_all_users():
    cursor = users.find({})
    return await cursor.to_list(length=10000)

async def add_word_for_user(telegram_id: int, phrase: str, ai_data: dict):
    try:
        doc = {
            "telegram_id": telegram_id,
            "phrase": phrase,
            "translation": ai_data.get("translation", ""),
            "definition": ai_data.get("definition", ""),
            "example": ai_data.get("example", ""),
            "example_translation": ai_data.get("example_translation", ""),
            "progress": 0,
            "created_at": __import__("datetime").datetime.utcnow()
        }
        await words.insert_one(doc)
        return doc
    except Exception:
      
        return await words.find_one({"telegram_id": telegram_id, "phrase": phrase})

async def list_words_for_user(telegram_id: int, limit=200):
    cursor = words.find({"telegram_id": telegram_id}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def sample_words_for_user(telegram_id: int, n=7):
    pipeline = [
        {"$match": {"telegram_id": telegram_id}},
        {"$sample": {"size": n}}
    ]
    cursor = words.aggregate(pipeline)
    return await cursor.to_list(length=n)

async def delete_words_for_user(telegram_id: int):
    await words.delete_many({"telegram_id": telegram_id})