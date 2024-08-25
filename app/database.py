from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Generator function to manage database sessions.
    
    Yields:
        Session: A SQLAlchemy database session.
    
    This function creates a new SQLAlchemy SessionLocal instance,
    yields it to be used in a single request, and then closes it
    when the request is done.
    """
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
