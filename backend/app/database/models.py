from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


json_type = JSON().with_variant(JSONB, "postgresql")


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(201), unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    github_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reports: Mapped[list["AnalysisReport"]] = relationship(back_populates="repository")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"))
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    health_score: Mapped[int | None] = mapped_column(Integer)
    coverage: Mapped[int] = mapped_column(Integer, nullable=False)
    classification: Mapped[str] = mapped_column(String(40), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    dimensions: Mapped[dict] = mapped_column(json_type, nullable=False)
    data_completeness: Mapped[dict] = mapped_column(json_type, nullable=False)
    report_data: Mapped[dict] = mapped_column(json_type, nullable=False)
    repository: Mapped[Repository] = relationship(back_populates="reports")
    dimension_scores: Mapped[list["DimensionScore"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class DimensionScore(Base):
    __tablename__ = "dimension_scores"

    report_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_reports.id", ondelete="CASCADE"), primary_key=True
    )
    dimension: Mapped[str] = mapped_column(String(32), primary_key=True)
    score: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    report: Mapped[AnalysisReport] = relationship(back_populates="dimension_scores")


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("report_id", "code", "source_url", name="uq_finding_report_code_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_reports.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(12), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[dict] = mapped_column(json_type, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    report: Mapped[AnalysisReport] = relationship(back_populates="findings")
    insight: Mapped["Insight | None"] = relationship(
        back_populates="finding", cascade="all, delete-orphan", uselist=False
    )


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), unique=True
    )
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False)
    finding: Mapped[Finding] = relationship(back_populates="insight")
