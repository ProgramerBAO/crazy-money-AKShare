import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { getStockList, getStockSummary } from '@/utils/api';
import { Stock, StockSummary } from '@/types';
import StockCard from './StockCard';

interface StockListProps {
  keyword?: string;
}

const StockList = ({ keyword }: StockListProps) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [summaries, setSummaries] = useState<Map<string, StockSummary>>(new Map());
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const router = useRouter();

  useEffect(() => {
    loadStocks(1);
  }, [keyword]);

  const loadStocks = async (pageNum: number) => {
    setLoading(true);
    try {
      const response = await getStockList(pageNum, 20, keyword);
      if (response.code === 200) {
        const newStocks = response.data.list as Stock[];
        setTotal(response.data.total);
        
        if (pageNum === 1) {
          setStocks(newStocks);
        } else {
          setStocks(prev => [...prev, ...newStocks]);
        }
        
        setHasMore(newStocks.length > 0 && pageNum * 20 < response.data.total);
        
        // 批量获取股票摘要
        const summaryPromises = newStocks.map(stock => getStockSummary(stock.code));
        const summaryResults = await Promise.allSettled(summaryPromises);
        
        setSummaries(prev => {
          const newMap = new Map(prev);
          summaryResults.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value.code === 200) {
              newMap.set(newStocks[index].code, result.value.data);
            }
          });
          return newMap;
        });
      }
    } catch (error) {
      console.error('加载股票列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
      loadStocks(page + 1);
    }
  };

  const handleStockClick = (code: string) => {
    router.push(`/stock/${code}`);
  };

  if (loading && stocks.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-dark-card border border-dark-border rounded-xl p-4 skeleton h-40" />
        ))}
      </div>
    );
  }

  if (stocks.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">暂无股票数据</p>
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {stocks.map(stock => {
          const summary = summaries.get(stock.code);
          if (!summary) {
            return (
              <div key={stock.code} className="bg-dark-card border border-dark-border rounded-xl p-4 skeleton h-40" />
            );
          }
          return (
            <StockCard
              key={stock.code}
              summary={summary}
              onClick={() => handleStockClick(stock.code)}
            />
          );
        })}
      </div>

      {hasMore && (
        <div className="flex justify-center mt-8">
          <button
            onClick={handleLoadMore}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
          >
            {loading ? '加载中...' : '加载更多'}
          </button>
        </div>
      )}
    </div>
  );
};

export default StockList;
