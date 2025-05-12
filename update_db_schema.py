import logging
from sqlalchemy import create_engine, Column, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_schema():
    """Update the database schema to add the is_summary column to the ai_messages table"""
    try:
        # Connect to the database
        conn = engine.connect()
        
        # Check if the column already exists
        result = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='ai_messages' AND column_name='is_summary'")
        if result.fetchone():
            logger.info("Column 'is_summary' already exists in the ai_messages table")
            conn.close()
            return
        
        # Add the column
        conn.execute("ALTER TABLE ai_messages ADD COLUMN is_summary BOOLEAN DEFAULT FALSE")
        logger.info("Added 'is_summary' column to the ai_messages table")
        
        # Close the connection
        conn.close()
        
        logger.info("Database schema updated successfully")
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        raise

if __name__ == "__main__":
    update_schema()
