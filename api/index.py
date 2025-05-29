from fastapi import FastAPI
from core.bot import analyze_and_alert
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    async def runner():
        while True:
            analyze_and_alert()
            await asyncio.sleep(60 * int(os.getenv("INTERVAL_MINUTES", 15)))
    asyncio.create_task(runner())

@app.get("/")
def read_root():
    return {"status": "Bot is running."}
