"""
Profile database model.

This represents the application-level user profile.
The `id` field corresponds to the Supabase Auth user UUID —
we do NOT auto-generate it; it comes from the verified JWT.
"""

from sqlalchemy import Column, String, DateTime, func, Text
from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    # UUID from Supabase Auth (the `sub` claim in the JWT)
    id = Column(String, primary_key=True, index=True)

    display_name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} display_name={self.display_name!r}>"
