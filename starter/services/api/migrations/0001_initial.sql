-- CiteTrace canonical PostgreSQL schema
-- Target: PostgreSQL 18.x + pgvector 0.8.x
-- This file is the authoritative relational contract for the v1 foundation.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS citetrace;
SET search_path TO citetrace, public;

CREATE TYPE membership_role AS ENUM ('owner', 'admin', 'researcher', 'reviewer', 'viewer');
CREATE TYPE work_type AS ENUM ('journal_article', 'conference_paper', 'preprint', 'thesis', 'book', 'book_chapter', 'dataset', 'software', 'web_resource', 'other');
CREATE TYPE version_kind AS ENUM ('publisher_version', 'accepted_manuscript', 'submitted_manuscript', 'preprint', 'repository_copy', 'correction', 'retraction_notice', 'other');
CREATE TYPE access_level AS ENUM ('user_private_full_text', 'open_access_full_text', 'repository_manuscript', 'publisher_open_full_text', 'abstract_only', 'metadata_only', 'not_accessible');
CREATE TYPE acquisition_method AS ENUM ('user_upload', 'open_repository', 'publisher_open', 'provider_abstract', 'provider_metadata', 'manual_registration');
CREATE TYPE security_scan_status AS ENUM ('pending', 'clean', 'rejected_malware', 'rejected_content', 'failed');
CREATE TYPE parse_quality_grade AS ENUM ('a', 'b', 'c', 'd');
CREATE TYPE node_type AS ENUM ('document', 'section', 'heading', 'paragraph', 'sentence', 'caption', 'equation', 'algorithm', 'table', 'table_region', 'figure', 'list_item', 'footnote', 'bibliography_entry', 'other');
CREATE TYPE resolution_status AS ENUM ('resolved', 'resolved_with_version_uncertainty', 'ambiguous', 'unresolved', 'not_a_scholarly_work', 'user_confirmed');
CREATE TYPE resolution_method AS ENUM ('automatic', 'user_confirmed', 'adjudicated');
CREATE TYPE analysis_mode AS ENUM ('understand', 'implement', 'review', 'survey', 'present');
CREATE TYPE audience_level AS ENUM ('beginner', 'intermediate', 'expert');
CREATE TYPE analysis_status AS ENUM ('created', 'validating', 'parsing', 'resolving_references', 'acquiring_sources', 'retrieving_evidence', 'verifying_relations', 'generating_explanations', 'auditing', 'completed', 'completed_with_limits', 'failed', 'cancelled');
CREATE TYPE stage_status AS ENUM ('pending', 'running', 'succeeded', 'succeeded_with_limits', 'failed', 'cancelled', 'skipped');
CREATE TYPE evidence_type AS ENUM ('text_span', 'equation', 'table_cell_or_region', 'figure_or_caption', 'algorithm_block', 'appendix_span', 'metadata_field', 'abstract_span');
CREATE TYPE evidence_relation AS ENUM ('direct_support', 'partial_support', 'indirect_support', 'contradicts', 'overgeneralized', 'scope_mismatch', 'no_relevant_evidence', 'insufficient_evidence', 'inaccessible_source');
CREATE TYPE evidence_link_status AS ENUM ('verified', 'limited', 'review_required', 'blocked');
CREATE TYPE citation_intent AS ENUM ('background', 'definition', 'problem_framing', 'method_adoption', 'method_extension', 'dataset_use', 'metric_use', 'benchmark_comparison', 'result_support', 'result_contrast', 'limitation', 'future_direction', 'tool_or_software_use', 'perfunctory_mention');
CREATE TYPE transformation_kind AS ENUM ('adopted_unchanged', 'parameter_changed', 'domain_transferred', 'extended', 'simplified', 'combined', 'benchmark_only', 'dataset_reused', 'metric_reused', 'conceptual_inspiration');
CREATE TYPE explanation_statement_kind AS ENUM ('evidence_based', 'inference', 'limitation', 'instruction');
CREATE TYPE audit_status AS ENUM ('pending', 'passed', 'passed_with_warnings', 'blocked');
CREATE TYPE feedback_category AS ENUM ('overall', 'reference_resolution', 'claim_span', 'source_evidence', 'relation', 'transformation', 'missing_evidence', 'nuance', 'explanation', 'access', 'other');
CREATE TYPE outbox_status AS ENUM ('pending', 'published', 'failed');

