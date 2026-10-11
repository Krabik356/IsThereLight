import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

def get_pool(min_size:int, max_size:int, dbname, user, password):
    return AsyncConnectionPool(
        conninfo=f'dbname={dbname} user={user} password={password}',
        min_size= min_size,
        max_size= max_size,
        open=False
    )

async def add_user(conn: psycopg.AsyncConnection, user_id: int, chat_id: str):
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO users(id, chat_id, status) VALUES(%s, %s, %s) ON CONFLICT (id) DO NOTHING", (user_id, chat_id, ""))

async def change_status(conn: psycopg.AsyncConnection, user_id: int, status: str):
    async with conn.cursor() as cur:
        await cur.execute("UPDATE users SET status=%s WHERE id=%s", (status, user_id))

async def get_status(conn: psycopg.AsyncConnection, user_id: int):
    async with conn.cursor(row_factory=dict_row) as cur:
        result = await cur.execute("SELECT status FROM users WHERE id=%s", (user_id,))
        return (await result.fetchone())["status"]

async def is_detector_free(conn: psycopg.AsyncConnection, detector_id: int):
    async with conn.cursor(row_factory=dict_row) as cur:
        result = await cur.execute("SELECT owner FROM detectors WHERE id=%s", (detector_id,))
        owner = (await result.fetchone())["owner"]
        print(owner)
        if owner == None:
            return True

        return False

async def detector_coding(conn: psycopg.AsyncConnection, detector_id: int , user_id: str, detector_password):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("UPDATE detectors SET owner=%s, password=%s WHERE id=%s", (user_id, detector_password, detector_id))

async def detector_user_relation(conn: psycopg.AsyncConnection, detector_id: int , user_id: str, detector_password):
    async with conn.cursor() as cur:
        await cur.execute("SELECT EXISTS(SELECT 1 FROM detectors WHERE id=%s AND password=%s)", (detector_id, detector_password))
        is_exists = await cur.fetchone()
        if not is_exists:
            return False

        await cur.execute("INSERT INTO detectors_users(user_id, detector_id) VALUES(%s, %s)", (user_id, detector_id))
        return True