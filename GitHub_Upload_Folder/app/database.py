import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Get the absolute path for the database file in the app directory
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "med_lookup.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

Base = declarative_base()

class SourceDocument(Base):
    __tablename__ = 'source_documents'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)           # Filename or title
    file_path = Column(String, nullable=True)       # Path if it's a local file
    url = Column(String, nullable=True)             # URL if it's a web link
    source_type = Column(String, nullable=False)    # 'pdf', 'excel', 'word', 'link', etc.
    is_active = Column(Boolean, default=True)       # Whether it is selected for lookup
    added_date = Column(DateTime, default=datetime.utcnow)

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a customized Session class
SessionLocal = sessionmaker(bind=engine)

def get_db_session():
    """Returns a new database session."""
    return SessionLocal()
