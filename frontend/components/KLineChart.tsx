import { useEffect, useRef, useState, useCallback } from 'react';
import { getAllChartData } from '@/utils/api';

interface KLineChartProps {
  code: string;
  period?: 'day' | 'week' | 'month';
}

const KLineChart = ({ code, period = 'day' }: KLineChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<any>(null);
  const [isClient, setIsClient] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsClient(true);
    return () => {
      setIsClient(false);
    };
  }, []);

  const disposeChart = useCallback(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispose();
      chartInstanceRef.current = null;
    }
  }, []);

  const renderChart = useCallback(async () => {
    if (!isClient || !chartContainerRef.current) return;

    disposeChart();
    setIsLoading(true);
    
    try {
      const echarts = await import('echarts');

      const response = await getAllChartData(code, period);

      if (response.code !== 200) {
        return;
      }

      const { kline, ma } = response.data;

      if (!kline || !kline.dates || !kline.items || kline.items.length === 0) {
        return;
      }

      const dates = kline.dates;
      const klineValues = kline.items.map((item: number[]) => [item[0], item[1], item[2], item[3]]);
      const volumes = kline.items.map((item: number[]) => item[4] || 0);

      const ma5Data = (ma.ma5 as number[]) || [];
      const ma10Data = (ma.ma10 as number[]) || [];
      const ma20Data = (ma.ma20 as number[]) || [];
      const ma60Data = (ma.ma60 as number[]) || [];

      const colors = dates.map((_: string, i: number) => {
        if (i === 0) return '#ef4444';
        return klineValues[i][1] >= klineValues[i - 1][1] ? '#ef4444' : '#22c55e';
      });

      const chart = (echarts as any).init(chartContainerRef.current);
      chartInstanceRef.current = chart;

      const option: any = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          borderColor: '#334155',
          textStyle: { color: '#e2e8f0' },
        },
        grid: [
          { left: '10%', right: '5%', top: '5%', height: '55%' },
          { left: '10%', right: '5%', top: '68%', height: '20%' }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8', fontSize: 10 },
            splitLine: { show: false }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { show: false },
            splitLine: { show: false }
          }
        ],
        yAxis: [
          {
            type: 'value',
            scale: true,
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8', fontSize: 10 },
            splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
          },
          {
            type: 'value',
            gridIndex: 1,
            scale: true,
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8', fontSize: 10 },
            splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
          }
        ],
        dataZoom: [
          { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '12%',
            start: 50,
            end: 100,
            height: 20,
            borderColor: '#475569',
            fillerColor: 'rgba(59, 130, 246, 0.2)',
            handleStyle: { color: '#3b82f6' },
            textStyle: { color: '#94a3b8' }
          }
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: klineValues,
            itemStyle: {
              color: '#ef4444',
              color0: '#22c55e',
              borderColor: '#ef4444',
              borderColor0: '#22c55e'
            }
          },
          { name: 'MA5', type: 'line', data: ma5Data, smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, showSymbol: false },
          { name: 'MA10', type: 'line', data: ma10Data, smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, showSymbol: false },
          { name: 'MA20', type: 'line', data: ma20Data, smooth: true, lineStyle: { width: 1, color: '#8b5cf6' }, showSymbol: false },
          { name: 'MA60', type: 'line', data: ma60Data, smooth: true, lineStyle: { width: 1, color: '#ec4899' }, showSymbol: false },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes.map((v: number, i: number) => ({
              value: v,
              itemStyle: { color: colors[i] }
            }))
          }
        ]
      };

      chart.setOption(option, true);

      const handleResize = () => {
        chart.resize();
      };

      window.addEventListener('resize', handleResize);

      chart.cleanup = () => {
        window.removeEventListener('resize', handleResize);
        chart.dispose();
      };
    } catch (error) {
      console.error('[KLineChart] 渲染图表失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isClient, code, period, disposeChart]);

  useEffect(() => {
    renderChart();
    return () => {
      disposeChart();
    };
  }, [renderChart, disposeChart]);

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-4">
      {isClient ? (
        <div className="relative w-full" style={{ height: '400px' }}>
          <div 
            ref={chartContainerRef} 
            className="w-full" 
            style={{ height: '400px' }}
          />
          {isLoading && (
            <div className="absolute inset-0 bg-dark-card/80 flex items-center justify-center z-10">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      ) : (
        <div className="w-full h-[400px] flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
};

export default KLineChart;
