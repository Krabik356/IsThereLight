import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

def get_pool(min_size, max_size, dbname, user, password):
    return AsyncConnectionPool(
        conninfo=f'dbname={dbname} user={user} password={password}',
        min_size= min_size,
        max_size= max_size,
        open=False,
        kwargs={"autocommit": True}
    )

async def add_user(conn: psycopg.AsyncConnection, user_id, chat_id):
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO users(id, chat_id, status) VALUES(%s, %s, %s) ON CONFLICT (id) DO NOTHING", (user_id, chat_id, ""))

async def change_status(conn: psycopg.AsyncConnection, user_id, status):
    async with conn.cursor() as cur:
        await cur.execute("UPDATE users SET status=%s WHERE id=%s", (status, user_id))

async def get_status(conn: psycopg.AsyncConnection, user_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        result = await cur.execute("SELECT status FROM users WHERE id=%s", (user_id,))
        return (await result.fetchone())["status"]

async def is_detector_free(conn: psycopg.AsyncConnection, detector_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT EXISTS(SELECT 1 FROM detectors WHERE id=%s)",(detector_id,))
        is_exists = await cur.fetchone()
        if not is_exists["exists"]:
            return False

        result = await cur.execute("SELECT owner FROM detectors WHERE id=%s", (detector_id,))
        owner = await result.fetchone()
        if owner["owner"] != None:
            return False

        return True

async def detector_coding(conn: psycopg.AsyncConnection, detector_id, user_id, detector_password):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("UPDATE detectors SET owner=%s, password=%s WHERE id=%s", (user_id, detector_password, detector_id))

async def detector_user_relation(conn: psycopg.AsyncConnection, detector_id, user_id, detector_password):
    async with conn.cursor() as cur:
        await cur.execute("SELECT EXISTS(SELECT 1 FROM detectors WHERE id=%s AND password=%s)", (detector_id, detector_password))
        is_exists = await cur.fetchone()
        if not is_exists:
            return False

        await cur.execute("INSERT INTO detectors_users(user_id, detector_id) VALUES(%s, %s)", (user_id, detector_id))
        return True

async def is_detector_correct(conn: psycopg.AsyncConnection, detector_id, detector_password):
    async with conn.cursor() as cur:
        await cur.execute("SELECT EXISTS(SELECT 1 FROM detectors WHERE id=%s AND password=%s)",(detector_id, detector_password))
        is_correct = await cur.fetchone()
        if not is_correct[0]:
            return False
        return True