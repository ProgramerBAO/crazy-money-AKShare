import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Head from 'next/head';
import Link from 'next/link';
import {
  getSystemStatus,
  startBackend,
  stopBackend,
  restartBackend,
  startFrontend,
  stopFrontend,
  restartFrontend,
  startScheduler,
  stopScheduler,
  runCliCommand,
  runCliCommandStream,
  wsProgressClient,
  ProgressMessage,
  SystemStatus,
  CliResult
} from '@/utils/api';

const Header = dynamic(() => import('@/components/Header'), { ssr: false });

interface Task {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'success' | 'error';
  output: string;
  progress: number;
  startTime?: string;
  endTime?: string;
  stats?: {
    success: number;
    failed: number;
    skipped: number;
  };
  taskType: string;
}

const STORAGE_KEY = 'crazy-money-tasks';

const AdminPage = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTaskType, setActiveTaskType] = useState<string | null>(null);

  const loadTasksFromStorage = useCallback(() => {
    if (typeof window === 'undefined') return;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed: Task[] = JSON.parse(stored);
        setTasks(parsed);
        const runningTask = parsed.find(t => t.status === 'running');
        if (runningTask) {
          setActiveTaskType(runningTask.taskType);
        }
      }
    } catch (error) {
      console.error('加载任务历史失败:', error);
    }
  }, []);

  const saveTasksToStorage = useCallback((newTasks: Task[]) => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newTasks));
    } catch (error) {
      console.error('保存任务历史失败:', error);
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('获取状态失败:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasksFromStorage();
  }, [loadTasksFromStorage]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const hasRunningTask = useCallback(() => {
    return tasks.some(t => t.status === 'running');
  }, [tasks]);

  const handleServiceAction = async (
    action: 'start' | 'stop' | 'restart',
    service: 'backend' | 'frontend' | 'scheduler'
  ) => {
    setLoading(true);
    try {
      if (service === 'backend') {
        if (action === 'start') await startBackend();
        else if (action === 'stop') await stopBackend();
        else await restartBackend();
      } else if (service === 'frontend') {
        if (action === 'start') await startFrontend();
        else if (action === 'stop') await stopFrontend();
        else await restartFrontend();
      } else {
        if (action === 'start') await startScheduler();
        else if (action === 'stop') await stopScheduler();
        else throw new Error('调度器不支持重启');
      }
      await fetchStatus();
    } catch (error) {
      console.error(`${service} ${action} 失败:`, error);
    } finally {
      setLoading(false);
    }
  };

  const runTask = async (
    taskType: string,
    taskName: string,
    command: string,
    options?: Record<string, any>
  ) => {
    if (hasRunningTask()) {
      console.warn('已有任务正在运行，无法启动新任务');
      return;
    }

    const uniqueTaskId = `${taskType}_${Date.now()}`;
    const task: Task = {
      id: uniqueTaskId,
      name: taskName,
      status: 'running',
      output: '正在连接进度服务器...\n',
      progress: 0,
      startTime: new Date().toISOString(),
      taskType: taskType
    };

    const newTasks = [task, ...tasks];
    setTasks(newTasks);
    saveTasksToStorage(newTasks);
    setActiveTaskType(taskType);

    let unsubscribe: (() => void) | null = null;

    try {
      await wsProgressClient.connect(command, 10000);
    } catch (error: any) {
      const errorMsg = error.message || '连接进度服务器失败';
      setTasks(prev => {
        const updated = prev.map(t => {
          if (t.id === uniqueTaskId) {
            const newTask: Task = {
              ...t,
              status: 'error',
              output: `连接进度服务器失败: ${errorMsg}\n请检查后端服务是否正常运行。`,
              endTime: new Date().toISOString()
            };
            return newTask;
          }
          return t;
        });
        saveTasksToStorage(updated);
        return updated;
      });
      setActiveTaskType(null);
      return;
    }

    try {
      unsubscribe = wsProgressClient.onProgress(command, (msg: ProgressMessage) => {
        setTasks(prev => {
          const updated = prev.map(t => {
            if (t.id !== uniqueTaskId) return t;

            if (msg.type === 'progress') {
              const newOutput = t.output + (msg.message || '') + '\n';
              const newTask: Task = {
                ...t,
                progress: msg.progress || t.progress,
                output: newOutput.slice(-5000),
                status: 'running'
              };
              return newTask;
            }

            if (msg.type === 'log') {
              const levelPrefix = msg.level === 'error' ? '❌ ' : msg.level === 'warning' ? '⚠️ ' : '';
              const newOutput = t.output + levelPrefix + msg.message + '\n';
              const newTask: Task = {
                ...t,
                output: newOutput.slice(-5000)
              };
              return newTask;
            }

            if (msg.type === 'complete') {
              const newTask: Task = {
                ...t,
                progress: msg.success ? 100 : t.progress,
                status: msg.success ? 'success' : 'error',
                output: t.output + (msg.message || (msg.success ? '执行成功' : '执行失败')) + '\n',
                endTime: new Date().toISOString(),
                stats: msg.stats
              };
              return newTask;
            }

            return t;
          });
          saveTasksToStorage(updated);
          return updated;
        });
      });

      const result: CliResult = await runCliCommandStream(command, options);

      const output = (result.stdout || '') + (result.stderr || '') || result.error || '';

      setTasks(prev => {
        const updated = prev.map(t => {
          if (t.id === uniqueTaskId) {
            const newTask: Task = {
              ...t,
              status: result.success ? 'success' : 'error',
              output: output || (result.success ? '执行成功' : '执行失败'),
              progress: result.success ? 100 : t.progress,
              endTime: new Date().toISOString()
            };
            return newTask;
          }
          return t;
        });
        saveTasksToStorage(updated);
        return updated;
      });
    } catch (error: any) {
      setTasks(prev => {
        const updated = prev.map(t => {
          if (t.id === uniqueTaskId) {
            const newTask: Task = {
              ...t,
              status: 'error',
              output: `执行失败: ${error.message}`,
              endTime: new Date().toISOString()
            };
            return newTask;
          }
          return t;
        });
        saveTasksToStorage(updated);
        return updated;
      });
    } finally {
      if (unsubscribe) {
        unsubscribe();
      }
      wsProgressClient.disconnect();
      setActiveTaskType(null);
    }
  };

  const formatUptime = (uptime?: string) => {
    return uptime || '已停止';
  };

  const getStatusColor = (running: boolean) => {
    return running ? 'text-stock-down' : 'text-slate-500';
  };

  const getStatusDot = (running: boolean) => {
    return running ? (
      <span className="w-3 h-3 bg-stock-down rounded-full animate-pulse" />
    ) : (
      <span className="w-3 h-3 bg-slate-500 rounded-full" />
    );
  };

  const getTaskStatusBadge = (status: Task['status']) => {
    switch (status) {
      case 'running':
        return <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full">运行中</span>;
      case 'success':
        return <span className="px-2 py-0.5 bg-stock-down/20 text-stock-down text-xs rounded-full">成功</span>;
      case 'error':
        return <span className="px-2 py-0.5 bg-stock-up/20 text-stock-up text-xs rounded-full">失败</span>;
      default:
        return <span className="px-2 py-0.5 bg-slate-500/20 text-slate-400 text-xs rounded-full">空闲</span>;
    }
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start) return '';
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const seconds = Math.round((endTime.getTime() - startTime.getTime()) / 1000);
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`;
  };

  const formatTime = (timeStr?: string) => {
    if (!timeStr) return '';
    return new Date(timeStr).toLocaleTimeString();
  };

  const clearTasks = () => {
    const newTasks: Task[] = [];
    setTasks(newTasks);
    saveTasksToStorage(newTasks);
  };

  return (
    <div className="min-h-screen bg-dark-bg">
      <Head>
        <title>系统管理 - Crazy Money</title>
      </Head>
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">系统管理</h1>
          <p className="text-slate-400">一站式管理前后端服务和数据任务</p>
        </div>

        {/* 服务状态卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* 后端服务 */}
          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">后端服务</h3>
                  <div className={`flex items-center gap-2 text-sm ${getStatusColor(systemStatus?.backend.running || false)}`}>
                    {getStatusDot(systemStatus?.backend.running || false)}
                    <span>{systemStatus?.backend.running ? '运行中' : '已停止'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 text-sm text-slate-400 mb-4">
              <div className="flex justify-between">
                <span>PID</span>
                <span className="font-mono">{systemStatus?.backend.pid === 'external' ? '外部启动' : (systemStatus?.backend.pid || '-')}</span>
              </div>
              <div className="flex justify-between">
                <span>端口</span>
                <span className="font-mono">{systemStatus?.backend.port || 8000}</span>
              </div>
              <div className="flex justify-between">
                <span>运行时长</span>
                <span>{systemStatus?.backend.pid === 'external' ? '无法获取' : formatUptime(systemStatus?.backend.uptime)}</span>
              </div>
              <div className="flex justify-between">
                <span>启动方式</span>
                <span>{systemStatus?.backend.pid === 'external' ? '外部' : '系统管理'}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleServiceAction('start', 'backend')}
                disabled={systemStatus?.backend.running || loading}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  systemStatus?.backend.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-stock-down/20 text-stock-down hover:bg-stock-down/30'
                }`}
              >
                启动
              </button>
              <button
                onClick={() => handleServiceAction('stop', 'backend')}
                disabled={!systemStatus?.backend.running || loading}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  !systemStatus?.backend.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-stock-up/20 text-stock-up hover:bg-stock-up/30'
                }`}
              >
                停止
              </button>
              <button
                onClick={() => handleServiceAction('restart', 'backend')}
                disabled={!systemStatus?.backend.running || loading}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  !systemStatus?.backend.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30'
                }`}
              >
                重启
              </button>
            </div>
          </div>

          {/* 前端服务 */}
          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">前端服务</h3>
                  <div className={`flex items-center gap-2 text-sm ${getStatusColor(systemStatus?.frontend.running || false)}`}>
                    {getStatusDot(systemStatus?.frontend.running || false)}
                    <span>{systemStatus?.frontend.running ? '运行中' : '已停止'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 text-sm text-slate-400 mb-4">
              <div className="flex justify-between">
                <span>PID</span>
                <span className="font-mono">{systemStatus?.frontend.pid === 'external' ? '外部启动' : (systemStatus?.frontend.pid || '-')}</span>
              </div>
              <div className="flex justify-between">
                <span>端口</span>
                <span className="font-mono">{systemStatus?.frontend.port || 3000}</span>
              </div>
              <div className="flex justify-between">
                <span>运行时长</span>
                <span>{systemStatus?.frontend.pid === 'external' ? '无法获取' : formatUptime(systemStatus?.frontend.uptime)}</span>
              </div>
              <div className="flex justify-between">
                <span>启动方式</span>
                <span>{systemStatus?.frontend.pid === 'external' ? '外部' : '系统管理'}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleServiceAction('start', 'frontend')}
                disabled={systemStatus?.frontend.running || loading}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  systemStatus?.frontend.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-stock-down/20 text-stock-down hover:bg-stock-down/30'
                }`}
              >
                启动
              </button>
              <button
                onClick={() => handleServiceAction('stop', 'frontend')}
                disabled={!systemStatus?.frontend.running || loading}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  !systemStatus?.frontend.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-stock-up/20 text-stock-up hover:bg-stock-up/30'
                }`}
              >
                停止
              </button>
              <button
                onClick={() => handleServiceAction('restart', 'frontend')}
                disabled={!systemStatus?.frontend.running || loading}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  !systemStatus?.frontend.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30'
                }`}
              >
                重启
              </button>
            </div>
          </div>

          {/* 调度器 */}
          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">数据调度器</h3>
                  <div className={`flex items-center gap-2 text-sm ${getStatusColor(systemStatus?.scheduler.running || false)}`}>
                    {getStatusDot(systemStatus?.scheduler.running || false)}
                    <span>{systemStatus?.scheduler.running ? '运行中' : '已停止'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 text-sm text-slate-400 mb-4">
              <div className="flex justify-between">
                <span>PID</span>
                <span className="font-mono">{systemStatus?.scheduler.pid || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span>运行时长</span>
                <span>{formatUptime(systemStatus?.scheduler.uptime)}</span>
              </div>
              <div className="flex justify-between">
                <span>功能</span>
                <span className="text-xs">每日自动更新</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleServiceAction('start', 'scheduler')}
                disabled={systemStatus?.scheduler.running || loading}
                className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  systemStatus?.scheduler.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-stock-down/20 text-stock-down hover:bg-stock-down/30'
                }`}
              >
                启动
              </button>
              <button
                onClick={() => handleServiceAction('stop', 'scheduler')}
                disabled={!systemStatus?.scheduler.running || loading}
                className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  !systemStatus?.scheduler.running
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-stock-up/20 text-stock-up hover:bg-stock-up/30'
                }`}
              >
                停止
              </button>
            </div>
          </div>
        </div>

        {/* 快速操作 */}
        <div className="bg-dark-card border border-dark-border rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">快速操作</h2>
          <p className="text-slate-400 text-sm mb-4">
            一键执行数据管理任务。执行时间取决于数据量大小，请耐心等待。
          </p>
          {hasRunningTask() && (
            <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-blue-400 text-sm">
              <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              有任务正在运行，请等待完成后再执行新任务
            </div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => runTask('init', '初始化股票列表', 'init')}
              disabled={hasRunningTask()}
              className="px-4 py-3 bg-gradient-to-r from-blue-500/20 to-blue-600/20 hover:from-blue-500/30 hover:to-blue-600/30 border border-blue-500/30 rounded-lg text-blue-400 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
              初始化列表
            </button>
            <button
              onClick={() => runTask('download', '下载股票数据', 'download')}
              disabled={hasRunningTask()}
              className="px-4 py-3 bg-gradient-to-r from-green-500/20 to-green-600/20 hover:from-green-500/30 hover:to-green-600/30 border border-green-500/30 rounded-lg text-green-400 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              下载数据
            </button>
            <button
              onClick={() => runTask('check', '检查数据完整性', 'check')}
              disabled={hasRunningTask()}
              className="px-4 py-3 bg-gradient-to-r from-purple-500/20 to-purple-600/20 hover:from-purple-500/30 hover:to-purple-600/30 border border-purple-500/30 rounded-lg text-purple-400 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              检查完整性
            </button>
            <button
              onClick={() => runTask('download-force', '强制全量下载', 'download', { force: true })}
              disabled={hasRunningTask()}
              className="px-4 py-3 bg-gradient-to-r from-orange-500/20 to-orange-600/20 hover:from-orange-500/30 hover:to-orange-600/30 border border-orange-500/30 rounded-lg text-orange-400 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
              </svg>
              全量下载
            </button>
          </div>
        </div>

        {/* 任务历史 */}
        <div className="bg-dark-card border border-dark-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">执行日志</h2>
            {tasks.length > 0 && (
              <button
                onClick={clearTasks}
                className="text-sm text-slate-400 hover:text-white transition-colors"
              >
                清空日志
              </button>
            )}
          </div>

          {tasks.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>暂无执行记录</p>
              <p className="text-sm mt-1">点击上方按钮开始执行任务</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {tasks.map(task => (
                <div
                  key={task.id}
                  className={`border rounded-lg p-4 transition-colors ${
                    task.status === 'running'
                      ? 'border-blue-500/50 bg-blue-500/5'
                      : 'border-dark-border bg-dark-bg/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-white">{task.name}</span>
                      {getTaskStatusBadge(task.status)}
                    </div>
                    <div className="text-xs text-slate-500">
                      {task.startTime && (
                        <span>
                          {formatTime(task.startTime)}
                          {task.endTime && ` (${formatDuration(task.startTime, task.endTime)})`}
                        </span>
                      )}
                    </div>
                  </div>

                  {task.status === 'running' && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-slate-400 mb-1">
                        <span>{task.progress.toFixed(1)}%</span>
                        {task.stats && (
                          <span>
                            成功: {task.stats.success} | 失败: {task.stats.failed} | 跳过: {task.stats.skipped}
                          </span>
                        )}
                      </div>
                      <div className="w-full bg-dark-bg rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap break-all bg-dark-bg rounded p-3 max-h-40 overflow-y-auto">
                    {task.output}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 导航链接 */}
        <div className="mt-8 pt-6 border-t border-dark-border">
          <Link href="/" className="text-blue-400 hover:text-blue-300 transition-colors text-sm">
            ← 返回首页
          </Link>
        </div>
      </main>
    </div>
  );
};

export default AdminPage;
