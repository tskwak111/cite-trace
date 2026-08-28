import asyncio
import logging

from citetrace_api.config import get_settings
from citetrace_api.db.repositories.outbox import OutboxRepository
from citetrace_api.db.repositories.parsed_documents import ParsedDocumentsRepository
from citetrace_api.db.session import Database
from citetrace_api.documents.storage import S3ObjectStore
from citetrace_api.orchestration.handlers import DocumentSourceRegisteredHandler
from citetrace_api.parsing.grobid_client import GrobidClient
from citetrace_api.parsing.service import ParsingService

logger = logging.getLogger(__name__)


class ObjectStoreAdapter:
    def __init__(self, store: S3ObjectStore):
        self.store = store

    async def put(self, key: str, data: bytes) -> None:
        await self.store.put_if_absent(key, data, "application/octet-stream")

    async def get(self, key: str) -> bytes:
        return await self.store.read(key)

    async def exists(self, key: str) -> bool:
        try:
            await self.store.read(key)
            return True
        except KeyError:
            return False
        except Exception:
            return False


class OutboxWorker:
    def __init__(self, db: Database, worker_id: str = "worker-1") -> None:
        self.db = db
        self.worker_id = worker_id
        self.settings = get_settings()
        self.object_store = S3ObjectStore(
            endpoint_url=self.settings.s3_endpoint_url,
            bucket=self.settings.s3_bucket,
            access_key=self.settings.s3_access_key,
            secret_key=self.settings.s3_secret_key,
        )
        self.grobid_client = GrobidClient()
        self.parsing_service = ParsingService(
            grobid_client=self.grobid_client, object_store=ObjectStoreAdapter(self.object_store)
        )

    async def run_once(self, limit: int = 20) -> int:
        async with self.db.sessions() as session:
            outbox_repo = OutboxRepository(session)
            try:
                records = await outbox_repo.claim_batch(self.worker_id, limit)
            except Exception:
                await session.rollback()
                return 0
                
            if not records:
                return 0

            parsed_docs_repo = ParsedDocumentsRepository(session)
            
            handlers = {
                ("document.source.registered", "1.0"): DocumentSourceRegisteredHandler(
                    object_store=self.object_store,
                    parsing_service=self.parsing_service,
                    parsed_docs_repo=parsed_docs_repo,
                    outbox_repo=outbox_repo,
                )
            }

            processed_count = 0
            for record in records:
                handler = handlers.get((record.event_type, record.schema_version))
                if not handler:
                    await outbox_repo.mark_published(record.id)
                    continue

                try:
                    event = {"payload": record.payload}
                    await handler(event)
                    await outbox_repo.mark_published(record.id)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process event {record.id}: {e}")

            await session.commit()
            return processed_count


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    db = Database(url=settings.database_url, pool_size=5, pool_timeout=30.0)
    worker = OutboxWorker(db=db)

    logger.info("Starting outbox worker")
    try:
        while True:
            processed = await worker.run_once(limit=20)
            if processed == 0:
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Worker cancelled")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
