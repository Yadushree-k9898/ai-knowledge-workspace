from sqlalchemy import Column, Integer
from app.db.base import Base

class DocumentJob(Base):
    __tablename__ = "document_jobs"
    id = Column(Integer, primary_key=True)
