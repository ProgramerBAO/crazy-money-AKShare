import { StockSummary } from '@/types';

interface StockSummaryCardProps {
  summary: StockSummary;
}

const StockSummaryCard = ({ summary }: StockSummaryCardProps) => {
  const isUp = summary.change >= 0;

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">{summary.code}</h2>
          <p className="text-slate-400">{summary.name}</p>
        </div>
        <span className="text-sm text-slate-500 bg-dark-bg px-3 py-1 rounded-full">
          qfq
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <p className="text-sm text-slate-400 mb-1">最新价</p>
          <p className={`text-3xl font-bold ${isUp ? 'text-stock-up' : 'text-stock-down'}`}>
            {summary.latest_close.toFixed(2)}
          </p>
        </div>
        <div className="flex flex-col justify-end">
          <p className="text-sm text-slate-400 mb-1">涨跌幅</p>
          <p className={`text-xl font-bold ${isUp ? 'text-stock-up' : 'text-stock-down'}`}>
            {isUp ? '+' : ''}{summary.change_pct.toFixed(2)}%
            <span className="text-sm font-normal ml-2">
              ({isUp ? '+' : ''}{summary.change.toFixed(2)})
            </span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 text-center">
        <div className="bg-dark-bg rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">开盘</p>
          <p className="text-sm font-medium text-white">{summary.latest_open.toFixed(2)}</p>
        </div>
        <div className="bg-dark-bg rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">最高</p>
          <p className="text-sm font-medium text-stock-up">{summary.latest_high.toFixed(2)}</p>
        </div>
        <div className="bg-dark-bg rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">最低</p>
          <p className="text-sm font-medium text-stock-down">{summary.latest_low.toFixed(2)}</p>
        </div>
        <div className="bg-dark-bg rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">成交量</p>
          <p className="text-sm font-medium text-white">{summary.latest_volume?.toLocaleString() || '-'}</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-dark-border flex justify-between text-xs text-slate-500">
        <span>数据周期: {summary.start_date} ~ {summary.end_date}</span>
        <span>共 {summary.total_records.toLocaleString()} 条记录</span>
      </div>
    </div>
  );
};

export default StockSummaryCard;
