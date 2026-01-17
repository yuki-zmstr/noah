"""Vector database initialization for content embeddings and similarity search."""

from pinecone import Pinecone, ServerlessSpec
from typing import Dict, Any
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class VectorDBManager:
    """Manages vector database operations for content embeddings."""

    def __init__(self):
        """Initialize Pinecone client."""
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = "noah-content-embeddings"
        self.dimension = 1536  # OpenAI text-embedding-3-small dimension

    def create_index_if_not_exists(self) -> bool:
        """Create Pinecone index if it doesn't exist."""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]

            if self.index_name not in existing_indexes:
                # Create index with appropriate configuration
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
                return True
            else:
                logger.info(f"Pinecone index {self.index_name} already exists")
                return False

        except Exception as e:
            logger.error(f"Error creating Pinecone index: {e}")
            raise

    def get_index(self):
        """Get the Pinecone index instance."""
        return self.pc.Index(self.index_name)

    def setup_vector_database(self) -> Dict[str, Any]:
        """Set up the complete vector database."""
        logger.info("Setting up vector database for content embeddings...")

        # Create index
        created = self.create_index_if_not_exists()

        # Get index stats
        index = self.get_index()
        stats = index.describe_index_stats()

        result = {
            "index_name": self.index_name,
            "dimension": self.dimension,
            "metric": "cosine",
            "created_new": created,
            "total_vectors": stats.total_vector_count,
            "namespaces": list(stats.namespaces.keys()) if stats.namespaces else []
        }

        logger.info(f"Vector database setup complete: {result}")
        return result


def init_vector_database():
    """Initialize vector database for content embeddings."""
    try:
        manager = VectorDBManager()
        result = manager.setup_vector_database()

        print("Vector Database Initialization Results:")
        print(f"  Index Name: {result['index_name']}")
        print(f"  Dimension: {result['dimension']}")
        print(f"  Metric: {result['metric']}")
        print(f"  Created New Index: {result['created_new']}")
        print(f"  Total Vectors: {result['total_vectors']}")
        print(f"  Namespaces: {result['namespaces']}")

        return result

    except Exception as e:
        print(f"Error initializing vector database: {e}")
        raise


if __name__ == "__main__":
    init_vector_database()
