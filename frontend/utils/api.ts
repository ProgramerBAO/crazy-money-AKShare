import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

interface CacheItem {
  data: any;
  timestamp: number;
}

const cache = new Map<string, CacheItem>();
const CACHE_TTL = 5 * 60 * 1000;

const getCacheKey = (url: string, params?: any): string => {
  return `${url}_${JSON.stringify(params || {})}`;
};

const getFromCache = (key: string): any | null => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  if (cached) {
    cache.delete(key);
  }
  return null;
};

const setToCache = (key: string, data: any): void => {
  if (cache.size >= 50) {
    const firstKey = cache.keys().next().value;
    if (firstKey) cache.delete(firstKey);
  }
  cache.set(key, {
    data,
    timestamp: Date.now()
  });
};

// 股票列表
export const getStockList = async (
  page: number = 1,
  limit: number = 50,
  keyword?: string
) => {
  const params: Record<string, string | number> = { page, limit };
  if (keyword) params.keyword = keyword;
  const response = await api.get('/stocks/list', { params });
  return response.data;
};

// 股票详情
export const getStockDetail = async (code: string) => {
  const response = await api.get(`/stocks/${code}`);
  return response.data;
};

// 股票历史数据
export const getStockHistory = async (
  code: string,
  startDate?: string,
  endDate?: string,
  limit: number = 100
) => {
  const params: Record<string, string | number> = { limit };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const response = await api.get(`/stocks/${code}/history`, { params });
  return response.data;
};

// 股票统计摘要
export const getStockSummary = async (code: string) => {
  const response = await api.get(`/stocks/${code}/summary`);
  return response.data;
};

// K线图数据
export const getKlineData = async (
  code: string,
  period: string = 'day',
  startDate?: string,
  endDate?: string
) => {
  const params: Record<string, string> = { period };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const response = await api.get(`/charts/${code}/kline`, { params });
  return response.data;
};

// 均线数据
export const getMaData = async (
  code: string,
  periods: string = '5,10,20,60',
  period: string = 'day',
  startDate?: string,
  endDate?: string
) => {
  const params: Record<string, string> = { periods, period };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const response = await api.get(`/charts/${code}/ma`, { params });
  return response.data;
};

// 成交量数据
export const getVolumeData = async (
  code: string,
  startDate?: string,
  endDate?: string
) => {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const response = await api.get(`/charts/${code}/volume`, { params });
  return response.data;
};

// 技术指标
export const getIndicators = async (
  code: string,
  indicators: string = 'macd,rsi,boll',
  startDate?: string,
  endDate?: string
) => {
  const params: Record<string, string> = { indicators };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const response = await api.get(`/charts/${code}/indicators`, { params });
  return response.data;
};

// 获取所有图表数据（聚合接口，带缓存）
export const getAllChartData = async (
  code: string,
  period: string = 'day',
  maPeriods: string = '5,10,20,60',
  indicators: string = 'macd,rsi,boll',
  startDate?: string,
  endDate?: string
) => {
  const params: Record<string, string> = {
    period,
    ma_periods: maPeriods,
    indicators
  };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const cacheKey = getCacheKey(`/charts/${code}/all`, params);
  const cachedData = getFromCache(cacheKey);

  if (cachedData) {
    return cachedData;
  }

  const response = await api.get(`/charts/${code}/all`, { params });
  setToCache(cacheKey, response.data);
  return response.data;
};

// 清除缓存
export const clearCache = () => {
  cache.clear();
};

// ==================== 系统控制API ====================

export interface ServiceStatus {
  running: boolean;
  pid?: number | string;
  uptime?: string;
  port?: number;
  status?: string;
  reason?: string;
}

export interface SystemStatus {
  backend: ServiceStatus;
  frontend: ServiceStatus;
  scheduler: ServiceStatus;
  ports: {
    backend: { in_use: boolean; port: number };
    frontend: { in_use: boolean; port: number };
  };
}

export interface CliResult {
  success: boolean;
  returncode: number;
  stdout?: string;
  stderr?: string;
  error?: string;
}

// 获取系统状态
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await api.get('/system/status');
  return response.data.data;
};

// 启动后端服务
export const startBackend = async (): Promise<{ running: boolean; pid?: number }> => {
  const response = await api.post('/system/start/backend');
  return response.data.data;
};

