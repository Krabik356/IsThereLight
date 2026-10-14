import asyncio
from fastapi import FastAPI, Request, Depends, HTTPException
import os
from dotenv import load_dotenv
import database
from contextlib import asynccontextmanager
import httpx

load_dotenv()

pool = database.get_pool(2, 10, os.getenv("DB_NAME"), os.getenv("DB_USER"), int(os.getenv("DB_PASSWORD")))
is_checker_work = True
token = os.getenv("BOT_TOKEN")

async def times_checker():
    async with pool.connection() as conn:
        while is_checker_work:
            chats = await database.get_chats_from_bad_detecrots(conn)
            for chat in chats:
                async with httpx.AsyncClient(base_url="") as client:
                    await client.post(f'https://api.telegram.org/bot{token}/sendMessage', json={"chat_id": chat, "text": f'*Увага 📢!*\n\nСвітло в домі *вимкнулось* 🕯️...', "parse_mode": "Markdown"})

            await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_checker_work

    await pool.open()
    task = asyncio.create_task(times_checker())

    yield

    await pool.close()
    is_checker_work = False
    await task

app = FastAPI(lifespan=lifespan)

async def get_conn():
    async with pool.connection() as conn:
        yield conn

@app.post("/remind/{detectors_id}", status_code=200)
async def remind(req: Request, detectors_id: str, conn=Depends(get_conn)):
    secret = req.get("secret")

    is_ok = await database.detector_valid(conn, detectors_id, secret)
    if not is_ok:
        raise HTTPException(detail="incorrect detector`s id or secret", status_code=405)

    is_updated = await database.update_time(conn, detectors_id)
    if not is_updated[0]:
        async with httpx.AsyncClient(base_url="") as client:
            for chat in is_updated[1]:
                await client.post(f'https://api.telegram.org/bot{token}/sendMessage',json={"chat_id": chat, "text": f'*УРААА 👏!!!*\n\nСвітло в домі *повернулось* 💡!',"parse_mode": "Markdown"})