CREATE TABLE workspace (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 200),
    slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
    retention_profile text NOT NULL DEFAULT 'standard-30d',
    source_policy_profile text NOT NULL DEFAULT 'lawful-open-or-user-upload',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE app_user (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_subject text NOT NULL UNIQUE,
    email citext,
    display_name text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE membership (
    workspace_id uuid NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    role membership_role NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE scholarly_work (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_title text NOT NULL,
    primary_authors jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(primary_authors) = 'array'),
    first_publication_year integer CHECK (first_publication_year BETWEEN 1400 AND 2200),
    work_type work_type NOT NULL DEFAULT 'other',
    identifiers jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(identifiers) = 'object'),
    metadata_provenance jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata_provenance) = 'object'),
    merged_into_work_id uuid REFERENCES scholarly_work(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX scholarly_work_title_trgm_idx ON scholarly_work USING gin (normalized_title gin_trgm_ops);

CREATE TABLE work_version (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id uuid NOT NULL REFERENCES scholarly_work(id) ON DELETE CASCADE,
    version_kind version_kind NOT NULL,
    version_label text,
    title text NOT NULL,
    authors jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(authors) = 'array'),
    publication_date date,
    publication_year integer CHECK (publication_year BETWEEN 1400 AND 2200),
    venue text,
    identifiers jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(identifiers) = 'object'),
    status_notices jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(status_notices) = 'array'),
    predecessor_version_id uuid REFERENCES work_version(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (work_id, version_kind, version_label)
);

CREATE UNIQUE INDEX work_version_doi_unique_idx
    ON work_version ((lower(identifiers->>'doi')))
    WHERE identifiers ? 'doi';
CREATE UNIQUE INDEX work_version_arxiv_unique_idx
    ON work_version ((lower(identifiers->>'arxiv')))
    WHERE identifiers ? 'arxiv';

CREATE TABLE source_asset (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    work_version_id uuid REFERENCES work_version(id),
    sha256 char(64) NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    media_type text NOT NULL,
    byte_size bigint NOT NULL CHECK (byte_size > 0 AND byte_size <= 104857600),
    object_key text,
    acquisition_method acquisition_method NOT NULL,
    source_url text,
    final_url text,
    access_level access_level NOT NULL,
    license_spdx text,
    license_url text,
    terms_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(terms_snapshot) = 'object'),
    acquired_at timestamptz NOT NULL DEFAULT now(),
    security_scan_status security_scan_status NOT NULL DEFAULT 'pending',
    quarantine_reason text,
    retention_expires_at timestamptz,
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, sha256)
);

CREATE INDEX source_asset_work_version_idx ON source_asset(work_version_id);
CREATE INDEX source_asset_retention_idx ON source_asset(retention_expires_at) WHERE deleted_at IS NULL;

CREATE TABLE parsed_document (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id uuid NOT NULL REFERENCES source_asset(id) ON DELETE CASCADE,
    parser_name text NOT NULL,
    parser_version text NOT NULL,
    parser_profile text NOT NULL,
    parser_options jsonb NOT NULL DEFAULT '{}'::jsonb,
    raw_artifact_key text,
    normalized_artifact_key text,
    normalized_text text NOT NULL,
    normalized_text_sha256 char(64) NOT NULL CHECK (normalized_text_sha256 ~ '^[a-f0-9]{64}$'),
    parse_quality_grade parse_quality_grade NOT NULL,
    parse_quality_features jsonb NOT NULL DEFAULT '{}'::jsonb,
    coordinate_coverage numeric(5,4) NOT NULL DEFAULT 0 CHECK (coordinate_coverage BETWEEN 0 AND 1),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_asset_id, parser_name, parser_version, parser_profile, normalized_text_sha256)
);

CREATE TABLE parsed_node (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parsed_document_id uuid NOT NULL REFERENCES parsed_document(id) ON DELETE CASCADE,
    parent_id uuid REFERENCES parsed_node(id) ON DELETE CASCADE,
    node_type node_type NOT NULL,
    order_index integer NOT NULL CHECK (order_index >= 0),
    section_path text[] NOT NULL DEFAULT '{}',
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    page_start integer CHECK (page_start >= 1),
    page_end integer CHECK (page_end >= page_start),
    bounding_boxes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(bounding_boxes) = 'array'),
    text_content text NOT NULL,
    text_sha256 char(64) NOT NULL CHECK (text_sha256 ~ '^[a-f0-9]{64}$'),
    UNIQUE (parsed_document_id, order_index, node_type)
);

