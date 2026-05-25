import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const TestChart = () => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      grid: [
        { left: '10%', right: '5%', top: '5%', height: '55%' },
        { left: '10%', right: '5%', top: '68%', height: '20%' }
      ],
      xAxis: [
        {
          type: 'category',
          data: ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 }
        },
        {
          type: 'category',
          gridIndex: 1,
          data: ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
          axisLabel: { show: false }
        }
      ],
      yAxis: [
        {
          type: 'value',
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 }
        },
        {
          type: 'value',
          gridIndex: 1,
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 }
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: [
            [10, 12, 8, 11],
            [11, 14, 10, 13],
            [13, 15, 12, 14],
            [14, 16, 13, 15],
            [15, 18, 14, 17]
          ],
          itemStyle: {
            color: '#ef4444',
            color0: '#22c55e',
            borderColor: '#ef4444',
            borderColor0: '#22c55e'
          }
        },
        {
          name: 'MA5',
          type: 'line',
          data: [10, 11.5, 13, 14.5, 16],
          smooth: true,
          lineStyle: { width: 1, color: '#f59e0b' },
          showSymbol: false
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: [100, 200, 150, 250, 300],
          itemStyle: { color: '#ef4444' }
        }
      ]
    };

    chart.setOption(option);

    const handleResize = () => {
      chart.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, []);

  return (
    <div ref={chartRef} className="w-full" style={{ height: '400px' }} />
  );
};

export default TestChart;
