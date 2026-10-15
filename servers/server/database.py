import psycopg
from psycopg_pool import AsyncConnectionPool
import time

def get_pool(min_size, max_size, dbname, user, password):
    return AsyncConnectionPool(
        conninfo=f'dbname={dbname} user={user} password={password}',
        min_size= min_size,
        max_size= max_size,
        open=False,
        kwargs = {"autocommit": True}
    )

async def detector_valid(conn: psycopg.AsyncConnection, detectors_id, detectors_secret):
    async with conn.cursor() as cur:
        await cur.execute("SELECT EXISTS(SELECT 1 FROM detectors WHERE id=%s AND secret=%s)",(detectors_id, detectors_secret))
        is_ok = await cur.fetchone()
        return is_ok[0]

async def update_time(conn: psycopg.AsyncConnection, detectors_id):
    async with conn.cursor() as cur:
        await cur.execute("SELECT is_updated FROM detectors WHERE id=%s", (detectors_id,))
        is_updated = await cur.fetchone()
        await cur.execute("SELECT u.chat_id FROM users u JOIN detectors_users ON u.id=du.user_id WHERE du.detector_id=%s",(detectors_id,))
        chats = await cur.fetchall()
        await cur.execute("UPDATE detectors SET last_time=%s, is_updated=%s WHERE id=%s", (time.time(), True, detectors_id))
        return (is_updated[0], chats)

async def get_chats_from_bad_detecrots(conn: psycopg.AsyncConnection):
    async with conn.cursor() as cur:
        time_now = time.time()
        print(time_now)
        await cur.execute("SELECT u.chat_id FROM users u JOIN detectors_users du ON u.id=du.user_id JOIN detectors d ON du.detector_id=d.id WHERE d.last_time < %s AND d.is_updated=TRUE", (time_now - 10,))
        chats = await cur.fetchall()
        await cur.execute("UPDATE detectors SET is_updated=%s WHERE last_time < %s", (False, time_now-10))
        return [r[0] for r in chats]