CREATE INDEX parsed_node_offsets_idx ON parsed_node(parsed_document_id, start_offset, end_offset);
CREATE INDEX parsed_node_parent_idx ON parsed_node(parent_id);

CREATE TABLE reference_entry (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parsed_document_id uuid NOT NULL REFERENCES parsed_document(id) ON DELETE CASCADE,
    bibliography_node_id uuid REFERENCES parsed_node(id),
    local_label text NOT NULL,
    raw_reference text NOT NULL,
    parsed_title text,
    parsed_authors jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(parsed_authors) = 'array'),
    parsed_year integer CHECK (parsed_year BETWEEN 1400 AND 2200),
    parsed_venue text,
    parsed_identifiers jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(parsed_identifiers) = 'object'),
    parser_confidence numeric(5,4) NOT NULL CHECK (parser_confidence BETWEEN 0 AND 1),
    start_offset integer CHECK (start_offset >= 0),
    end_offset integer CHECK (end_offset > start_offset),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parsed_document_id, local_label)
);

CREATE TABLE citation_cluster (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parsed_document_id uuid NOT NULL REFERENCES parsed_document(id) ON DELETE CASCADE,
    anchor_text text NOT NULL,
    citation_style text,
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    page integer CHECK (page >= 1),
    bounding_boxes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(bounding_boxes) = 'array'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE citation_anchor (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citation_cluster_id uuid NOT NULL REFERENCES citation_cluster(id) ON DELETE CASCADE,
    reference_entry_id uuid NOT NULL REFERENCES reference_entry(id) ON DELETE CASCADE,
    parser_link_confidence numeric(5,4) NOT NULL CHECK (parser_link_confidence BETWEEN 0 AND 1),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (citation_cluster_id, reference_entry_id)
);

CREATE TABLE reference_candidate (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_entry_id uuid NOT NULL REFERENCES reference_entry(id) ON DELETE CASCADE,
    provider text NOT NULL,
    provider_record_id text NOT NULL,
    proposed_work_version_id uuid REFERENCES work_version(id),
    metadata_snapshot jsonb NOT NULL CHECK (jsonb_typeof(metadata_snapshot) = 'object'),
    feature_scores jsonb NOT NULL CHECK (jsonb_typeof(feature_scores) = 'object'),
    total_score numeric(7,6) NOT NULL CHECK (total_score BETWEEN 0 AND 1),
    hard_conflicts text[] NOT NULL DEFAULT '{}',
    provider_provenance jsonb NOT NULL CHECK (jsonb_typeof(provider_provenance) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (reference_entry_id, provider, provider_record_id)
);

CREATE INDEX reference_candidate_rank_idx ON reference_candidate(reference_entry_id, total_score DESC);

CREATE TABLE reference_resolution (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_entry_id uuid NOT NULL REFERENCES reference_entry(id) ON DELETE CASCADE,
    status resolution_status NOT NULL,
    selected_work_version_id uuid REFERENCES work_version(id),
    selected_candidate_id uuid REFERENCES reference_candidate(id),
    absolute_score numeric(7,6) CHECK (absolute_score BETWEEN 0 AND 1),
    score_margin numeric(7,6) CHECK (score_margin BETWEEN 0 AND 1),
    threshold_profile text NOT NULL,
    decision_method resolution_method NOT NULL,
    decision_reason_codes text[] NOT NULL DEFAULT '{}',
    superseded_by_id uuid REFERENCES reference_resolution(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        (status IN ('resolved', 'resolved_with_version_uncertainty', 'user_confirmed') AND selected_work_version_id IS NOT NULL)
        OR (status IN ('ambiguous', 'unresolved', 'not_a_scholarly_work') AND selected_work_version_id IS NULL)
    )
);

CREATE UNIQUE INDEX reference_resolution_current_idx
    ON reference_resolution(reference_entry_id)
    WHERE superseded_by_id IS NULL;

CREATE TABLE citing_claim (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citation_cluster_id uuid NOT NULL REFERENCES citation_cluster(id) ON DELETE CASCADE,
    citation_anchor_id uuid REFERENCES citation_anchor(id) ON DELETE CASCADE,
    parsed_document_id uuid NOT NULL REFERENCES parsed_document(id) ON DELETE CASCADE,
    claim_text text NOT NULL,
    normalized_claim text NOT NULL,
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    page integer CHECK (page >= 1),
    qualifiers jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(qualifiers) = 'array'),
    structured_scope jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(structured_scope) = 'object'),
    claim_strength numeric(5,4) NOT NULL DEFAULT 0.5 CHECK (claim_strength BETWEEN 0 AND 1),
    extractor_name text NOT NULL,
    extractor_version text NOT NULL,
    prompt_version text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX citing_claim_document_idx ON citing_claim(parsed_document_id, start_offset);

CREATE TABLE source_chunk (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parsed_document_id uuid NOT NULL REFERENCES parsed_document(id) ON DELETE CASCADE,
    parsed_node_id uuid REFERENCES parsed_node(id) ON DELETE SET NULL,
    section_path text[] NOT NULL DEFAULT '{}',
    evidence_type evidence_type NOT NULL,
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    page integer CHECK (page >= 1),
    bounding_boxes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(bounding_boxes) = 'array'),
    chunk_text text NOT NULL,
    chunk_sha256 char(64) NOT NULL CHECK (chunk_sha256 ~ '^[a-f0-9]{64}$'),
    search_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(chunk_text, ''))) STORED,
    embedding vector(1536),
    embedding_profile text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parsed_document_id, start_offset, end_offset, chunk_sha256)
);

