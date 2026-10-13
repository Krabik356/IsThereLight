import psycopg
from psycopg_pool import AsyncConnectionPool
import time

def get_pool(min_size, max_size, dbname, user, password):
    return AsyncConnectionPool(
        conninfo=f'dbname={dbname} user={user} password={password}',
        min_size= min_size,
        max_size= max_size,
        open=False
    )

async def detector_valid(conn: psycopg.AsyncConnection, detectors_id, detectors_secret):
    async with conn.cursor() as cur:
        is_ok = await cur.execute("SELECT EXISTS(SELECT 1 FROM detectors WHERE id=%s AND secret=%s)", (detectors_id, detectors_secret))
        return is_ok[0]

async def update_time(conn: psycopg.AsyncConnection, detectors_id):
    async with conn.cursor() as cur:
        await cur.execute("UPDATE detectors SET time=%s WHERE id=%s", (time.time(), detectors_id))

async def get_time(conn: psycopg.AsyncConnection, detectors_id):
    async with conn.cursor() as cur:
        return await cur.execute("SELECT time FROM detectors WHERE id=%s", (detectors_id,))