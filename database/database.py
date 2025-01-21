from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base

driver = "postgresql+asyncpg"  # Use asyncpg driver for PostgreSQL
server = "localhost"
database = "database"
username = "postgres"
password = "password"

DATABASE_URI = f"{driver}://{username}:{password}@{server}/{database}"

# Create an asynchronous engine
async_engine = create_async_engine(DATABASE_URI, echo=True)

# Create an AsyncSession maker
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Dependency to get DB session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