CREATE INDEX source_chunk_fts_idx ON source_chunk USING gin(search_tsv);
CREATE INDEX source_chunk_vector_idx ON source_chunk USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL;

CREATE TABLE query_plan (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citing_claim_id uuid NOT NULL REFERENCES citing_claim(id) ON DELETE CASCADE,
    plan_version text NOT NULL,
    lexical_queries jsonb NOT NULL CHECK (jsonb_typeof(lexical_queries) = 'array'),
    semantic_queries jsonb NOT NULL CHECK (jsonb_typeof(semantic_queries) = 'array'),
    entity_constraints jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(entity_constraints) = 'object'),
    section_hints text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE evidence_candidate (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citing_claim_id uuid NOT NULL REFERENCES citing_claim(id) ON DELETE CASCADE,
    source_chunk_id uuid NOT NULL REFERENCES source_chunk(id) ON DELETE CASCADE,
    query_plan_id uuid NOT NULL REFERENCES query_plan(id) ON DELETE CASCADE,
    lexical_score numeric(7,6) CHECK (lexical_score BETWEEN 0 AND 1),
    vector_score numeric(7,6) CHECK (vector_score BETWEEN 0 AND 1),
    entity_score numeric(7,6) CHECK (entity_score BETWEEN 0 AND 1),
    merged_rank integer NOT NULL CHECK (merged_rank >= 1),
    reranker_score numeric(7,6) CHECK (reranker_score BETWEEN 0 AND 1),
    reranker_version text,
    candidate_status text NOT NULL CHECK (candidate_status IN ('retrieved', 'shortlisted', 'accepted', 'rejected')),
    rejection_reason_codes text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (citing_claim_id, source_chunk_id, query_plan_id)
);

CREATE INDEX evidence_candidate_rank_idx ON evidence_candidate(citing_claim_id, merged_rank, reranker_score DESC NULLS LAST);

CREATE TABLE analysis_run (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    source_asset_id uuid NOT NULL REFERENCES source_asset(id),
    parsed_document_id uuid REFERENCES parsed_document(id),
    mode analysis_mode NOT NULL,
    audience audience_level NOT NULL,
    requested_scope jsonb NOT NULL CHECK (jsonb_typeof(requested_scope) = 'object'),
    source_policy_profile text NOT NULL,
    pipeline_version text NOT NULL,
    status analysis_status NOT NULL DEFAULT 'created',
    progress jsonb NOT NULL DEFAULT '{"stage":"created","completed_units":0,"total_units":0,"percent":0}'::jsonb,
    limitations jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(limitations) = 'array'),
    idempotency_key text NOT NULL,
    input_fingerprint char(64) NOT NULL CHECK (input_fingerprint ~ '^[a-f0-9]{64}$'),
    total_cost_usd numeric(12,6) NOT NULL DEFAULT 0 CHECK (total_cost_usd >= 0),
    started_at timestamptz,
    completed_at timestamptz,
    cancelled_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, idempotency_key)
);

