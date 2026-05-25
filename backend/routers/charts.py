"""
图表数据路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
import pandas as pd

from services.chart_service import ChartService

router = APIRouter()
chart_service = ChartService()

@router.get("/{code}/kline", summary="获取K线图数据")
async def get_kline_data(
    code: str,
    period: str = Query("day"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        code = str(code).zfill(6)
        kline_data = chart_service.get_kline_data(code, period, start_date, end_date)
        
        if not kline_data:
            return {
                "code": 200,
                "data": {"dates": [], "items": []},
                "message": "success"
            }
        
        return {
            "code": 200,
            "data": kline_data,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}/ma", summary="获取均线数据")
async def get_ma_data(
    code: str,
    periods: str = Query("5,10,20,60"),
    period: str = Query("day"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        code = str(code).zfill(6)
        period_list = [int(p) for p in periods.split(",")]
        ma_data = chart_service.get_ma_data(code, period_list, period, start_date, end_date)
        
        return {
            "code": 200,
            "data": ma_data,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}/volume", summary="获取成交量数据")
async def get_volume_data(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        code = str(code).zfill(6)
        volume_data = chart_service.get_volume_data(code, start_date, end_date)
        
        return {
            "code": 200,
            "data": volume_data,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}/indicators", summary="获取技术指标")
async def get_indicators(
    code: str,
    indicators: str = Query("macd,rsi,boll"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        code = str(code).zfill(6)
        indicator_list = [i.strip() for i in indicators.split(",")]
        indicator_data = chart_service.get_indicators(code, indicator_list, start_date, end_date)
        
        return {
            "code": 200,
            "data": indicator_data,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}/all", summary="获取所有图表数据（聚合接口）")
async def get_all_chart_data(
    code: str,
    period: str = Query("day", description="周期：day/week/month"),
    ma_periods: str = Query("5,10,20,60", description="均线周期，逗号分隔"),
    indicators: str = Query("macd,rsi,boll", description="技术指标，逗号分隔"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期")
):
    """
    聚合接口：一次性获取K线、均线、技术指标数据
    
    - **code**: 股票代码（6位数字）
    - **period**: 数据周期（day/week/month）
    - **ma_periods**: 均线周期列表，如 5,10,20,60
    - **indicators**: 技术指标列表，如 macd,rsi,boll
    """
    try:
        code = str(code).zfill(6)
        ma_period_list = [int(p.strip()) for p in ma_periods.split(",")]
        indicator_list = [i.strip() for i in indicators.split(",")]
        
        all_data = chart_service.get_all_chart_data(
            code, period, ma_period_list, indicator_list, start_date, end_date
        )
        
        return {
            "code": 200,
            "data": all_data,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
