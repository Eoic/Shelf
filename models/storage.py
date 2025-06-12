from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String

from database.base import Base


class Storage(Base):
    __tablename__ = "storage"

    id = Column(Integer, primary_key=True, index=True)
    config = Column(JSON, nullable=False)
    storage_type = Column(String, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_default = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates whether this is the primary (default) storage for the user. Only one storage entry per user can have this set to True.",
    )

    def __repr__(self):
        return f"<Storage(id={self.id}, user_id={self.user_id}, type={self.type}, primary={self.is_default})>"
