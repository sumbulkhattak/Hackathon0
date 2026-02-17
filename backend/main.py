import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from database import engine, get_db, Base
from models import Product
from routes.products import router as products_router
from routes.orders import router as orders_router
from routes.hooks import router as hooks_router
from routes.triggers import router as triggers_router
from routes.tasks import router as tasks_router
from routes.dashboard import router as dashboard_router
from routes.memory import router as memory_router
from routes.audit import router as audit_router
from routes.ecommerce import router as ecommerce_router
from seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate vault path
    if not config.VAULT_PATH.exists():
        logger.error(f"Vault path not found: {config.VAULT_PATH}")
        raise RuntimeError(f"Vault path not found: {config.VAULT_PATH}")
    logger.info(f"Vault found at {config.VAULT_PATH}")

    # Ensure all vault directories exist
    config.ensure_vault_dirs()

    # Initialize database
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        count = db.query(Product).count()
        if count == 0:
            seed_database(db)
            logger.info("Database seeded successfully.")
        else:
            logger.info(f"Database already has {count} products. Skipping seed.")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Royal Sparkle API",
    description="Backend API for Royal Sparkle Jewellery E-Commerce + AI Employee",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(hooks_router)
app.include_router(triggers_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)
app.include_router(memory_router)
app.include_router(audit_router)
app.include_router(ecommerce_router)
