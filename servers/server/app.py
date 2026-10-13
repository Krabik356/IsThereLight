from fastapi import FastAPI, Request, Depends, HTTPException
import os
from dotenv import load_dotenv
import database
from contextlib import asynccontextmanager
import asyncio

load_dotenv()

pool = database.get_pool(2, 10, os.getenv("DB_NAME"), os.getenv("DB_USER"), int(os.getenv("DB_PASSWORD")))
is_checker_work = True

async def times_checker():
    while is_checker_work:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
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

    await database.update_time(conn, detectors_id)