CREATE INDEX analysis_run_status_idx ON analysis_run(workspace_id, status, created_at DESC);

CREATE TABLE analysis_stage_run (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id uuid NOT NULL REFERENCES analysis_run(id) ON DELETE CASCADE,
    stage_name text NOT NULL,
    attempt integer NOT NULL CHECK (attempt >= 1),
    input_fingerprint char(64) NOT NULL CHECK (input_fingerprint ~ '^[a-f0-9]{64}$'),
    output_artifact_ids jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(output_artifact_ids) = 'array'),
    status stage_status NOT NULL DEFAULT 'pending',
    error_code text,
    error_detail_safe text,
    trace_id text,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (analysis_run_id, stage_name, attempt)
);

CREATE TABLE model_execution (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_stage_run_id uuid REFERENCES analysis_stage_run(id) ON DELETE SET NULL,
    purpose text NOT NULL,
    provider text NOT NULL,
    model_id text NOT NULL,
    model_version text,
    route_profile text NOT NULL,
    prompt_template text NOT NULL,
    prompt_version text NOT NULL,
    input_artifact_hashes jsonb NOT NULL CHECK (jsonb_typeof(input_artifact_hashes) = 'array'),
    output_schema_version text NOT NULL,
    input_tokens integer CHECK (input_tokens >= 0),
    output_tokens integer CHECK (output_tokens >= 0),
    latency_ms integer CHECK (latency_ms >= 0),
    cost_usd numeric(12,6) CHECK (cost_usd >= 0),
    validation_status text NOT NULL CHECK (validation_status IN ('valid', 'repaired', 'invalid', 'blocked')),
    retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    privacy_policy text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE source_span (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id uuid NOT NULL REFERENCES source_asset(id),
    parsed_document_id uuid REFERENCES parsed_document(id),
    evidence_candidate_id uuid REFERENCES evidence_candidate(id),
    access_level access_level NOT NULL,
    evidence_type evidence_type NOT NULL,
    section_path text[] NOT NULL DEFAULT '{}',
    page integer CHECK (page >= 1),
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    bounding_boxes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(bounding_boxes) = 'array'),
    quote text NOT NULL,
    quote_sha256 char(64) NOT NULL CHECK (quote_sha256 ~ '^[a-f0-9]{64}$'),
    validation_status text NOT NULL CHECK (validation_status IN ('pending', 'valid', 'invalid')),
    validator_version text NOT NULL,
    display_restrictions jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(display_restrictions) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_asset_id, start_offset, end_offset, quote_sha256)
);

CREATE TABLE evidence_link (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    analysis_run_id uuid NOT NULL REFERENCES analysis_run(id) ON DELETE CASCADE,
    citing_claim_id uuid NOT NULL REFERENCES citing_claim(id) ON DELETE CASCADE,
    reference_resolution_id uuid REFERENCES reference_resolution(id),
    cited_work_version_id uuid REFERENCES work_version(id),
    status evidence_link_status NOT NULL,
    evidence_relation evidence_relation NOT NULL,
    citation_intents citation_intent[] NOT NULL DEFAULT '{}',
    transformations transformation_kind[] NOT NULL DEFAULT '{}',
    scope_observations jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(scope_observations) = 'array'),
    access_level access_level NOT NULL,
    abstention jsonb,
    confidence_vector jsonb NOT NULL CHECK (jsonb_typeof(confidence_vector) = 'object'),
    calibration_profile text NOT NULL,
    audit_status audit_status NOT NULL DEFAULT 'pending',
    model_execution_ids uuid[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        (evidence_relation = 'inaccessible_source' AND access_level = 'not_accessible')
        OR evidence_relation <> 'inaccessible_source'
    ),
    CHECK (
        (status = 'blocked' AND abstention IS NOT NULL)
        OR status <> 'blocked'
    )
);

CREATE INDEX evidence_link_analysis_idx ON evidence_link(analysis_run_id, created_at);
CREATE INDEX evidence_link_relation_idx ON evidence_link(workspace_id, evidence_relation, status);

