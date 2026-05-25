import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Header from '@/components/Header';
import StockList from '@/components/StockList';
import StatsCard from '@/components/StatsCard';
import { getStockList } from '@/utils/api';

const HomePage = () => {
  const [keyword, setKeyword] = useState('');
  const [totalStocks, setTotalStocks] = useState(0);
  const router = useRouter();

  useEffect(() => {
    // 获取URL参数中的搜索关键词
    if (router.query.keyword) {
      setKeyword(decodeURIComponent(router.query.keyword as string));
    }

    // 获取股票总数
    const fetchTotal = async () => {
      try {
        const response = await getStockList(1, 1);
        if (response.code === 200) {
          setTotalStocks(response.data.total);
        }
      } catch (error) {
        console.error('获取股票总数失败:', error);
      }
    };
    fetchTotal();
  }, [router.query]);

  return (
    <div className="min-h-screen bg-dark-bg">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatsCard
            title="股票总数"
            value={totalStocks.toLocaleString()}
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>}
            color="blue"
          />
          <StatsCard
            title="数据格式"
            value="CSV / Parquet"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>}
            color="green"
          />
          <StatsCard
            title="数据源"
            value="腾讯 / 东方财富"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>}
            color="purple"
          />
          <StatsCard
            title="更新频率"
            value="每日自动"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>}
            color="orange"
          />
        </div>

        {/* 页面标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">股票列表</h2>
          <p className="text-slate-400">
            {keyword ? `搜索结果: "${keyword}"` : '浏览全部股票数据'}
          </p>
        </div>

        {/* 股票列表 */}
        <StockList keyword={keyword} />

        {/* 页脚 */}
        <footer className="mt-12 py-6 border-t border-dark-border text-center text-slate-500 text-sm">
          <p>Crazy Money - A股量化数据平台</p>
          <p className="mt-1">数据仅供参考，不构成投资建议</p>
        </footer>
      </main>
    </div>
  );
};

export default HomePage;
