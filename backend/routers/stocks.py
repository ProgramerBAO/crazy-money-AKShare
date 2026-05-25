"""
股票数据路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
import pandas as pd
from pathlib import Path

from services.data_service import DataService

router = APIRouter()
data_service = DataService()

@router.get("/list", summary="获取股票列表")
async def get_stock_list(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=10000),
    keyword: Optional[str] = Query(None)
):
    try:
        stocks = data_service.get_stock_list()
        
        if keyword:
            keyword = keyword.lower()
            stocks = [s for s in stocks if 
                     keyword in s["code"].lower() or 
                     keyword in s["name"].lower()]
        
        total = len(stocks)
        start = (page - 1) * limit
        end = start + limit
        paginated_stocks = stocks[start:end]
        
        return {
            "code": 200,
            "data": {
                "list": paginated_stocks,
                "total": total,
                "page": page,
                "limit": limit
            },
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}", summary="获取股票详情")
async def get_stock_detail(code: str):
    try:
        code = str(code).zfill(6)
        stock = data_service.get_stock_by_code(code)
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"股票 {code} 不存在")
        
        return {
            "code": 200,
            "data": stock,
            "message": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}/history", summary="获取股票历史数据")
async def get_stock_history(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500)
):
    try:
        code = str(code).zfill(6)
        df = data_service.get_stock_history(code, start_date, end_date)
        
        if df.empty:
            return {
                "code": 200,
                "data": [],
                "message": "success"
            }
        
        df = df.tail(limit)
        data = df.to_dict("records")
        
        return {
            "code": 200,
            "data": data,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}/summary", summary="获取股票统计摘要")
async def get_stock_summary(code: str):
    try:
        code = str(code).zfill(6)
        summary = data_service.get_stock_summary(code)
        
        if not summary:
            raise HTTPException(status_code=404, detail=f"股票 {code} 不存在或无数据")
        
        return {
            "code": 200,
            "data": summary,
            "message": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
