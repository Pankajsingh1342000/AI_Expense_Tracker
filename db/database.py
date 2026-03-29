from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.config import DATABASE_URL

is_sqlite = DATABASE_URL.startswith("sqlite")
uses_supabase_pooler = "pooler.supabase.com" in DATABASE_URL

engine_kwargs = {}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    )

    # Supabase transaction pooler is already a connection pool. Re-pooling
    # inside SQLAlchemy can lead to stale TLS sessions and intermittent SSL
    # errors on hosted platforms like Render.
    if uses_supabase_pooler:
        engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
