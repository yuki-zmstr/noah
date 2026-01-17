"""Enhanced database service with session management and AWS Agent Core integration."""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any, Type, TypeVar
from contextlib import contextmanager
import logging

from src.database import SessionLocal, get_db
from src.services.agent_core import AgentCoreService

logger = logging.getLogger(__name__)

# Generic type for SQLAlchemy models
ModelType = TypeVar("ModelType")


class DatabaseService:
    """Enhanced database service with session management."""

    def __init__(self):
        """Initialize database service."""
        self.agent_core = AgentCoreService()

    @contextmanager
    def get_session(self):
        """Get database session with proper error handling."""
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error: {e}")
            raise
        finally:
            db.close()

    def create_record(self, db: Session, model_class: Type[ModelType], **kwargs) -> ModelType:
        """Create a new database record."""
        try:
            record = model_class(**kwargs)
            db.add(record)
            db.flush()  # Get the ID without committing
            db.refresh(record)
            return record
        except SQLAlchemyError as e:
            logger.error(f"Error creating {model_class.__name__}: {e}")
            raise

    def get_record(
        self,
        db: Session,
        model_class: Type[ModelType],
        record_id: Any
    ) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            return db.query(model_class).filter(
                model_class.id == record_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting {model_class.__name__} {record_id}: {e}")
            raise

    def get_records(
        self,
        db: Session,
        model_class: Type[ModelType],
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """Get multiple records with optional filtering."""
        try:
            query = db.query(model_class)

            if filters:
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(
                            getattr(model_class, field) == value)

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {model_class.__name__} records: {e}")
            raise

    def update_record(
        self,
        db: Session,
        record: ModelType,
        **kwargs
    ) -> ModelType:
        """Update a database record."""
        try:
            for field, value in kwargs.items():
                if hasattr(record, field):
                    setattr(record, field, value)

            db.flush()
            db.refresh(record)
            return record
        except SQLAlchemyError as e:
            logger.error(f"Error updating record: {e}")
            raise

    def delete_record(self, db: Session, record: ModelType) -> bool:
        """Delete a database record."""
        try:
            db.delete(record)
            db.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting record: {e}")
            raise

    async def create_user_profile_with_agent_core(
        self,
        db: Session,
        user_id: str,
        initial_preferences: Optional[Dict] = None
    ) -> Any:
        """Create user profile with AWS Agent Core integration."""
        from src.models.user_profile import UserProfile

        try:
            # Create basic profile
            profile_data = {
                "user_id": user_id,
                "preferences": initial_preferences or {},
                "reading_levels": {
                    "english": {"level": 5.0, "confidence": 0.5},
                    "japanese": {"level": 3.0, "confidence": 0.5}
                }
            }

            profile = self.create_record(db, UserProfile, **profile_data)

            # Initialize with Agent Core
            await self.agent_core.update_conversation_context(
                session_id=f"profile_init_{user_id}",
                user_message="Profile created",
                agent_response="Welcome to Noah!",
                intent={"intent": "profile_initialization", "confidence": 1.0}
            )

            logger.info(f"Created user profile for {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Error creating user profile with Agent Core: {e}")
            raise

    async def process_conversation_with_agent_core(
        self,
        db: Session,
        session_id: str,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process conversation message with AWS Agent Core integration."""
        from src.models.conversation import ConversationMessage

        try:
            # Analyze intent with Agent Core
            intent = await self.agent_core.analyze_intent(message, context)

            # Extract entities
            entities = await self.agent_core.extract_entities(message)

            # Store user message
            user_message = self.create_record(
                db,
                ConversationMessage,
                message_id=f"msg_{session_id}_{len(message)}",
                session_id=session_id,
                sender="user",
                content=message,
                intent=intent
            )

            # Generate response
            agent_response = await self.agent_core.generate_response(
                user_message=message,
                intent=intent,
                context=context or {}
            )

            # Store agent response
            agent_message = self.create_record(
                db,
                ConversationMessage,
                message_id=f"msg_{session_id}_{len(agent_response)}",
                session_id=session_id,
                sender="noah",
                content=agent_response,
                intent={"intent": "response", "confidence": 1.0}
            )

            # Update conversation context
            updated_context = await self.agent_core.update_conversation_context(
                session_id=session_id,
                user_message=message,
                agent_response=agent_response,
                intent=intent
            )

            return {
                "user_message": user_message,
                "agent_message": agent_message,
                "intent": intent,
                "entities": entities,
                "updated_context": updated_context
            }

        except Exception as e:
            logger.error(f"Error processing conversation with Agent Core: {e}")
            raise


# Global database service instance
db_service = DatabaseService()
