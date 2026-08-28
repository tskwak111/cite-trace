# Dependency locking before implementation merge

The scaffold pins direct runtime versions but intentionally does not include fabricated lockfiles. The package-generation environment could not resolve external registries, so a trustworthy transitive lock could not be produced here.

Before the first implementation pull request is merged:

## Python

1. Use Python 3.13.x.
2. Generate `uv.lock` from `starter/services/api/pyproject.toml` in a network-enabled, trusted environment.
3. Review resolved sources and hashes.
4. Change CI to `uv sync --frozen --all-extras` and run tools through `uv run`.
5. Keep direct runtime dependencies exact or tightly bounded; update through reviewed dependency PRs.

Example bootstrap:

```bash
cd starter/services/api
uv lock
uv sync --all-extras
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Web

1. Use Node.js 24 LTS and the package-manager version declared in `package.json`.
2. Run `pnpm install` once in a trusted environment and commit `pnpm-lock.yaml`.
3. Replace `--no-frozen-lockfile` in CI and Docker with `--frozen-lockfile`.
4. Review install scripts and prefer `pnpm approve-builds`/policy controls for packages requiring lifecycle scripts.

## Containers

- Resolve every image tag to an approved digest in release manifests.
- Scan images and generate an SBOM.
- Record image source, license, architecture and end-of-support policy.
- Do not auto-promote a new database, Redis, parser or base-image major version.

## Release gate

A deployable build requires committed Python and pnpm locks, reproducible CI installs, image digests, SBOMs and vulnerability review. The current `--no-frozen-lockfile` commands are scaffold bootstrap behavior only and must not remain in a production branch.
