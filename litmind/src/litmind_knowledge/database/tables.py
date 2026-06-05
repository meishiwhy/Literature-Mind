"""SQLAlchemy ORM 表定义"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class PaperTable(Base):
    __tablename__ = "papers"

    paper_id = Column(String(255), primary_key=True)
    title = Column(Text, default="")
    year = Column(Integer, nullable=True)
    journal = Column(Text, default="")
    doi = Column(Text, default="")
    research_question = Column(Text, default="")
    research_domain = Column(Text, default="")
    study_design = Column(Text, default="")
    sample_size = Column(Integer, nullable=True)
    population = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    variables = relationship("VariableTable", back_populates="paper", cascade="all, delete-orphan")
    statistics = relationship("StatisticTable", back_populates="paper", cascade="all, delete-orphan")
    claims = relationship("ClaimTable", back_populates="paper", cascade="all, delete-orphan")
    keywords = relationship("KeywordTable", back_populates="paper", cascade="all, delete-orphan")
    limitations = relationship("LimitationTable", back_populates="paper", cascade="all, delete-orphan")
    future_directions = relationship("FutureDirectionTable", back_populates="paper", cascade="all, delete-orphan")


class VariableTable(Base):
    __tablename__ = "variables"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    variable = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="variables")


class StatisticTable(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    method = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="statistics")


class ClaimTable(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    statement = Column(Text, nullable=False)
    direction = Column(Text, default="")
    evidence_source = Column(Text, default="")
    paper = relationship("PaperTable", back_populates="claims")


class KeywordTable(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    keyword = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="keywords")


class LimitationTable(Base):
    __tablename__ = "limitations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    limitation = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="limitations")


class FutureDirectionTable(Base):
    __tablename__ = "future_directions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    future_direction = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="future_directions")
