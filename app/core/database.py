from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from .config import settings
from .logger import logger

Base = declarative_base()

# Create a new engine
engine = create_engine(settings.DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the database tables
def create_db():
    engine = create_engine(settings.DATABASE_URL)
    if not database_exists(engine.url):
        logger.info('Database does not exist. Creating...')
        create_database(engine.url)
        logger.info('Database created successfully!')

    Base.metadata.create_all(bind=engine)


# Dependency for getting the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