CREATE TABLE evidence_link_source_span (
    evidence_link_id uuid NOT NULL REFERENCES evidence_link(id) ON DELETE CASCADE,
    source_span_id uuid NOT NULL REFERENCES source_span(id) ON DELETE RESTRICT,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    role text NOT NULL CHECK (role IN ('primary', 'qualifier', 'contrast', 'context')),
    PRIMARY KEY (evidence_link_id, source_span_id),
    UNIQUE (evidence_link_id, ordinal)
);

CREATE TABLE explanation_statement (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_link_id uuid NOT NULL REFERENCES evidence_link(id) ON DELETE CASCADE,
    statement_kind explanation_statement_kind NOT NULL,
    statement_text text NOT NULL,
    supporting_citing_claim_ids uuid[] NOT NULL DEFAULT '{}',
    supporting_source_span_ids uuid[] NOT NULL DEFAULT '{}',
    confidence numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    model_execution_id uuid REFERENCES model_execution(id),
    prompt_version text NOT NULL,
    audit_status audit_status NOT NULL DEFAULT 'pending',
    display_order integer NOT NULL CHECK (display_order >= 0),
    audience audience_level NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        statement_kind IN ('limitation', 'instruction')
        OR cardinality(supporting_source_span_ids) > 0
    ),
    UNIQUE (evidence_link_id, audience, display_order)
);

CREATE TABLE feedback_event (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    evidence_link_id uuid NOT NULL REFERENCES evidence_link(id) ON DELETE CASCADE,
    actor_user_id uuid REFERENCES app_user(id) ON DELETE SET NULL,
    category feedback_category NOT NULL,
    proposed_relation evidence_relation,
    proposed_source_span jsonb,
    comment text CHECK (comment IS NULL OR char_length(comment) <= 4000),
    idempotency_key text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, idempotency_key)
);

