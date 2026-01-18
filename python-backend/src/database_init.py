"""Database initialization script."""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from src.database import Base, engine
from src.config import settings

# Import all models to ensure they're registered
from src.models.user_profile import UserProfile, ReadingBehavior, PreferenceSnapshot
from src.models.content import ContentItem, DiscoveryRecommendation
from src.models.conversation import ConversationSession, ConversationMessage, ConversationHistory


def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    # Parse database URL to get database name
    db_url_parts = settings.database_url.split('/')
    db_name = db_url_parts[-1]
    base_url = '/'.join(db_url_parts[:-1])

    # Connect to PostgreSQL server (not specific database)
    server_engine = create_engine(f"{base_url}/postgres")

    try:
        with server_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )

            if not result.fetchone():
                # Database doesn't exist, create it
                conn.execute(text("COMMIT"))  # End any existing transaction
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Created database: {db_name}")
            else:
                print(f"Database {db_name} already exists")

    except OperationalError as e:
        print(f"Error connecting to PostgreSQL server: {e}")
        print("Make sure PostgreSQL is running and connection details are correct")
        raise
    finally:
        server_engine.dispose()


def create_tables():
    """Create all database tables."""
    try:
        # Test connection to the target database
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Successfully created all database tables")

        # Print created tables
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"Created tables: {', '.join(tables)}")

    except OperationalError as e:
        print(f"Error creating tables: {e}")
        raise


def init_database():
    """Initialize the complete database setup."""
    print("Initializing Noah Reading Agent database...")
    print(f"Database URL: {settings.database_url}")

    # Step 1: Create database if it doesn't exist
    create_database_if_not_exists()

    # Step 2: Create tables
    create_tables()

    print("Database initialization completed successfully!")


if __name__ == "__main__":
    init_database()
