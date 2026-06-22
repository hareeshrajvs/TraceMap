from __future__ import annotations

import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from tracemap.config import ensure_data_dirs, get_settings


class Base(DeclarativeBase):
    pass


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False)
    source_ref = Column(String(512), nullable=False)
    doc_hash = Column(String(64), nullable=False)
    metadata_json = Column(Text, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    test_cases = relationship(
        "TestCase", back_populates="requirement", cascade="all, delete-orphan"
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    pre_conditions = Column(Text)
    steps = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=False)
    test_type = Column(String(50), default="positive")

    requirement = relationship("Requirement", back_populates="test_cases")
    runs = relationship("TestRun", back_populates="test_case", cascade="all, delete-orphan")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_case_id = Column(String, ForeignKey("test_cases.id", ondelete="CASCADE"))
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), nullable=False)
    execution_logs = Column(Text)

    test_case = relationship("TestCase", back_populates="runs")
    defects = relationship("Defect", back_populates="test_run", cascade="all, delete-orphan")


class Defect(Base):
    __tablename__ = "defects"

    jira_key = Column(String(50), primary_key=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id", ondelete="CASCADE"))
    status = Column(String(50), default="Open")
    severity = Column(String(50))

    test_run = relationship("TestRun", back_populates="defects")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_ref = Column(String(512), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)
    requirements_count = Column(Integer, default=0)
    test_cases_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)


class DocumentHash(Base):
    __tablename__ = "document_hashes"

    source_ref = Column(String(512), primary_key=True)
    doc_hash = Column(String(64), nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        ensure_data_dirs()
        settings = get_settings()
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            rel = db_url.replace("sqlite:///", "")
            from pathlib import Path

            from tracemap.config import PROJECT_ROOT

            path = Path(rel)
            if not path.is_absolute():
                db_url = f"sqlite:///{PROJECT_ROOT / rel}"
        _engine = create_engine(db_url, connect_args={"check_same_thread": False})

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_db_session():
    factory = get_session_factory()
    return factory()
