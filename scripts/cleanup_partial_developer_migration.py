"""Remove only empty tables left by the failed non-transactional developer migration."""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models import engine


TABLES = [
    "api_usage_log",
    "developer_subscription",
    "api_plan",
    "developer_api_key",
    "developer_account",
]


async def main():
    async with engine.begin() as connection:
        existing = set(
            (await connection.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name IN "
                "('api_usage_log','developer_subscription','api_plan','developer_api_key','developer_account')"
            ))).scalars()
        )
        for table in TABLES:
            if table not in existing:
                continue
            count = (await connection.execute(text(f"SELECT COUNT(*) FROM `{table}`"))).scalar_one()
            if count:
                raise RuntimeError(f"Refusing to drop non-empty partial table: {table}")
            await connection.execute(text(f"DROP TABLE `{table}`"))
        print({"removed_empty_partial_tables": [x for x in TABLES if x in existing]})
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
