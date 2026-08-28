# Database contract

`schema.sql` is the canonical v1 PostgreSQL contract. The production migration tool may split it into smaller forward-only migrations, but table names, enum values, constraints and tenant semantics must remain equivalent.

## Required extensions

- `pgcrypto`
- `vector`
- `citext`
- `pg_trgm`

Before applying the schema, the database image must provide pgvector and the operator must create a migration role with extension privileges. Application roles must not own extensions or bypass row-level security.

## Transaction tenant context

Every authenticated request opens a transaction and executes:

```sql
SET LOCAL app.workspace_id = '<authorized-workspace-uuid>';
```

A connection must never be returned to the pool with session-level tenant state. Use `SET LOCAL`, not `SET`.

## Migration discipline

1. Forward-only migration in production.
2. Expand before contract for externally used columns.
3. Backfill with bounded batches and resumable checkpoints.
4. Validate new constraints before making them blocking when tables are large.
5. Record the deployed contract hash in `schema_registry`.
6. Test RLS with two tenants and a role that cannot bypass RLS.
