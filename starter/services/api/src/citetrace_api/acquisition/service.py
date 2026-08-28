from uuid import UUID, uuid4

from pydantic import BaseModel

from citetrace_api.acquisition.fetcher import SafeRemoteFetcher
from citetrace_api.acquisition.policy import (
    AccessLevel,
    AcquisitionPolicyRequest,
    evaluate_acquisition_policy,
)
from citetrace_api.acquisition.url_guard import UrlGuard
from citetrace_api.db.repositories.source_assets import SourceAsset, SourceAssetRepository
from citetrace_api.providers.unpaywall import UnpaywallProvider


class AcquisitionOutcome(BaseModel):
    source_asset_id: UUID | None
    access_level: AccessLevel
    acquisition_method: str
    sha256: str | None
    byte_size: int | None
    limitations: list[str]


class ObjectStore:
    async def put(self, key: str, data: bytes, content_type: str) -> None:
        pass


class SourceAcquisitionService:
    def __init__(
        self,
        repository: SourceAssetRepository,
        unpaywall: UnpaywallProvider,
        url_guard: UrlGuard,
        fetcher: SafeRemoteFetcher,
        object_store: ObjectStore,
    ):
        self.repository = repository
        self.unpaywall = unpaywall
        self.url_guard = url_guard
        self.fetcher = fetcher
        self.object_store = object_store

    async def acquire(
        self,
        work_version_id: UUID,
        workspace_id: UUID,
        doi: str | None = None,
        title: str | None = None,
        abstract: str | None = None,
        trace_id: str = "",
    ) -> AcquisitionOutcome:
        # 1. Check if workspace already has a source asset
        existing = await self.repository.get_by_work_version(workspace_id, work_version_id)
        if existing:
            return AcquisitionOutcome(
                source_asset_id=existing.id,
                access_level=AccessLevel(existing.access_level),
                acquisition_method=existing.acquisition_method,
                sha256=existing.sha256,
                byte_size=existing.byte_size,
                limitations=[],
            )

        # 2. If DOI available, query Unpaywall
        oa_result = None
        if doi:
            import contextlib

            with contextlib.suppress(Exception):
                oa_result = await self.unpaywall.get_oa_locations(doi)

        meta: dict[str, object] = {"has_abstract": bool(abstract), "has_metadata": True}
        proposed_url = None
        proposed_method = "metadata"

        if oa_result and oa_result.is_oa and oa_result.best_oa_location:
            loc = oa_result.best_oa_location
            meta["is_oa"] = True
            meta["host_type"] = loc.host_type
            proposed_url = loc.url_for_pdf or loc.url
            proposed_method = "unpaywall_oa"

        # 3. Evaluate policy
        req = AcquisitionPolicyRequest(
            workspace_id=workspace_id,
            work_version_id=work_version_id,
            proposed_method=proposed_method,
            proposed_url=proposed_url,
            provider_access_metadata=meta,
        )
        decision = evaluate_acquisition_policy(req)

        if not decision.allowed:
            return AcquisitionOutcome(
                source_asset_id=None,
                access_level=decision.access_level,
                acquisition_method="rejected",
                sha256=None,
                byte_size=None,
                limitations=["Policy denied acquisition"],
            )

        # 4. Fetch PDF if open access
        if (
            decision.access_level
            in (
                AccessLevel.open_access_full_text,
                AccessLevel.publisher_open_full_text,
                AccessLevel.repository_manuscript,
            )
            and proposed_url
        ):
            try:
                val_loc = await self.url_guard.validate(proposed_url)
                asset = await self.fetcher.fetch(val_loc, trace_id=trace_id)

                asset_id = uuid4()
                object_key = f"{workspace_id}/{work_version_id}/{asset_id}.pdf"
                await self.object_store.put(object_key, asset.data, asset.media_type)

                new_asset = SourceAsset(
                    id=asset_id,
                    workspace_id=workspace_id,
                    work_version_id=work_version_id,
                    access_level=decision.access_level.value,
                    acquisition_method=proposed_method,
                    sha256=asset.sha256,
                    byte_size=asset.byte_size,
                    object_key=object_key,
                )
                await self.repository.create(new_asset)

                return AcquisitionOutcome(
                    source_asset_id=asset_id,
                    access_level=decision.access_level,
                    acquisition_method=proposed_method,
                    sha256=asset.sha256,
                    byte_size=asset.byte_size,
                    limitations=[],
                )
            except Exception:
                # Fallback to abstract
                decision.access_level = (
                    AccessLevel.abstract_only if abstract else AccessLevel.metadata_only
                )

        # 5/6. Fallbacks
        if decision.access_level == AccessLevel.abstract_only and abstract:
            asset_id = uuid4()
            object_key = f"{workspace_id}/{work_version_id}/{asset_id}.txt"
            abstract_bytes = abstract.encode("utf-8")
            await self.object_store.put(object_key, abstract_bytes, "text/plain")

            import hashlib

            sha256 = hashlib.sha256(abstract_bytes).hexdigest()
            byte_size = len(abstract_bytes)

            new_asset = SourceAsset(
                id=asset_id,
                workspace_id=workspace_id,
                work_version_id=work_version_id,
                access_level=decision.access_level.value,
                acquisition_method="abstract_fallback",
                sha256=sha256,
                byte_size=byte_size,
                object_key=object_key,
            )
            await self.repository.create(new_asset)

            return AcquisitionOutcome(
                source_asset_id=asset_id,
                access_level=decision.access_level,
                acquisition_method="abstract_fallback",
                sha256=sha256,
                byte_size=byte_size,
                limitations=["Full text unavailable"],
            )

        return AcquisitionOutcome(
            source_asset_id=None,
            access_level=AccessLevel.metadata_only,
            acquisition_method="metadata_fallback",
            sha256=None,
            byte_size=None,
            limitations=["Full text and abstract unavailable"],
        )
