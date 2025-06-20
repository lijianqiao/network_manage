from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device_groups" DROP CONSTRAINT IF EXISTS "fk_device_g_regions_1978882f";
        ALTER TABLE "device_groups" DROP COLUMN "region_id";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device_groups" ADD "region_id" UUID;
        ALTER TABLE "device_groups" ADD CONSTRAINT "fk_device_g_regions_1978882f" FOREIGN KEY ("region_id") REFERENCES "regions" ("id") ON DELETE CASCADE;"""
