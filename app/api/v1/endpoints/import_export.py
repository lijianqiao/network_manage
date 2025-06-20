"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: import_export.py
@DateTime: 2025/06/20 14:00:00
@Docs: 导入导出API端点
"""

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST

from app.core.dependencies import get_import_export_service
from app.schemas.import_export import ImportResultResponse, SupportedModelsResponse
from app.services.import_export_service import ImportExportService
from app.utils.logger import logger

router = APIRouter(prefix="/import-export", tags=["导入导出"])


@router.get("/models", response_model=SupportedModelsResponse, summary="获取支持的模型列表")
async def get_supported_models(service: ImportExportService = Depends(get_import_export_service)):
    """获取支持的模型列表及字段信息"""
    try:
        models_info = {}
        for model_name, mapping in service.FIELD_MAPPINGS.items():
            models_info[model_name] = {
                "display_fields": mapping["display_fields"],
                "required_fields": mapping["required_fields"],
                "foreign_keys": list(mapping["foreign_keys"].keys()),
                "model_class": service.SUPPORTED_MODELS[model_name].__name__,
            }

        return SupportedModelsResponse(models=models_info)
    except Exception as e:
        logger.error(f"获取支持模型列表失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"获取支持模型列表失败: {str(e)}") from e


@router.get("/template/{model_name}", summary="下载导入模板")
async def download_template(model_name: str, service: ImportExportService = Depends(get_import_export_service)):
    """下载指定模型的导入模板"""
    try:
        # 生成模板文件
        excel_data = await service.export_template(model_name)
        filename = service.get_filename(model_name, "template")

        # 返回文件流
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"下载模板失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"下载模板失败: {str(e)}") from e


@router.get("/export/{model_name}", summary="导出数据")
async def export_data(model_name: str, service: ImportExportService = Depends(get_import_export_service)):
    """导出指定模型的数据"""
    try:
        # 导出数据
        excel_data = await service.export_data(model_name)
        filename = service.get_filename(model_name, "data")

        # 返回文件流
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"导出数据失败: {str(e)}") from e


@router.post("/import/{model_name}", response_model=ImportResultResponse, summary="导入数据")
async def import_data(
    model_name: str,
    file: UploadFile = File(..., description="Excel文件"),
    create_missing_fk: bool = Form(default=True, description="是否自动创建缺失的外键记录"),
    service: ImportExportService = Depends(get_import_export_service),
):
    """导入数据到指定模型

    Args:
        model_name: 模型名称（如：region, brand, device_model等）
        file: 上传的Excel文件
        create_missing_fk: 是否自动创建缺失的外键记录

    Returns:
        导入结果统计
    """
    try:
        # 执行导入
        result = await service.import_data(model_name, file, create_missing_fk)

        return ImportResultResponse(**result)
    except Exception as e:
        logger.error(f"导入数据失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"导入数据失败: {str(e)}") from e


@router.get("/example/{model_name}", summary="获取示例数据说明")
async def get_example_data(model_name: str, service: ImportExportService = Depends(get_import_export_service)):
    """获取指定模型的示例数据说明"""
    try:
        if model_name not in service.SUPPORTED_MODELS:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"不支持的模型: {model_name}")

        mapping = service.FIELD_MAPPINGS[model_name]

        # 构建示例数据
        example_data = {}
        for field in mapping["display_fields"]:
            if field in mapping["foreign_keys"]:
                example_data[field] = f"关联{mapping['foreign_keys'][field].__name__}的名称"
            elif field == "name":
                example_data[field] = f"示例{model_name}名称"
            elif field == "description":
                example_data[field] = f"示例{model_name}描述"
            elif field == "ip_address":
                example_data[field] = "192.168.1.1"
            elif field == "device_type":
                example_data[field] = "switch 或 router"
            elif field == "status":
                example_data[field] = "online, offline, unknown"
            elif field == "is_dynamic_password":
                example_data[field] = "true 或 false"
            elif field in ["snmp_community_string", "default_cli_username", "cli_username"]:
                example_data[field] = "示例字符串"
            elif field == "platform_type":
                example_data[field] = "设备平台类型（如：huawei_vrp, cisco_ios等）"
            elif field == "serial_number":
                example_data[field] = "设备序列号"
            else:
                example_data[field] = f"示例{field}值"

        return {
            "model_name": model_name,
            "required_fields": mapping["required_fields"],
            "foreign_keys": list(mapping["foreign_keys"].keys()),
            "example_data": example_data,
            "notes": [
                "必填字段不能为空",
                "外键字段需要填写对应记录的name字段值",
                "如果外键记录不存在且开启自动创建，系统会自动创建",
                "Excel文件支持.xlsx和.xls格式",
            ],
        }
    except Exception as e:
        logger.error(f"获取示例数据失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"获取示例数据失败: {str(e)}") from e


@router.get("/models/{model_name}/fields", summary="获取模型字段详细信息")
async def get_model_fields(model_name: str, service: ImportExportService = Depends(get_import_export_service)):
    """获取指定模型的字段详细信息，包括必需字段提示"""
    try:
        field_info = service.get_model_field_info(model_name)
        return field_info
    except Exception as e:
        logger.error(f"获取模型字段信息失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"获取模型字段信息失败: {str(e)}") from e
