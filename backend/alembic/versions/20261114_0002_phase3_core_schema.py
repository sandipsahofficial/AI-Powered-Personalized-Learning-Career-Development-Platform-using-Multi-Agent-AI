"""Phase 3 Core Relational Schema and HNSW Vector Indexes

Revision ID: 0002_phase3_core_schema
Revises: 0001_baseline_infra
Create Date: 2026-11-14 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = '0002_phase3_core_schema'
down_revision: Union[str, None] = '0001_baseline_infra'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. User role enum
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
                CREATE TYPE user_role_enum AS ENUM ('STUDENT', 'MENTOR', 'ORG_ADMIN', 'SYS_ADMIN');
            END IF;
        END $$;
    """)

    # 2. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # 3. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('role', sa.Enum('STUDENT', 'MENTOR', 'ORG_ADMIN', 'SYS_ADMIN', name='user_role_enum', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # 4. User Profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('headline', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('target_career_title', sa.String(255), nullable=True),
        sa.Column('hours_per_week_commitment', sa.Integer(), default=10),
        sa.Column('preferred_learning_style', sa.String(50), default='BALANCED'),
        sa.Column('raw_resume_text', sa.Text(), nullable=True),
        sa.Column('profile_embedding', Vector(768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. User Preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('email_notifications', sa.Boolean(), default=True),
        sa.Column('theme', sa.String(20), default='dark'),
        sa.Column('ai_coaching_frequency', sa.String(50), default='WEEKLY'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 6. User Sessions & Refresh Tokens
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_token', sa.String(255), unique=True, nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), default=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_user_sessions_token', 'user_sessions', ['session_token'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('is_revoked', sa.Boolean(), default=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_refresh_tokens_hash', 'refresh_tokens', ['token_hash'])

    # 7. Organization Memberships
    op.create_table(
        'organization_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_in_org', sa.String(50), default='MEMBER'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Skill Categories & Skills
    op.create_table(
        'skill_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )

    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skill_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(150), unique=True, nullable=False),
        sa.Column('slug', sa.String(150), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), default=1),
        sa.Column('skill_embedding', Vector(768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skills_name', 'skills', ['name'])

    # 9. Skill Prerequisites & User Skills
    op.create_table(
        'skill_prerequisites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prerequisite_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('dependency_strength', sa.String(20), default='MANDATORY'),
        sa.UniqueConstraint('skill_id', 'prerequisite_skill_id', name='uq_skill_prereq')
    )

    op.create_table(
        'user_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('proficiency_level', sa.Integer(), default=1),
        sa.Column('confidence_score', sa.Float(), default=0.50),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source', sa.String(50), default='SELF_REPORTED'),
        sa.Column('last_assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'skill_id', name='uq_user_skill')
    )

    # 10. Skill Assessments & Verifications
    op.create_table(
        'skill_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('passing_score', sa.Float(), default=70.0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'skill_assessment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skill_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'skill_verification_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('verifier_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Career Roles & Benchmarks
    op.create_table(
        'career_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )

    op.create_table(
        'career_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(200), unique=True, nullable=False),
        sa.Column('slug', sa.String(200), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry_demand_level', sa.String(20), default='HIGH'),
        sa.Column('average_salary_range', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'career_skill_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('career_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('required_proficiency', sa.Integer(), default=2),
        sa.Column('importance_weight', sa.Float(), default=1.0),
        sa.Column('is_mandatory', sa.Boolean(), default=True),
        sa.UniqueConstraint('career_role_id', 'skill_id', name='uq_role_skill')
    )

    op.create_table(
        'career_benchmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('career_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('benchmark_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'user_career_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('career_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('target_completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(30), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'career_matching_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('career_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_percentage', sa.Float(), nullable=False),
        sa.Column('gap_summary', postgresql.JSONB(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. Learning Resources & Roadmaps
    op.create_table(
        'resource_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )

    op.create_table(
        'learning_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resource_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('difficulty_level', sa.Integer(), default=1),
        sa.Column('estimated_minutes', sa.Integer(), default=30),
        sa.Column('provider_name', sa.String(150), nullable=True),
        sa.Column('rating', sa.Float(), default=4.5),
        sa.Column('is_free', sa.Boolean(), default=True),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('content_embedding', Vector(768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'learning_roadmaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('career_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('status', sa.String(30), default='ACTIVE'),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('total_estimated_hours', sa.Integer(), default=0),
        sa.Column('progress_percentage', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'roadmap_milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('roadmap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('phase_number', sa.Integer(), default=1),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deliverable_title', sa.String(255), nullable=True),
        sa.Column('deliverable_criteria', sa.Text(), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), default=10),
        sa.Column('status', sa.String(30), default='LOCKED'),
        sa.Column('is_remedial', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'milestone_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roadmap_milestones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('display_order', sa.Integer(), default=1),
        sa.Column('is_mandatory', sa.Boolean(), default=True),
        sa.UniqueConstraint('milestone_id', 'resource_id', name='uq_milestone_resource')
    )

    op.create_table(
        'learning_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roadmap_milestones.id', ondelete='SET NULL'), nullable=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('time_spent_minutes', sa.Integer(), default=0),
        sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'learning_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roadmap_milestones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('completion_percentage', sa.Float(), default=0.0),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'course_completion_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('roadmap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('certificate_hash', sa.String(255), nullable=True),
    )

    op.create_table(
        'learning_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. Assessments & Question Items
    op.create_table(
        'assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roadmap_milestones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('assessment_type', sa.String(50), default='QUIZ'),
        sa.Column('passing_score', sa.Float(), default=70.0),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'assessment_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(20), default='MCQ'),
        sa.Column('points', sa.Float(), default=1.0),
        sa.Column('order_index', sa.Integer(), default=1),
    )

    op.create_table(
        'assessment_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), default=False),
        sa.Column('explanation', sa.Text(), nullable=True),
    )

    op.create_table(
        'assessment_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(30), default='IN_PROGRESS'),
    )

    op.create_table(
        'assessment_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_option_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_options.id', ondelete='SET NULL'), nullable=True),
        sa.Column('submitted_text', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), default=False),
        sa.Column('awarded_points', sa.Float(), default=0.0),
    )

    op.create_table(
        'assessment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('ai_evaluator_feedback', sa.Text(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 14. AI Agents Logs & Recommendations
    op.create_table(
        'agent_execution_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(30), default='SUCCESS'),
        sa.Column('execution_time_ms', sa.Integer(), default=0),
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'agent_execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_execution_history.id', ondelete='CASCADE'), nullable=False),
        sa.Column('log_level', sa.String(20), default='INFO'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'ai_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'recommendation_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_action', sa.String(30), nullable=False),
        sa.Column('action_timestamp', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'adaptive_replanning_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('roadmap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trigger_reason', sa.String(100), nullable=False),
        sa.Column('prior_milestone_count', sa.Integer(), nullable=False),
        sa.Column('new_milestone_count', sa.Integer(), nullable=False),
        sa.Column('replanned_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'ai_mentor_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_title', sa.String(255), default='Career & Learning Mentorship'),
        sa.Column('messages_history', postgresql.JSONB(), nullable=False),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Gamification & Notifications
    op.create_table(
        'user_gamification',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('current_xp', sa.Integer(), default=0),
        sa.Column('current_level', sa.Integer(), default=1),
        sa.Column('streak_days', sa.Integer(), default=0),
        sa.Column('last_activity_date', sa.Date(), nullable=True),
        sa.Column('badges_unlocked', postgresql.JSONB(), default=list),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'points_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('points_amount', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('awarded_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'achievement_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_code', sa.String(50), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(50), default='SYSTEM'),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'user_activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_target', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )

    # 16. HNSW Vector Indexes (m = 16, ef_construction = 64)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_skills_embedding_hnsw 
        ON skills USING hnsw (skill_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_resources_embedding_hnsw 
        ON learning_resources USING hnsw (content_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_profiles_embedding_hnsw 
        ON user_profiles USING hnsw (profile_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_profiles_embedding_hnsw;")
    op.execute("DROP INDEX IF EXISTS idx_resources_embedding_hnsw;")
    op.execute("DROP INDEX IF EXISTS idx_skills_embedding_hnsw;")

    tables = [
        'user_activity_logs', 'notifications', 'achievement_records', 'points_history', 'user_gamification',
        'ai_mentor_conversations', 'adaptive_replanning_events', 'recommendation_history', 'ai_recommendations',
        'agent_execution_logs', 'agent_execution_history',
        'assessment_results', 'assessment_answers', 'assessment_attempts', 'assessment_options', 'assessment_questions', 'assessments',
        'learning_history', 'course_completion_records', 'learning_progress', 'learning_activities', 'milestone_resources',
        'roadmap_milestones', 'learning_roadmaps', 'learning_resources', 'resource_categories',
        'career_matching_results', 'user_career_goals', 'career_benchmarks', 'career_skill_requirements', 'career_roles', 'career_categories',
        'skill_verification_records', 'skill_assessment_results', 'skill_assessments', 'user_skills', 'skill_prerequisites', 'skills', 'skill_categories',
        'organization_memberships', 'refresh_tokens', 'user_sessions', 'user_preferences', 'user_profiles', 'users', 'organizations'
    ]
    for table in tables:
        op.drop_table(table)

    op.execute('DROP TYPE IF EXISTS user_role_enum;')
