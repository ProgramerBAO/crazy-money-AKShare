import { StockSummary } from '@/types';

interface StockCardProps {
  summary: StockSummary;
  onClick: () => void;
}

const StockCard = ({ summary, onClick }: StockCardProps) => {
  const isUp = summary.change >= 0;

  return (
    <div
      className="bg-dark-card border border-dark-border rounded-xl p-4 cursor-pointer hover:border-blue-500 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-lg font-bold text-white">{summary.code}</span>
          <span className="text-sm text-slate-400 ml-2">{summary.name}</span>
        </div>
        <span className="text-xs text-slate-500">{summary.latest_date}</span>
      </div>

      <div className="flex items-end justify-between">
        <div>
          <div className={`text-2xl font-bold ${isUp ? 'text-stock-up' : 'text-stock-down'}`}>
            {summary.latest_close.toFixed(2)}
          </div>
          <div className={`text-sm ${isUp ? 'text-stock-up' : 'text-stock-down'}`}>
            {isUp ? '+' : ''}{summary.change.toFixed(2)} ({isUp ? '+' : ''}{summary.change_pct.toFixed(2)}%)
          </div>
        </div>
        <div className="text-right text-xs text-slate-400">
          <div>最高: {summary.latest_high.toFixed(2)}</div>
          <div>最低: {summary.latest_low.toFixed(2)}</div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-dark-border flex justify-between text-xs text-slate-500">
        <span>数据条数: {summary.total_records}</span>
        <span>区间: {summary.start_date} ~ {summary.end_date}</span>
      </div>
    </div>
  );
};

export default StockCard;