CREATE TABLE audit_decision (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_link_id uuid NOT NULL REFERENCES evidence_link(id) ON DELETE CASCADE,
    auditor_version text NOT NULL,
    status audit_status NOT NULL,
    check_results jsonb NOT NULL CHECK (jsonb_typeof(check_results) = 'array'),
    blocking_codes text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE outbox_event (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type text NOT NULL,
    schema_version text NOT NULL,
    workspace_id uuid REFERENCES workspace(id) ON DELETE CASCADE,
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    status outbox_status NOT NULL DEFAULT 'pending',
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    last_error_safe text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX outbox_pending_idx ON outbox_event(status, available_at) WHERE status IN ('pending', 'failed');

CREATE TABLE schema_registry (
    schema_name text NOT NULL,
    schema_version text NOT NULL,
    sha256 char(64) NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    effective_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (schema_name, schema_version)
);

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER workspace_touch_updated_at BEFORE UPDATE ON workspace
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER app_user_touch_updated_at BEFORE UPDATE ON app_user
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER scholarly_work_touch_updated_at BEFORE UPDATE ON scholarly_work
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER work_version_touch_updated_at BEFORE UPDATE ON work_version
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER analysis_run_touch_updated_at BEFORE UPDATE ON analysis_run
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER evidence_link_touch_updated_at BEFORE UPDATE ON evidence_link
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Session-scoped tenant helper. The API must SET LOCAL app.workspace_id at the
-- beginning of every tenant transaction after authenticating the actor.
CREATE OR REPLACE FUNCTION current_workspace_id() RETURNS uuid
LANGUAGE sql STABLE AS $$
    SELECT nullif(current_setting('app.workspace_id', true), '')::uuid
$$;

ALTER TABLE workspace ENABLE ROW LEVEL SECURITY;
ALTER TABLE membership ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE parsed_document ENABLE ROW LEVEL SECURITY;
ALTER TABLE parsed_node ENABLE ROW LEVEL SECURITY;
ALTER TABLE reference_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE citation_cluster ENABLE ROW LEVEL SECURITY;
ALTER TABLE citation_anchor ENABLE ROW LEVEL SECURITY;
ALTER TABLE reference_candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE reference_resolution ENABLE ROW LEVEL SECURITY;
ALTER TABLE citing_claim ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_chunk ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_plan ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_stage_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_execution ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_span ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_link ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_link_source_span ENABLE ROW LEVEL SECURITY;
ALTER TABLE explanation_statement ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_decision ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_event ENABLE ROW LEVEL SECURITY;

ALTER TABLE workspace FORCE ROW LEVEL SECURITY;
ALTER TABLE membership FORCE ROW LEVEL SECURITY;
ALTER TABLE source_asset FORCE ROW LEVEL SECURITY;
ALTER TABLE parsed_document FORCE ROW LEVEL SECURITY;
ALTER TABLE parsed_node FORCE ROW LEVEL SECURITY;
ALTER TABLE reference_entry FORCE ROW LEVEL SECURITY;
ALTER TABLE citation_cluster FORCE ROW LEVEL SECURITY;
ALTER TABLE citation_anchor FORCE ROW LEVEL SECURITY;
ALTER TABLE reference_candidate FORCE ROW LEVEL SECURITY;
ALTER TABLE reference_resolution FORCE ROW LEVEL SECURITY;
ALTER TABLE citing_claim FORCE ROW LEVEL SECURITY;
ALTER TABLE source_chunk FORCE ROW LEVEL SECURITY;
ALTER TABLE query_plan FORCE ROW LEVEL SECURITY;
ALTER TABLE evidence_candidate FORCE ROW LEVEL SECURITY;
ALTER TABLE analysis_run FORCE ROW LEVEL SECURITY;
ALTER TABLE analysis_stage_run FORCE ROW LEVEL SECURITY;
ALTER TABLE model_execution FORCE ROW LEVEL SECURITY;
ALTER TABLE source_span FORCE ROW LEVEL SECURITY;
ALTER TABLE evidence_link FORCE ROW LEVEL SECURITY;
ALTER TABLE evidence_link_source_span FORCE ROW LEVEL SECURITY;
ALTER TABLE explanation_statement FORCE ROW LEVEL SECURITY;
ALTER TABLE feedback_event FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_decision FORCE ROW LEVEL SECURITY;
ALTER TABLE outbox_event FORCE ROW LEVEL SECURITY;

CREATE POLICY workspace_isolation ON workspace
    USING (id = current_workspace_id())
    WITH CHECK (id = current_workspace_id());

CREATE POLICY membership_isolation ON membership
    USING (workspace_id = current_workspace_id())
    WITH CHECK (workspace_id = current_workspace_id());

CREATE POLICY source_asset_isolation ON source_asset
    USING (workspace_id = current_workspace_id())
    WITH CHECK (workspace_id = current_workspace_id());

CREATE POLICY parsed_document_isolation ON parsed_document
    USING (EXISTS (
        SELECT 1 FROM source_asset sa
        WHERE sa.id = parsed_document.source_asset_id
          AND sa.workspace_id = current_workspace_id()
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM source_asset sa
        WHERE sa.id = parsed_document.source_asset_id
          AND sa.workspace_id = current_workspace_id()
    ));

CREATE POLICY parsed_node_isolation ON parsed_node
    USING (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = parsed_node.parsed_document_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = parsed_node.parsed_document_id
    ));

CREATE POLICY reference_entry_isolation ON reference_entry
    USING (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = reference_entry.parsed_document_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = reference_entry.parsed_document_id
    ));

CREATE POLICY citation_cluster_isolation ON citation_cluster
    USING (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = citation_cluster.parsed_document_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = citation_cluster.parsed_document_id
    ));

CREATE POLICY citation_anchor_isolation ON citation_anchor
    USING (EXISTS (
        SELECT 1 FROM citation_cluster cc
        WHERE cc.id = citation_anchor.citation_cluster_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM citation_cluster cc
        WHERE cc.id = citation_anchor.citation_cluster_id
    ));

CREATE POLICY reference_candidate_isolation ON reference_candidate
    USING (EXISTS (
        SELECT 1 FROM reference_entry re
        WHERE re.id = reference_candidate.reference_entry_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM reference_entry re
        WHERE re.id = reference_candidate.reference_entry_id
    ));

CREATE POLICY reference_resolution_isolation ON reference_resolution
    USING (EXISTS (
        SELECT 1 FROM reference_entry re
        WHERE re.id = reference_resolution.reference_entry_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM reference_entry re
        WHERE re.id = reference_resolution.reference_entry_id
    ));

