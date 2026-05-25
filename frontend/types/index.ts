// 股票信息
export interface Stock {
  code: string;
  name: string;
}

// 股票历史数据
export interface StockHistory {
  date: string;
  code: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume?: number;
  amount?: number;
  source?: string;
  adjust?: string;
}

// 股票统计摘要
export interface StockSummary {
  code: string;
  name: string;
  latest_date: string;
  latest_open: number;
  latest_close: number;
  latest_high: number;
  latest_low: number;
  latest_volume?: number;
  latest_amount?: number;
  total_records: number;
  start_date: string;
  end_date: string;
  avg_close: number;
  max_close: number;
  min_close: number;
  std_close: number;
  change: number;
  change_pct: number;
}

// K线数据
export interface KlineData {
  dates: string[];
  items: number[][]; // [open, close, low, high, volume]
}

// 均线数据
export interface MaData {
  dates: string[];
  [key: string]: number[] | string[];
}

// 成交量数据
export interface VolumeData {
  dates: string[];
  volumes: number[];
  colors: string[];
}

// 技术指标数据
export interface IndicatorData {
  dates: string[];
  macd_dif?: number[];
  macd_dea?: number[];
  macd_bar?: number[];
  rsi?: number[];
  boll_up?: number[];
  boll_mid?: number[];
  boll_down?: number[];
}

// API 响应
export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

// 分页结果
export interface PagedResult<T> {
  list: T[];
  total: number;
  page: number;
  limit: number;
}
