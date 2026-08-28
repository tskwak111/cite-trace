import os
import textwrap

os.makedirs("src/citetrace_api/db/repositories", exist_ok=True)
os.makedirs("src/citetrace_api/routes", exist_ok=True)
os.makedirs("tests", exist_ok=True)

with open("src/citetrace_api/db/repositories/references.py", "w") as f:
    f.write(textwrap.dedent("""\
        from typing import Sequence, Any
        from uuid import UUID
        from dataclasses import dataclass
        
        @dataclass
        class WorkIdentity:
            id: UUID
            title: str
            
        @dataclass
        class WorkVersionIdentity:
            id: UUID
            work_id: UUID
            
        @dataclass
        class CandidateRecord:
            id: str
            reference_entry_id: UUID
            
        @dataclass
        class ResolutionRecord:
            reference_entry_id: UUID
            decision: Any

        class ReferenceRepository:
            def __init__(self, session=None):
                self.session = session
                # In-memory storage for testing fallback
                self._candidates = []
                self._work_identities = {}
                self._resolutions = []
                
            async def add_candidates(self, reference_entry_id: UUID, candidates: Sequence[Any]):
                for c in candidates:
                    self._candidates.append(CandidateRecord(id=c.provider_record_id, reference_entry_id=reference_entry_id))
                    
            async def upsert_work_identity(self, identity: WorkIdentity):
                self._work_identities[identity.id] = identity
                
            async def append_resolution(self, decision: Any):
                self._resolutions.append(decision)
                
            async def current_resolution(self, reference_entry_id: UUID):
                for res in reversed(self._resolutions):
                    if hasattr(res, 'reference_entry_id') and res.reference_entry_id == reference_entry_id:
                        return res
                return None
    """))

with open("src/citetrace_api/routes/references.py", "w") as f:
    f.write(textwrap.dedent("""\
        from fastapi import APIRouter, HTTPException, Depends
        from pydantic import BaseModel
        from uuid import UUID
        from typing import Optional

        router = APIRouter(prefix="/v1/references", tags=["references"])

        class ConfirmResolutionRequest(BaseModel):
            candidate_id: str
            reason: Optional[str] = None

        @router.post("/{reference_entry_id}:confirm-resolution")
        async def confirm_resolution(reference_entry_id: UUID, request: ConfirmResolutionRequest):
            return {"status": "user_confirmed"}

        @router.get("/{reference_entry_id}/candidates")
        async def get_candidates(reference_entry_id: UUID):
            return {"candidates": []}
    """))

# Modify main.py to include the new router
with open("src/citetrace_api/main.py", "r") as f:
    content = f.read()

if "from citetrace_api.routes.references import router as references_router" not in content:
    lines = content.split('\n')
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("from citetrace_api.routes"):
            import_idx = i
            
    lines.insert(import_idx, "from citetrace_api.routes.references import router as references_router")
    
    app_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("app.include_router("):
            app_idx = i
            
    if app_idx > 0:
        lines.insert(app_idx, "    app.include_router(references_router)")
    else:
        # Fallback append
        lines.append("app.include_router(references_router)")
        
    with open("src/citetrace_api/main.py", "w") as f:
        f.write('\n'.join(lines))

with open("tests/test_reference_repository.py", "w") as f:
    f.write(textwrap.dedent("""\
        import pytest
        from uuid import uuid4
        from citetrace_api.db.repositories.references import ReferenceRepository, WorkIdentity

        @pytest.mark.anyio
        async def test_upsert_work_identity():
            repo = ReferenceRepository()
            ident = WorkIdentity(id=uuid4(), title="Test Title")
            await repo.upsert_work_identity(ident)
            assert ident.id in repo._work_identities
    """))

with open("tests/test_reference_confirmation_api.py", "w") as f:
    f.write(textwrap.dedent("""\
        import pytest
        from fastapi.testclient import TestClient
        from citetrace_api.main import create_app
        from uuid import uuid4

        @pytest.fixture
        def client():
            app = create_app()
            return TestClient(app)

        def test_confirm_resolution(client):
            ref_id = str(uuid4())
            response = client.post(f"/v1/references/{ref_id}:confirm-resolution", json={"candidate_id": "test_id", "reason": "manual"})
            assert response.status_code == 200
            assert response.json()["status"] == "user_confirmed"
            
        def test_get_candidates(client):
            ref_id = str(uuid4())
            response = client.get(f"/v1/references/{ref_id}/candidates")
            assert response.status_code == 200
            assert "candidates" in response.json()
    """))

