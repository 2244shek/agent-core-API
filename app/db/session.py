from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# pool_pre_ping=True is vital for serverless DBs like Neon
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()