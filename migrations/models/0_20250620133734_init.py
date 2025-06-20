from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "brands" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "platform_type" VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON COLUMN "brands"."id" IS '主键';
COMMENT ON COLUMN "brands"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "brands"."description" IS '描述信息';
COMMENT ON COLUMN "brands"."created_at" IS '创建时间';
COMMENT ON COLUMN "brands"."updated_at" IS '更新时间';
COMMENT ON COLUMN "brands"."name" IS '品牌唯一名称';
COMMENT ON COLUMN "brands"."platform_type" IS '平台驱动类型';
COMMENT ON TABLE "brands" IS '网络设备品牌表';
CREATE TABLE IF NOT EXISTS "config_templates" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "template_type" VARCHAR(6) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "config_templates"."id" IS '主键';
COMMENT ON COLUMN "config_templates"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "config_templates"."description" IS '描述信息';
COMMENT ON COLUMN "config_templates"."created_at" IS '创建时间';
COMMENT ON COLUMN "config_templates"."updated_at" IS '更新时间';
COMMENT ON COLUMN "config_templates"."name" IS '模板唯一名称';
COMMENT ON COLUMN "config_templates"."template_type" IS '模板类型';
COMMENT ON COLUMN "config_templates"."is_active" IS '是否启用';
COMMENT ON TABLE "config_templates" IS '配置模板表';
CREATE TABLE IF NOT EXISTS "device_models" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "brand_id" UUID NOT NULL REFERENCES "brands" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "device_models"."id" IS '主键';
COMMENT ON COLUMN "device_models"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "device_models"."description" IS '描述信息';
COMMENT ON COLUMN "device_models"."created_at" IS '创建时间';
COMMENT ON COLUMN "device_models"."updated_at" IS '更新时间';
COMMENT ON COLUMN "device_models"."name" IS '设备型号唯一名称';
COMMENT ON COLUMN "device_models"."brand_id" IS '关联品牌';
COMMENT ON TABLE "device_models" IS '网络设备型号表';
CREATE TABLE IF NOT EXISTS "regions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "snmp_community_string" VARCHAR(100) NOT NULL,
    "default_cli_username" VARCHAR(50) NOT NULL
);
COMMENT ON COLUMN "regions"."id" IS '主键';
COMMENT ON COLUMN "regions"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "regions"."description" IS '描述信息';
COMMENT ON COLUMN "regions"."created_at" IS '创建时间';
COMMENT ON COLUMN "regions"."updated_at" IS '更新时间';
COMMENT ON COLUMN "regions"."name" IS '区域唯一名称';
COMMENT ON COLUMN "regions"."snmp_community_string" IS 'SNMP社区字符串';
COMMENT ON COLUMN "regions"."default_cli_username" IS '默认CLI账号名';
COMMENT ON TABLE "regions" IS '网络设备区域管理表';
CREATE TABLE IF NOT EXISTS "device_groups" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "region_id" UUID REFERENCES "regions" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "device_groups"."id" IS '主键';
COMMENT ON COLUMN "device_groups"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "device_groups"."description" IS '描述信息';
COMMENT ON COLUMN "device_groups"."created_at" IS '创建时间';
COMMENT ON COLUMN "device_groups"."updated_at" IS '更新时间';
COMMENT ON COLUMN "device_groups"."name" IS '分组唯一名称';
COMMENT ON COLUMN "device_groups"."region_id" IS '关联区域';
COMMENT ON TABLE "device_groups" IS '设备分组表';
CREATE TABLE IF NOT EXISTS "devices" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "ip_address" VARCHAR(45) NOT NULL UNIQUE,
    "device_type" VARCHAR(6) NOT NULL,
    "serial_number" VARCHAR(100),
    "is_dynamic_password" BOOL NOT NULL DEFAULT True,
    "cli_username" VARCHAR(50),
    "cli_password_encrypted" TEXT,
    "enable_password_encrypted" TEXT,
    "status" VARCHAR(7) NOT NULL DEFAULT 'unknown',
    "extra_info" JSONB,
    "device_group_id" UUID NOT NULL REFERENCES "device_groups" ("id") ON DELETE CASCADE,
    "model_id" UUID NOT NULL REFERENCES "device_models" ("id") ON DELETE CASCADE,
    "region_id" UUID NOT NULL REFERENCES "regions" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_devices_ip_addr_97a627" ON "devices" ("ip_address", "region_id", "status");
