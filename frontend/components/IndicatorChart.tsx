import { useEffect, useRef, useState, useCallback } from 'react';

interface IndicatorChartProps {
  code: string;
  indicator: 'macd' | 'rsi' | 'boll';
}

interface IndicatorData {
  dates: string[];
  macd_dif?: (number | null)[];
  macd_dea?: (number | null)[];
  macd_bar?: (number | null)[];
  rsi?: (number | null)[];
  boll_up?: (number | null)[];
  boll_mid?: (number | null)[];
  boll_down?: (number | null)[];
}

const IndicatorChart = ({ code, indicator }: IndicatorChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [isClient, setIsClient] = useState(false);
  const [indicatorData, setIndicatorData] = useState<IndicatorData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setIsClient(true);
    return () => {
      setIsClient(false);
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/charts/${code}/indicators?indicators=${indicator}`);
        const data = await response.json();
        if (data.code === 200) {
          setIndicatorData(data.data);
        }
      } catch (error) {
        console.error(`获取${indicator}指标失败:`, error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [code, indicator]);

  const renderChart = useCallback(async () => {
    if (!isClient || !chartContainerRef.current || !indicatorData) return;

    const echarts = await import('echarts');
    const chart = (echarts as any).init(chartContainerRef.current);
    const dates = indicatorData.dates;

    let option: echarts.EChartsOption;

    if (indicator === 'macd') {
      option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          borderColor: '#334155',
          textStyle: { color: '#e2e8f0' }
        },
        grid: {
          left: '10%',
          right: '5%',
          top: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { show: false }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
        },
        series: [
          {
            name: 'DIF',
            type: 'line',
            data: indicatorData.macd_dif,
            lineStyle: { color: '#3b82f6', width: 1 },
            showSymbol: false
          },
          {
            name: 'DEA',
            type: 'line',
            data: indicatorData.macd_dea,
            lineStyle: { color: '#f59e0b', width: 1 },
            showSymbol: false
          },
          {
            name: 'MACD',
            type: 'bar',
            data: indicatorData.macd_bar?.map((v) => ({
              value: v,
              itemStyle: {
                color: (v ?? 0) >= 0 ? '#ef4444' : '#22c55e'
              }
            }))
          }
        ]
      };
    } else if (indicator === 'rsi') {
      option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          borderColor: '#334155',
          textStyle: { color: '#e2e8f0' }
        },
        grid: {
          left: '10%',
          right: '5%',
          top: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { show: false }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
        },
        series: [
          {
            name: 'RSI',
            type: 'line',
            data: indicatorData.rsi,
            lineStyle: { color: '#8b5cf6', width: 1 },
            showSymbol: false,
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: { color: '#ef4444', type: 'dashed' },
              data: [{ yAxis: 70, label: { formatter: '70', color: '#ef4444' } }]
            }
          }
        ]
      };
    } else {
      option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          borderColor: '#334155',
          textStyle: { color: '#e2e8f0' }
        },
        grid: {
          left: '10%',
          right: '5%',
          top: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { show: false }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
        },
        series: [
          {
            name: '上轨',
            type: 'line',
            data: indicatorData.boll_up,
            lineStyle: { color: '#ef4444', width: 1, type: 'dashed' },
            showSymbol: false
          },
          {
            name: '中轨',
            type: 'line',
            data: indicatorData.boll_mid,
            lineStyle: { color: '#3b82f6', width: 1 },
            showSymbol: false
          },
          {
            name: '下轨',
            type: 'line',
            data: indicatorData.boll_down,
            lineStyle: { color: '#22c55e', width: 1, type: 'dashed' },
            showSymbol: false
          }
        ]
      };
    }

    chart.setOption(option);

    const handleResize = () => {
      chart.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [isClient, indicatorData, indicator]);

  useEffect(() => {
    const cleanup = renderChart();
    return () => {
      if (cleanup) cleanup.then(fn => fn && fn());
    };
  }, [renderChart]);

  const title = {
    macd: 'MACD',
    rsi: 'RSI',
    boll: '布林带'
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">{title[indicator]}</h3>
      {loading ? (
        <div className="h-40 flex items-center justify-center">
          <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : isClient ? (
        <div ref={chartContainerRef} className="w-full h-40" />
      ) : (
        <div className="h-40 flex items-center justify-center">
          <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
};

export default IndicatorChart;
