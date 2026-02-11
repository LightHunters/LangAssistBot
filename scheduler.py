import pendulum
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import mongo
import asyncio

sched = AsyncIOScheduler()

def start_scheduler(bot):
    @sched.scheduled_job("interval", minutes=1)
    async def check_and_send():
        try:
            all_users = await mongo.list_all_users()
            for u in all_users:
                tz = u.get("tz", "Europe/Zurich")
                review_time = u.get("review_time", "09:00")
                now = pendulum.now(tz)
                hhmm = now.format("HH:mm")
                if hhmm == review_time:
                    
                    words = await mongo.sample_words_for_user(u["telegram_id"], n=7)
                    if not words:
                        await bot.send_message(u["telegram_id"], "No words saved yet — keep reading!")
                        continue
                 
                    await bot.send_message(u["telegram_id"], f"Your quick review — {len(words)} items. Reply with translations to practice.")
                    for w in words:
                        ex = w.get("example") or ""
                        await bot.send_message(u["telegram_id"], f"{w['phrase']}\n{ex}")
        except Exception as e:
            print("Scheduler error:", e)

    sched.start()
