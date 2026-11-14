import asyncio
from sqlalchemy import text
from app.db.session import engine, check_database_connection
from app.models import Base


async def init_test():
    print("Connecting to database...")
    status = await check_database_connection()
    print("Database Status:", status)

    async with engine.begin() as conn:
        print("Enabling uuid-ossp extension...")
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        
        # Test if vector extension exists
        try:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector";'))
            print("pgvector extension enabled successfully!")
        except Exception as e:
            print("pgvector extension not enabled in this container:", str(e))

        res = await conn.execute(text('SELECT uuid_generate_v4();'))
        print("Sample Generated UUID:", res.scalar())

        print("Testing Base.metadata.create_all...")
        await conn.run_sync(Base.metadata.create_all)
        print("All tables successfully verified and created in PostgreSQL!")


if __name__ == "__main__":
    asyncio.run(init_test())