CREATE POLICY citing_claim_isolation ON citing_claim
    USING (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = citing_claim.parsed_document_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = citing_claim.parsed_document_id
    ));

CREATE POLICY source_chunk_isolation ON source_chunk
    USING (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = source_chunk.parsed_document_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM parsed_document pd
        WHERE pd.id = source_chunk.parsed_document_id
    ));

CREATE POLICY query_plan_isolation ON query_plan
    USING (EXISTS (
        SELECT 1 FROM citing_claim cc
        WHERE cc.id = query_plan.citing_claim_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM citing_claim cc
        WHERE cc.id = query_plan.citing_claim_id
    ));

CREATE POLICY evidence_candidate_isolation ON evidence_candidate
    USING (EXISTS (
        SELECT 1 FROM citing_claim cc
        WHERE cc.id = evidence_candidate.citing_claim_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM citing_claim cc
        WHERE cc.id = evidence_candidate.citing_claim_id
    ));

CREATE POLICY analysis_run_isolation ON analysis_run
    USING (workspace_id = current_workspace_id())
    WITH CHECK (workspace_id = current_workspace_id());

CREATE POLICY analysis_stage_run_isolation ON analysis_stage_run
    USING (EXISTS (
        SELECT 1 FROM analysis_run ar
        WHERE ar.id = analysis_stage_run.analysis_run_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM analysis_run ar
        WHERE ar.id = analysis_stage_run.analysis_run_id
    ));

CREATE POLICY model_execution_isolation ON model_execution
    USING (
        analysis_stage_run_id IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM analysis_stage_run sr
            WHERE sr.id = model_execution.analysis_stage_run_id
        )
    )
    WITH CHECK (
        analysis_stage_run_id IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM analysis_stage_run sr
            WHERE sr.id = model_execution.analysis_stage_run_id
        )
    );

CREATE POLICY source_span_isolation ON source_span
    USING (EXISTS (
        SELECT 1 FROM source_asset sa
        WHERE sa.id = source_span.source_asset_id
          AND sa.workspace_id = current_workspace_id()
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM source_asset sa
        WHERE sa.id = source_span.source_asset_id
          AND sa.workspace_id = current_workspace_id()
    ));

CREATE POLICY evidence_link_isolation ON evidence_link
    USING (workspace_id = current_workspace_id())
    WITH CHECK (workspace_id = current_workspace_id());

CREATE POLICY evidence_link_source_span_isolation ON evidence_link_source_span
    USING (EXISTS (
        SELECT 1 FROM evidence_link el
        WHERE el.id = evidence_link_source_span.evidence_link_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM evidence_link el
        WHERE el.id = evidence_link_source_span.evidence_link_id
    ));

CREATE POLICY explanation_statement_isolation ON explanation_statement
    USING (EXISTS (
        SELECT 1 FROM evidence_link el
        WHERE el.id = explanation_statement.evidence_link_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM evidence_link el
        WHERE el.id = explanation_statement.evidence_link_id
    ));

CREATE POLICY feedback_event_isolation ON feedback_event
    USING (workspace_id = current_workspace_id())
    WITH CHECK (workspace_id = current_workspace_id());

CREATE POLICY audit_decision_isolation ON audit_decision
    USING (EXISTS (
        SELECT 1 FROM evidence_link el
        WHERE el.id = audit_decision.evidence_link_id
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM evidence_link el
        WHERE el.id = audit_decision.evidence_link_id
    ));

CREATE POLICY outbox_event_isolation ON outbox_event
    USING (workspace_id IS NULL OR workspace_id = current_workspace_id())
    WITH CHECK (workspace_id IS NULL OR workspace_id = current_workspace_id());

COMMENT ON TABLE evidence_link IS 'Primary inspectable claim-to-source judgment. Generated prose must not replace this record.';
COMMENT ON COLUMN source_span.quote_sha256 IS 'Hash of the exact normalized quote at creation; auditors revalidate against immutable source bytes.';
COMMENT ON COLUMN evidence_link.confidence_vector IS 'Stage-level confidence object; never expose one unexplained probability as certainty.';
COMMENT ON COLUMN analysis_run.limitations IS 'Structured, user-visible limitations; completed_with_limits is a successful domain outcome.';

COMMIT;
