from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Storage(Base):
    __tablename__ = "storage"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    config: Mapped[Any] = mapped_column(JSON, nullable=False)
    storage_type: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates whether this is the primary (default) storage for the user. Only one storage entry per user can have this set to True.",
    )

    def __repr__(self):
        return f"<Storage(id={self.id}, user_id={self.user_id}, type={self.storage_type}, primary={self.is_default})>"