COMMENT ON COLUMN "devices"."id" IS '主键';
COMMENT ON COLUMN "devices"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "devices"."description" IS '描述信息';
COMMENT ON COLUMN "devices"."created_at" IS '创建时间';
COMMENT ON COLUMN "devices"."updated_at" IS '更新时间';
COMMENT ON COLUMN "devices"."name" IS '设备唯一主机名';
COMMENT ON COLUMN "devices"."ip_address" IS '设备管理IP地址';
COMMENT ON COLUMN "devices"."device_type" IS '设备类型';
COMMENT ON COLUMN "devices"."serial_number" IS '设备序列号';
COMMENT ON COLUMN "devices"."is_dynamic_password" IS '是否使用动态密码';
COMMENT ON COLUMN "devices"."cli_username" IS '固定CLI账号';
COMMENT ON COLUMN "devices"."cli_password_encrypted" IS '加密存储的固定密码';
COMMENT ON COLUMN "devices"."enable_password_encrypted" IS '加密存储的enable密码';
COMMENT ON COLUMN "devices"."status" IS '设备在线状态';
COMMENT ON COLUMN "devices"."extra_info" IS '扩展信息';
COMMENT ON COLUMN "devices"."device_group_id" IS '设备所属分组';
COMMENT ON COLUMN "devices"."model_id" IS '设备型号';
COMMENT ON COLUMN "devices"."region_id" IS '设备所属区域';
COMMENT ON TABLE "devices" IS '网络设备信息表';
CREATE TABLE IF NOT EXISTS "device_connection_status" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_reachable" BOOL NOT NULL DEFAULT False,
    "last_check_time" TIMESTAMPTZ NOT NULL,
    "last_success_time" TIMESTAMPTZ,
    "failure_count" INT NOT NULL DEFAULT 0,
    "failure_reason" TEXT,
    "snmp_response_time_ms" INT,
    "device_id" UUID NOT NULL UNIQUE REFERENCES "devices" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_device_conn_device__b9bf8b" ON "device_connection_status" ("device_id", "last_check_time");
COMMENT ON COLUMN "device_connection_status"."id" IS '主键';
COMMENT ON COLUMN "device_connection_status"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "device_connection_status"."description" IS '描述信息';
COMMENT ON COLUMN "device_connection_status"."created_at" IS '创建时间';
COMMENT ON COLUMN "device_connection_status"."updated_at" IS '更新时间';
COMMENT ON COLUMN "device_connection_status"."is_reachable" IS '设备是否可达';
COMMENT ON COLUMN "device_connection_status"."last_check_time" IS '最近检查时间';
COMMENT ON COLUMN "device_connection_status"."last_success_time" IS '最近成功连接时间';
COMMENT ON COLUMN "device_connection_status"."failure_count" IS '连续失败次数';
COMMENT ON COLUMN "device_connection_status"."failure_reason" IS '失败原因';
COMMENT ON COLUMN "device_connection_status"."snmp_response_time_ms" IS 'SNMP响应时间';
COMMENT ON COLUMN "device_connection_status"."device_id" IS '关联设备';
COMMENT ON TABLE "device_connection_status" IS '设备连接状态表';
CREATE TABLE IF NOT EXISTS "operation_logs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "command_executed" TEXT,
    "output_received" TEXT,
    "parsed_output" JSONB,
    "status" VARCHAR(7) NOT NULL,
    "error_message" TEXT,
    "executed_by" VARCHAR(100),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "device_id" UUID REFERENCES "devices" ("id") ON DELETE CASCADE,
    "template_id" UUID REFERENCES "config_templates" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_operation_l_device__3a17a3" ON "operation_logs" ("device_id", "timestamp");
COMMENT ON COLUMN "operation_logs"."id" IS '主键';
COMMENT ON COLUMN "operation_logs"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "operation_logs"."description" IS '描述信息';
COMMENT ON COLUMN "operation_logs"."created_at" IS '创建时间';
COMMENT ON COLUMN "operation_logs"."updated_at" IS '更新时间';
COMMENT ON COLUMN "operation_logs"."command_executed" IS '实际执行的命令';
COMMENT ON COLUMN "operation_logs"."output_received" IS '设备返回的原始输出';
COMMENT ON COLUMN "operation_logs"."parsed_output" IS '结构化解析结果';
COMMENT ON COLUMN "operation_logs"."status" IS '操作执行状态';
COMMENT ON COLUMN "operation_logs"."error_message" IS '错误信息';
COMMENT ON COLUMN "operation_logs"."executed_by" IS '操作者身份';
COMMENT ON COLUMN "operation_logs"."timestamp" IS '操作时间';
COMMENT ON COLUMN "operation_logs"."device_id" IS '操作的设备';
COMMENT ON COLUMN "operation_logs"."template_id" IS '使用的模板';
COMMENT ON TABLE "operation_logs" IS '操作日志表';
CREATE TABLE IF NOT EXISTS "config_snapshots" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "snapshot_type" VARCHAR(11) NOT NULL,
    "config_content" TEXT NOT NULL,
    "checksum" VARCHAR(32) NOT NULL,
    "device_id" UUID NOT NULL REFERENCES "devices" ("id") ON DELETE CASCADE,
    "operation_log_id" UUID REFERENCES "operation_logs" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_config_snap_device__86b690" ON "config_snapshots" ("device_id", "created_at");