// 停止后端服务
export const stopBackend = async (): Promise<{ running: boolean }> => {
  const response = await api.post('/system/stop/backend');
  return response.data.data;
};

// 启动前端服务
export const startFrontend = async (): Promise<{ running: boolean; pid?: number }> => {
  const response = await api.post('/system/start/frontend');
  return response.data.data;
};

// 停止前端服务
export const stopFrontend = async (): Promise<{ running: boolean }> => {
  const response = await api.post('/system/stop/frontend');
  return response.data.data;
};

// 重启后端服务
export const restartBackend = async (): Promise<{ running: boolean; pid?: number }> => {
  const response = await api.post('/system/restart/backend');
  return response.data.data;
};

// 重启前端服务
export const restartFrontend = async (): Promise<{ running: boolean; pid?: number }> => {
  const response = await api.post('/system/restart/frontend');
  return response.data.data;
};

// 启动调度器
export const startScheduler = async (): Promise<{ running: boolean; pid?: number }> => {
  const response = await api.post('/system/start/scheduler');
  return response.data.data;
};

// 停止调度器
export const stopScheduler = async (): Promise<{ running: boolean }> => {
  const response = await api.post('/system/stop/scheduler');
  return response.data.data;
};

// 执行CLI命令
export const runCliCommand = async (
  command: string,
  options?: Record<string, any>
): Promise<CliResult> => {
  const response = await api.post('/system/cli', {
    command,
    options
  }, {
    timeout: 300000
  });
  return response.data.data;
};

// 执行CLI命令（支持流式进度）
export const runCliCommandStream = async (
  command: string,
  options?: Record<string, any>
): Promise<CliResult> => {
  const response = await api.post('/system/cli/stream', {
    command,
    options
  }, {
    timeout: 3600000
  });
  return response.data.data;
};

// WebSocket 进度消息类型
export interface ProgressMessage {
  type: 'progress' | 'log' | 'complete';
  task_id: string;
  progress?: number;
  message: string;
  current?: number;
  total?: number;
  status?: 'running' | 'success' | 'error';
  success?: boolean;
  level?: 'info' | 'warning' | 'error';
  timestamp?: string;
  stats?: {
    success: number;
    failed: number;
    skipped: number;
  };
}

// WebSocket 进度回调类型
export type ProgressCallback = (message: ProgressMessage) => void;

// WebSocket 连接管理
class WebSocketProgressClient {
  private ws: WebSocket | null = null;
  private callbacks: Map<string, ProgressCallback[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000;
  private currentChannel: string | null = null;

  connect(channel: string, timeoutMs: number = 5000): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.disconnect();
        reject(new Error('WebSocket 连接超时'));
      }, timeoutMs);

      if (this.ws && this.ws.readyState === WebSocket.OPEN && this.currentChannel === channel) {
        clearTimeout(timeout);
        resolve();
        return;
      }

      this.disconnect();
      this.currentChannel = channel;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//localhost:8000/ws/${channel}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log(`WebSocket connected: ${channel}`);
          clearTimeout(timeout);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: ProgressMessage = JSON.parse(event.data);
            const callbacks = this.callbacks.get(channel) || [];
            callbacks.forEach(cb => cb(message));
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        this.ws.onerror = (error) => {
          console.warn('WebSocket error:', error);
          clearTimeout(timeout);
          reject(new Error('WebSocket 连接失败'));
        };

        this.ws.onclose = (event) => {
          console.log(`WebSocket disconnected: ${channel}, code: ${event.code}`);
          clearTimeout(timeout);
          this.currentChannel = null;
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
              if (this.currentChannel !== channel) {
                this.connect(channel, timeoutMs).catch(console.error);
              }
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };
      } catch (e) {
        clearTimeout(timeout);
        reject(e);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.currentChannel = null;
    this.reconnectAttempts = 0;
  }

  onProgress(channel: string, callback: ProgressCallback) {
    if (!this.callbacks.has(channel)) {
      this.callbacks.set(channel, []);
    }
    this.callbacks.get(channel)!.push(callback);

    return () => {
      const callbacks = this.callbacks.get(channel);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const wsProgressClient = new WebSocketProgressClient();