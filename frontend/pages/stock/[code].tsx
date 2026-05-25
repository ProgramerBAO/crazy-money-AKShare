import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import dynamic from 'next/dynamic';
import Header from '@/components/Header';
import StockSummaryCard from '@/components/StockSummaryCard';
import StatsCard from '@/components/StatsCard';
import { getStockSummary } from '@/utils/api';
import { StockSummary } from '@/types';

// 动态导入图表组件，只在客户端渲染
const KLineChart = dynamic(() => import('@/components/KLineChart'), {
  ssr: false,
  loading: () => <div className="h-[400px] bg-dark-card flex items-center justify-center">
    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
  </div>
});

const IndicatorChart = dynamic(() => import('@/components/IndicatorChart'), {
  ssr: false,
  loading: () => <div className="h-[200px] bg-dark-card flex items-center justify-center">
    <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
  </div>
});

interface StockDetailPageProps {
  initialCode: string;
}

const StockDetailPage = ({ initialCode }: StockDetailPageProps) => {
  const [summary, setSummary] = useState<StockSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day');
  const router = useRouter();
  const code = initialCode || (router.query.code as string);

  useEffect(() => {
    if (!code) return;

    const fetchData = async () => {
      setLoading(true);
      console.log('fetchData called with code:', code);
      try {
        const response = await getStockSummary(code);
        console.log('getStockSummary response:', response);
        if (response.code === 200) {
          setSummary(response.data);
          console.log('summary set:', response.data);
        }
      } catch (error) {
        console.error('获取股票摘要失败:', error);
      } finally {
        setLoading(false);
        console.log('loading set to false');
      }
    };

    fetchData();
  }, [code]);

  if (!code) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <p className="text-slate-400">股票代码不能为空</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-bg">
        <Header />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        </main>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-dark-bg">
        <Header />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center py-20">
            <p className="text-slate-400">股票 {code} 不存在或无数据</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 返回按钮 */}
        <button
          onClick={() => router.push('/')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-6"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>

        {/* 股票摘要卡片 */}
        <StockSummaryCard summary={summary} />

        {/* K线图 */}
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">K线图</h3>
            <div className="flex gap-2">
              {(['day', 'week', 'month'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-4 py-1 rounded-lg text-sm font-medium transition-colors ${
                    period === p
                      ? 'bg-blue-600 text-white'
                      : 'bg-dark-card text-slate-400 hover:text-white'
                  }`}
                >
                  {p === 'day' ? '日线' : p === 'week' ? '周线' : '月线'}
                </button>
              ))}
            </div>
          </div>
          <KLineChart code={code} period={period} />
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <StatsCard
            title="平均收盘价"
            value={summary.avg_close.toFixed(2)}
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>}
            color="blue"
          />
          <StatsCard
            title="最高收盘价"
            value={summary.max_close.toFixed(2)}
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>}
            color="red"
          />
          <StatsCard
            title="最低收盘价"
            value={summary.min_close.toFixed(2)}
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />
            </svg>}
            color="green"
          />
          <StatsCard
            title="标准差"
            value={summary.std_close.toFixed(2)}
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>}
            color="purple"
          />
        </div>

        {/* 技术指标 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <IndicatorChart code={code} indicator="macd" />
          <IndicatorChart code={code} indicator="rsi" />
          <IndicatorChart code={code} indicator="boll" />
        </div>

        {/* 页脚 */}
        <footer className="mt-12 py-6 border-t border-dark-border text-center text-slate-500 text-sm">
          <p>Crazy Money - A股量化数据平台</p>
          <p className="mt-1">数据仅供参考，不构成投资建议</p>
        </footer>
      </main>
    </div>
  );
};

export async function getServerSideProps(context: any) {
  const { code } = context.params;
  
  return {
    props: {
      initialCode: code,
    },
  };
}

export default StockDetailPage;
