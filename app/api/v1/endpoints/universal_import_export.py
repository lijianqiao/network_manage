"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_import_export.py
@DateTime: 2025/06/20 00:00:00
@Docs: 通用导入导出API端点 - 演示如何使用通用工具
"""

import io
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Path, UploadFile, status
from fastapi.responses import StreamingResponse

from app.models.network_models import Brand, Device, DeviceGroup, DeviceModel, Region
from app.schemas.base import SuccessResponse
from app.utils.logger import logger
from app.utils.universal_import_export import get_import_export_tool

router = APIRouter(prefix="/universal", tags=["通用导入导出"])

# 模型映射表
MODEL_MAPPING = {
    "brands": Brand,
    "regions": Region,
    "device_models": DeviceModel,
    "device_groups": DeviceGroup,
    "devices": Device,
}


@router.get(
    "/{model_name}/template",
    summary="下载通用模板",
    description="下载指定模型的导入模板文件",
)
async def download_template(
    model_name: Literal["brands", "regions", "device_models", "device_groups", "devices"] = Path(
        ..., description="模型名称"
    ),
):
    """下载通用导入模板"""
    try:
        # 获取模型类
        model_class = MODEL_MAPPING.get(model_name)
        if not model_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"不支持的模型: {model_name}",
            )

        # 获取导入导出工具
        tool = await get_import_export_tool(model_class)

        # 生成模板
        excel_data = await tool.export_template()

        # 生成文件名
        filename = tool.get_filename("template")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载{model_name}模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载模板失败: {str(e)}",
        ) from e


@router.post(
    "/{model_name}/import",
    summary="通用数据导入",
    description="从Excel文件导入指定模型的数据",
)
async def import_data(
    model_name: Literal["brands", "regions", "device_models", "device_groups", "devices"] = Path(
        ..., description="模型名称"
    ),
    file: UploadFile = File(..., description="要导入的Excel文件"),
):
    """通用数据导入"""
    try:
        # 获取模型类
        model_class = MODEL_MAPPING.get(model_name)
        if not model_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"不支持的模型: {model_name}",
            )

        # 验证文件类型
        if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传Excel文件（.xlsx或.xls格式）")

        # 获取导入导出工具
        tool = await get_import_export_tool(model_class)

        # 执行导入
        result = await tool.import_data(file)

        return SuccessResponse(data=result, message=f"{model_class.__name__}数据导入完成")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入{model_name}数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}",
        ) from e


@router.get(
    "/{model_name}/export",
    summary="通用数据导出",
    description="导出指定模型的数据到Excel文件",
)
async def export_data(
    model_name: Literal["brands", "regions", "device_models", "device_groups", "devices"] = Path(
        ..., description="模型名称"
    ),
):
    """通用数据导出"""
    try:
        # 获取模型类
        model_class = MODEL_MAPPING.get(model_name)
        if not model_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"不支持的模型: {model_name}",
            )

        # 获取导入导出工具
        tool = await get_import_export_tool(model_class)

        # 导出数据
        excel_data = await tool.export_data()

        # 生成文件名
        filename = tool.get_filename("export")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出{model_name}数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}",
        ) from e


@router.get(
    "/{model_name}/fields",
    summary="获取模型字段信息",
    description="获取指定模型的字段信息，用于前端动态生成表单",
)
async def get_model_fields(
    model_name: Literal["brands", "regions", "device_models", "device_groups", "devices"] = Path(
        ..., description="模型名称"
    ),
):
    """获取模型字段信息"""
    try:
        # 获取模型类
        model_class = MODEL_MAPPING.get(model_name)
        if not model_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"不支持的模型: {model_name}",
            )

        # 获取导入导出工具
        tool = await get_import_export_tool(model_class)

        # 获取字段信息
        fields = tool.get_field_info()

        return SuccessResponse(data=fields, message="获取字段信息成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{model_name}字段信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段信息失败: {str(e)}",
        ) from e


@router.get(
    "/supported-models",
    summary="获取支持的模型列表",
    description="获取所有支持通用导入导出的模型列表",
)
async def get_supported_models():
    """获取支持的模型列表"""
    try:
        models_info = []
        for model_name, model_class in MODEL_MAPPING.items():
            # 获取导入导出工具并初始化
            tool = await get_import_export_tool(model_class)
            field_info = tool.get_field_info()

            models_info.append(
                {
                    "model_name": model_name,
                    "model_class": model_class.__name__,
                    "table_name": model_class._meta.table,
                    "description": getattr(model_class._meta, "table_description", ""),
                    "field_count": len(field_info["fields"]),
                    "required_fields": len([f for f in field_info["fields"] if f["required"]]),
                }
            )

        return SuccessResponse(
            data={
                "models": models_info,
                "total_count": len(models_info),
            },
            message="获取支持的模型列表成功",
        )
    except Exception as e:
        logger.error(f"获取支持的模型列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}",
        ) from e
