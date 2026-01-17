#!/usr/bin/env python3
"""Complete database setup script for Noah Reading Agent."""

from src.vector_db_init import init_vector_database
from src.database_init import init_database
import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run complete database setup."""
    print("=" * 60)
    print("Noah Reading Agent - Database Setup")
    print("=" * 60)

    try:
        # Step 1: Initialize PostgreSQL database
        print("\n1. Setting up PostgreSQL database...")
        init_database()

        # Step 2: Initialize vector database
        print("\n2. Setting up vector database...")
        vector_result = init_vector_database()

        print("\n" + "=" * 60)
        print("Database setup completed successfully!")
        print("=" * 60)

        print("\nSetup Summary:")
        print("✓ PostgreSQL database and tables created")
        print("✓ Vector database (Pinecone) configured")
        print(f"✓ Vector index: {vector_result['index_name']}")
        print(f"✓ Embedding dimension: {vector_result['dimension']}")

        print("\nNext steps:")
        print("1. Run the FastAPI server: uvicorn src.main:app --reload")
        print("2. Test the API endpoints")
        print("3. Start ingesting content for recommendations")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"\n❌ Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
