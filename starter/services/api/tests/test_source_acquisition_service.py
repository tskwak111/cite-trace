from uuid import uuid4

import pytest

from citetrace_api.acquisition.fetcher import FetchedRemoteAsset
from citetrace_api.acquisition.policy import AccessLevel
from citetrace_api.acquisition.service import SourceAcquisitionService
from citetrace_api.acquisition.url_guard import ValidatedRemoteLocation
from citetrace_api.db.repositories.source_assets import SourceAsset, SourceAssetRepository


class MockUnpaywall:
    def __init__(self, result=None):
        self.result = result

    async def get_oa_locations(self, doi: str):
        if self.result is None:
            raise Exception("Not found")
        return self.result


class MockUrlGuard:
    async def validate(self, url: str):
        return ValidatedRemoteLocation(url, "example.com", ("1.1.1.1",), 443, "https")


class MockFetcher:
    async def fetch(self, loc, **kwargs):
        return FetchedRemoteAsset(b"%PDF", "hash", "application/pdf", 4, loc.url, {}, 200)


class MockObjectStore:
    async def put(self, key, data, ct):
        pass


@pytest.mark.anyio
async def test_acquire_existing_asset():
    repo = SourceAssetRepository()
    ws_id = uuid4()
    wv_id = uuid4()
    await repo.create(SourceAsset(uuid4(), ws_id, wv_id, "open_access_full_text", "unpaywall"))

    svc = SourceAcquisitionService(
        repo, MockUnpaywall(), MockUrlGuard(), MockFetcher(), MockObjectStore()
    )
    outcome = await svc.acquire(wv_id, ws_id)

    assert outcome.source_asset_id is not None
    assert outcome.access_level == AccessLevel.open_access_full_text


@pytest.mark.anyio
async def test_acquire_abstract_fallback():
    repo = SourceAssetRepository()
    ws_id = uuid4()
    wv_id = uuid4()

    svc = SourceAcquisitionService(
        repo, MockUnpaywall(), MockUrlGuard(), MockFetcher(), MockObjectStore()
    )
    outcome = await svc.acquire(wv_id, ws_id, abstract="Test abstract")

    assert outcome.source_asset_id is not None
    assert outcome.access_level == AccessLevel.abstract_only
    assert outcome.acquisition_method == "abstract_fallback"