COMMENT ON COLUMN "config_snapshots"."id" IS '主键';
COMMENT ON COLUMN "config_snapshots"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "config_snapshots"."description" IS '描述信息';
COMMENT ON COLUMN "config_snapshots"."created_at" IS '创建时间';
COMMENT ON COLUMN "config_snapshots"."updated_at" IS '更新时间';
COMMENT ON COLUMN "config_snapshots"."snapshot_type" IS '快照类型';
COMMENT ON COLUMN "config_snapshots"."config_content" IS '完整配置内容';
COMMENT ON COLUMN "config_snapshots"."checksum" IS '配置MD5校验码';
COMMENT ON COLUMN "config_snapshots"."device_id" IS '关联设备';
COMMENT ON COLUMN "config_snapshots"."operation_log_id" IS '关联操作记录';
COMMENT ON TABLE "config_snapshots" IS '配置快照表';
CREATE TABLE IF NOT EXISTS "config_diffs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "diff_content" TEXT NOT NULL,
    "added_lines" INT NOT NULL,
    "removed_lines" INT NOT NULL,
    "after_snapshot_id" UUID NOT NULL REFERENCES "config_snapshots" ("id") ON DELETE CASCADE,
    "before_snapshot_id" UUID NOT NULL REFERENCES "config_snapshots" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "config_diffs"."id" IS '主键';
COMMENT ON COLUMN "config_diffs"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "config_diffs"."description" IS '描述信息';
COMMENT ON COLUMN "config_diffs"."created_at" IS '创建时间';
COMMENT ON COLUMN "config_diffs"."updated_at" IS '更新时间';
COMMENT ON COLUMN "config_diffs"."diff_content" IS '差异内容';
COMMENT ON COLUMN "config_diffs"."added_lines" IS '新增行数';
COMMENT ON COLUMN "config_diffs"."removed_lines" IS '删除行数';
COMMENT ON COLUMN "config_diffs"."after_snapshot_id" IS '变更后快照';
COMMENT ON COLUMN "config_diffs"."before_snapshot_id" IS '变更前快照';
COMMENT ON TABLE "config_diffs" IS '配置差异表';
CREATE TABLE IF NOT EXISTS "rollback_operations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "rollback_status" VARCHAR(7) NOT NULL,
    "executed_by" VARCHAR(100) NOT NULL,
    "executed_at" TIMESTAMPTZ NOT NULL,
    "original_operation_id" UUID NOT NULL REFERENCES "operation_logs" ("id") ON DELETE CASCADE,
    "target_snapshot_id" UUID NOT NULL REFERENCES "config_snapshots" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "rollback_operations"."id" IS '主键';
COMMENT ON COLUMN "rollback_operations"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "rollback_operations"."description" IS '描述信息';
COMMENT ON COLUMN "rollback_operations"."created_at" IS '创建时间';
COMMENT ON COLUMN "rollback_operations"."updated_at" IS '更新时间';
COMMENT ON COLUMN "rollback_operations"."rollback_status" IS '回滚状态';
COMMENT ON COLUMN "rollback_operations"."executed_by" IS '执行回滚的操作者';
COMMENT ON COLUMN "rollback_operations"."executed_at" IS '回滚执行时间';
COMMENT ON COLUMN "rollback_operations"."original_operation_id" IS '原始操作记录';
COMMENT ON COLUMN "rollback_operations"."target_snapshot_id" IS '目标回滚快照';
COMMENT ON TABLE "rollback_operations" IS '回滚操作表';
CREATE TABLE IF NOT EXISTS "template_commands" (
    "id" UUID NOT NULL PRIMARY KEY,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "jinja_content" TEXT NOT NULL,
    "ttp_template" TEXT,
    "expected_params" JSONB,
    "brand_id" UUID NOT NULL REFERENCES "brands" ("id") ON DELETE CASCADE,
    "config_template_id" UUID NOT NULL REFERENCES "config_templates" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_template_co_config__c7e7d1" UNIQUE ("config_template_id", "brand_id")
);
COMMENT ON COLUMN "template_commands"."id" IS '主键';
COMMENT ON COLUMN "template_commands"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "template_commands"."description" IS '描述信息';
COMMENT ON COLUMN "template_commands"."created_at" IS '创建时间';
COMMENT ON COLUMN "template_commands"."updated_at" IS '更新时间';
COMMENT ON COLUMN "template_commands"."jinja_content" IS 'Jinja2模板内容';
COMMENT ON COLUMN "template_commands"."ttp_template" IS 'TTP解析模板';
COMMENT ON COLUMN "template_commands"."expected_params" IS '期望的参数列表';
COMMENT ON COLUMN "template_commands"."brand_id" IS '关联品牌';
COMMENT ON COLUMN "template_commands"."config_template_id" IS '关联配置模板';
COMMENT ON TABLE "template_commands" IS '模板命令表';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
