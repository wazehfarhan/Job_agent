"""Initial schema — 12 tables, 5 enum types, indexes, pgvector extension.

Revision ID: 0001
Revises:
Create Date: 2026-09-21

Hand-written to match app/models exactly (autogenerate needs a live DB —
Todo T0.2). Run `alembic upgrade head` against a Postgres started from
docker-compose (pgvector/pgvector:pg16), which ships the vector extension.
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

ENUMS = {
    "workmode": ("remote", "hybrid", "onsite", "unspecified"),
    "employmenttype": ("internship", "full_time", "part_time", "contract", "unspecified"),
    "jobstatus": (
        "discovered", "extracted", "duplicate", "matched", "ineligible", "expired",
    ),
    "applicationstatus": (
        "discovered", "analyzing", "matched", "preparing", "awaiting_approval",
        "approved", "submitting", "applied", "interview", "rejected",
        "withdrawn", "failed", "needs_user_action",
    ),
    "skillcategory": (
        "programming_language", "framework", "library", "database", "cloud",
        "ai_ml", "nlp", "devops", "testing", "other",
    ),
}

# Reverse dependency order for downgrade().
TABLE_ORDER = [
    "preferences", "projects", "experiences", "skills", "certifications",
    "educations", "status_events", "applications", "profiles", "resumes",
    "jobs", "users",
]


def _enum(name: str) -> postgresql.ENUM:
    # Types are created explicitly in upgrade(); create_type=False avoids
    # double-creation when two tables share one enum (applicationstatus).
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


def _pk() -> list[sa.Column]:
    """id + created_at/updated_at from TimestampedBase (app/models/base.py)."""
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    for name, values in ENUMS.items():
        rendered = ", ".join(f"'{value}'" for value in values)
        op.execute(f"CREATE TYPE {name} AS ENUM ({rendered})")

    op.create_table(
        "users",
        *_pk(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "jobs",
        *_pk(),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_job_id", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("work_mode", _enum("workmode"), server_default="unspecified", nullable=False),
        sa.Column("employment_type", _enum("employmenttype"), server_default="unspecified", nullable=False),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("required_skills", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_skills", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("experience_requirement", sa.Text(), nullable=True),
        sa.Column("education_requirement", sa.Text(), nullable=True),
        sa.Column("deadline", sa.String(length=50), nullable=True),
        sa.Column("application_url", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.String(length=50), nullable=True),
        sa.Column("discovered_at", sa.String(length=50), nullable=True),
        sa.Column("status", _enum("jobstatus"), server_default="discovered", nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
    )
    for column in ("source", "source_job_id", "company", "title", "status", "content_hash"):
        op.create_index(op.f(f"ix_jobs_{column}"), "jobs", [column])
    op.create_index(
        "ix_jobs_embedding",
        "jobs",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


    op.create_table(
        "resumes",
        *_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=10), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("structured_data", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"])

    op.create_table(
        "profiles",
        *_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("portfolio_url", sa.String(length=500), nullable=True),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("other_links", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.create_index(op.f("ix_profiles_user_id"), "profiles", ["user_id"], unique=True)

    op.create_table(
        "applications",
        *_pk(),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", _enum("applicationstatus"), server_default="discovered", nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("answers_json", sa.Text(), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("match_category", sa.String(length=20), nullable=True),
        sa.Column("match_reasons", postgresql.ARRAY(sa.Text()), nullable=True),
    )
    for column in ("job_id", "user_id", "status"):
        op.create_index(op.f(f"ix_applications_{column}"), "applications", [column])

    op.create_table(
        "status_events",
        *_pk(),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("status", _enum("applicationstatus"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_status_events_application_id"), "status_events", ["application_id"])


    op.create_table(
        "educations",
        *_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("institution", sa.String(length=255), nullable=True),
        sa.Column("degree", sa.String(length=255), nullable=True),
        sa.Column("field", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=50), nullable=True),
        sa.Column("expected_graduation", sa.String(length=50), nullable=True),
        sa.Column("gpa", sa.Numeric(3, 2), nullable=True),
    )
    op.create_index(op.f("ix_educations_profile_id"), "educations", ["profile_id"])

    op.create_table(
        "certifications",
        *_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("issuer", sa.String(length=255), nullable=True),
        sa.Column("date", sa.String(length=50), nullable=True),
        sa.Column("credential_url", sa.String(length=500), nullable=True),
    )
    op.create_index(op.f("ix_certifications_profile_id"), "certifications", ["profile_id"])

    op.create_table(
        "skills",
        *_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("category", _enum("skillcategory"), server_default="other", nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
    )
    op.create_index(op.f("ix_skills_profile_id"), "skills", ["profile_id"])

    op.create_table(
        "experiences",
        *_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("position", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=50), nullable=True),
        sa.Column("end_date", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("skills_used", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("achievements", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.create_index(op.f("ix_experiences_profile_id"), "experiences", ["profile_id"])

    op.create_table(
        "projects",
        *_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("responsibilities", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("achievements", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.create_index(op.f("ix_projects_profile_id"), "projects", ["profile_id"])

    op.create_table(
        "preferences",
        *_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("target_roles", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("job_types", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("internship_types", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_locations", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("work_modes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("min_salary", sa.Float(), nullable=True),
        sa.Column("min_stipend", sa.Float(), nullable=True),
        sa.Column("preferred_industries", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("excluded_companies", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("excluded_roles", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("min_match_score", sa.Integer(), nullable=True),
    )
    op.create_index(op.f("ix_preferences_profile_id"), "preferences", ["profile_id"], unique=True)


def downgrade() -> None:
    # Indexes drop with their tables; reverse dependency order matters.
    for table in TABLE_ORDER:
        op.drop_table(table)
    for name in ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {name}")