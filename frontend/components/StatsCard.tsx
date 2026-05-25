interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'red' | 'purple' | 'orange';
}

const colorMap = {
  blue: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/30'
  },
  green: {
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    border: 'border-green-500/30'
  },
  red: {
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/30'
  },
  purple: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/30'
  },
  orange: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/30'
  }
};

const StatsCard = ({ title, value, change, changeLabel, icon, color }: StatsCardProps) => {
  const colors = colorMap[color];

  return (
    <div className={`bg-dark-card border ${colors.border} rounded-xl p-4`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-slate-400">{title}</span>
        <div className={`p-2 rounded-lg ${colors.bg}`}>
          <span className={colors.text}>{icon}</span>
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-white">{value}</span>
        {change !== undefined && (
          <span className={`text-sm ${change >= 0 ? 'text-stock-up' : 'text-stock-down'}`}>
            {change >= 0 ? '+' : ''}{change} {changeLabel}
          </span>
        )}
      </div>
    </div>
  );
};

export default StatsCard;
