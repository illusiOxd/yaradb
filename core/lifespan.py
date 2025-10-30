from contextlib import asynccontextmanager
from fastapi import FastAPI
from core import wal


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- YaraDB: Starting up... ---")

    wal.load_snapshot()

    wal.recover_from_wal()

    print("--- YaraDB: Startup complete. Service is running. ---")

    yield

    wal.perform_checkpoint()