"""Base repository pattern for database operations."""

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from src.infrastructure.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations."""

    def __init__(self, model_class: type[T], session: Session):
        """Initialize repository with model class and database session.

        Args:
            model_class: The SQLAlchemy model class
            session: Database session
        """
        self.model_class = model_class
        self.session = session

    def create(self, **kwargs: Any) -> T:
        """Create a new instance.

        Args:
            **kwargs: Model attributes

        Returns:
            Created model instance
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get_by_id(self, id: int) -> T | None:
        """Get instance by ID.

        Args:
            id: Instance ID

        Returns:
            Model instance or None if not found
        """
        return self.session.query(self.model_class).filter_by(id=id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all instances with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return self.session.query(self.model_class).offset(skip).limit(limit).all()

    def get_by_filter(self, **filters: Any) -> list[T]:
        """Get instances by filter criteria.

        Args:
            **filters: Filter criteria as keyword arguments

        Returns:
            List of matching model instances
        """
        return self.session.query(self.model_class).filter_by(**filters).all()

    def get_one_by_filter(self, **filters: Any) -> T | None:
        """Get single instance by filter criteria.

        Args:
            **filters: Filter criteria as keyword arguments

        Returns:
            Model instance or None if not found
        """
        return self.session.query(self.model_class).filter_by(**filters).first()

    def update(self, id: int, **kwargs: Any) -> T | None:
        """Update an instance.

        Args:
            id: Instance ID
            **kwargs: Attributes to update

        Returns:
            Updated model instance or None if not found
        """
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.commit()
            self.session.refresh(instance)
        return instance

    def delete(self, id: int) -> bool:
        """Delete an instance.

        Args:
            id: Instance ID

        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False

    def count(self, **filters: Any) -> int:
        """Count instances matching filter criteria.

        Args:
            **filters: Filter criteria as keyword arguments

        Returns:
            Count of matching instances
        """
        query = self.session.query(self.model_class)
        if filters:
            query = query.filter_by(**filters)
        return query.count()

    def exists(self, **filters: Any) -> bool:
        """Check if instance exists matching filter criteria.

        Args:
            **filters: Filter criteria as keyword arguments

        Returns:
            True if exists, False otherwise
        """
        return self.count(**filters) > 0
