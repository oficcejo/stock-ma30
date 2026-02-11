import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Scan, 
  Filter, 
  TrendingUp, 
  RefreshCw, 
  CheckCircle2,
  XCircle,
  BarChart3,
  Target,
  History,
  Calendar,
  Clock,
  Database,
  Activity
} from 'lucide-react'
import { 
  scanMarket, 
  getMarketStatistics, 
  getScanHistory, 
  getLatestScanResults,
  getPersistentPhase2Stocks 
} from '../api/client'

interface Phase2Stock {
  code: string
  name: string
  current_price: number
  ma30: number
  trend_strength: number
  volume_ratio: number
  weeks_in_phase2: number
  breakout_confirmed: boolean
}

interface MarketStats {
  total_stocks: number
  valid_stocks: number
  phase1_count: number
  phase2_count: number
  phase3_count: number
  phase4_count: number
}

interface ScanRecord {
  id: number
  scan_date: string
  scan_batch_id: string
  stock_code: string
  stock_name: string
  phase: string
  current_price: number
  ma30: number
  trend_strength: number
  volume_ratio: number
  weeks_in_phase2: number
  breakout_confirmed: boolean
  created_at: string
}

interface PersistentStock {
  stock_code: string
  stock_name: string
  appearance_count: number
  avg_price: number
  avg_strength: number
}

export default function MarketScan() {
  const [stocks, setStocks] = useState<Phase2Stock[]>([])
  const [loading, setLoading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [stats, setStats] = useState<MarketStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'scan' | 'history' | 'persistent'>('scan')
  
  // 历史记录
  const [historyRecords, setHistoryRecords] = useState<ScanRecord[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyDateFilter, setHistoryDateFilter] = useState<'7' | '30' | '90' | 'all'>('7')
  
  // 持续强势股
  const [persistentStocks, setPersistentStocks] = useState<PersistentStock[]>([])
  const [persistentLoading, setPersistentLoading] = useState(false)
  const [minDays, setMinDays] = useState(3)
  
  // 筛选配置
  const [filters, setFilters] = useState({
    excludeST: true,
    excludeGEM: true,
    excludeSTAR: true,
    maxStocks: 0  // 0表示不限制
  })

  // 获取市场统计
  const fetchStatistics = async () => {
    try {
      const response = await getMarketStatistics()
      if (response.success) {
        setStats(response.data)
      }
    } catch (err: any) {
      console.error('获取统计失败:', err)
    }
  }

  // 获取历史记录
  const fetchHistory = async () => {
    try {
      setHistoryLoading(true)
      let startDate: string | undefined
      const endDate = new Date().toISOString().split('T')[0]
      
      if (historyDateFilter !== 'all') {
        const days = parseInt(historyDateFilter)
        const date = new Date()
        date.setDate(date.getDate() - days)
        startDate = date.toISOString().split('T')[0]
      }
      
      const response = await getScanHistory(startDate, endDate, 200)
      if (response.success) {
        setHistoryRecords(response.records)
      }
    } catch (err: any) {
      console.error('获取历史记录失败:', err)
    } finally {
      setHistoryLoading(false)
    }
  }

  // 获取持续强势股
  const fetchPersistentStocks = async () => {
    try {
      setPersistentLoading(true)
      const response = await getPersistentPhase2Stocks(minDays)
      if (response.success) {
        setPersistentStocks(response.stocks)
      }
    } catch (err: any) {
      console.error('获取持续强势股失败:', err)
    } finally {
      setPersistentLoading(false)
    }
  }

  // 获取最新扫描结果
  const fetchLatestResults = async () => {
    try {
      setLoading(true)
      const response = await getLatestScanResults()
      if (response.success && response.stocks.length > 0) {
        const formatted = response.stocks.map((r: ScanRecord) => ({
          code: r.stock_code,
          name: r.stock_name,
          current_price: r.current_price,
          ma30: r.ma30,
          trend_strength: r.trend_strength,
          volume_ratio: r.volume_ratio,
          weeks_in_phase2: r.weeks_in_phase2,
          breakout_confirmed: r.breakout_confirmed
        }))
        setStocks(formatted)
      }
    } catch (err: any) {
      console.error('获取最新结果失败:', err)
    } finally {
      setLoading(false)
    }
  }

  // 扫描生成的信号
  const [generatedSignals, setGeneratedSignals] = useState<any[]>([])
  const [signalCount, setSignalCount] = useState(0)

  // 执行扫描
  const handleScan = async () => {
    try {
      setScanning(true)
      setError(null)
      setGeneratedSignals([])
      setSignalCount(0)
      console.log('开始全市场扫描...')
      
      const response = await scanMarket(
        filters.maxStocks,
        filters.excludeST,
        filters.excludeGEM,
        filters.excludeSTAR,
        true // 生成信号
      )
      
      if (response.success) {
        setStocks(response.stocks)
        setSignalCount(response.signal_count || 0)
        setGeneratedSignals(response.signals || [])
        console.log(`扫描完成，找到 ${response.count} 只第二阶段股票，生成 ${response.signal_count} 个交易信号`)
        
        // 显示提示
        if (response.signal_count > 0) {
          alert(`扫描完成！\n发现 ${response.count} 只第二阶段股票\n已生成 ${response.signal_count} 个交易信号并加入监测\n\n请前往"交易信号"页面查看详情。`)
        }
      }
    } catch (err: any) {
      console.error('扫描失败:', err)
      setError(err.message || '扫描失败')
      alert('扫描失败: ' + (err.message || '未知错误'))
    } finally {
      setScanning(false)
    }
  }

  useEffect(() => {
    fetchStatistics()
    fetchLatestResults() // 加载最新扫描结果
  }, [])

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory()
    } else if (activeTab === 'persistent') {
      fetchPersistentStocks()
    }
  }, [activeTab, historyDateFilter, minDays])

  return (
    <div className="space-y-6">
      {/* 标题和控制面板 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Scan className="w-6 h-6 text-primary" />
              全市场扫描
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              扫描全市场A股，筛选出处于第二阶段（上升趋势）的优质股票
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* 标签切换 */}
            <div className="flex bg-white/5 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('scan')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'scan' 
                    ? 'bg-primary text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Scan className="w-4 h-4 inline mr-1" />
                实时扫描
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'history' 
                    ? 'bg-primary text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <History className="w-4 h-4 inline mr-1" />
                历史记录
              </button>
              <button
                onClick={() => setActiveTab('persistent')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'persistent' 
                    ? 'bg-primary text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <TrendingUp className="w-4 h-4 inline mr-1" />
                持续强势
              </button>
            </div>
            
            {activeTab === 'scan' && (
              <button
                onClick={handleScan}
                disabled={scanning}
                className="flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 font-medium"
              >
                {scanning ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <Scan className="w-5 h-5" />
                )}
                {scanning ? '扫描中...' : '开始扫描'}
              </button>
            )}
          </div>
        </div>

        {/* 筛选选项 - 只在实时扫描标签显示 */}
        {activeTab === 'scan' && (
          <div className="mt-6 pt-6 border-t border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">筛选条件</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <label className="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.excludeST}
                  onChange={(e) => setFilters({...filters, excludeST: e.target.checked})}
                  className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
                />
                <span className="text-sm text-gray-300">排除ST股票</span>
              </label>
              
              <label className="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.excludeGEM}
                  onChange={(e) => setFilters({...filters, excludeGEM: e.target.checked})}
                  className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
                />
                <span className="text-sm text-gray-300">排除创业板</span>
              </label>
              
              <label className="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.excludeSTAR}
                  onChange={(e) => setFilters({...filters, excludeSTAR: e.target.checked})}
                  className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
                />
                <span className="text-sm text-gray-300">排除科创板</span>
              </label>
              
            <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
              <span className="text-sm text-gray-300">最大数量:</span>
              <select
                value={filters.maxStocks}
                onChange={(e) => setFilters({...filters, maxStocks: parseInt(e.target.value)})}
                className="bg-transparent text-white text-sm border border-white/20 rounded px-2 py-1 focus:outline-none focus:border-primary"
              >
                <option value="0">不限制</option>
                <option value="20">20只</option>
                <option value="50">50只</option>
                <option value="100">100只</option>
                <option value="200">200只</option>
              </select>
            </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* 市场统计 */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
        >
          <div className="glass-card p-4 text-center">
            <p className="text-gray-400 text-xs">全市场</p>
            <p className="text-2xl font-bold text-white">{stats.total_stocks.toLocaleString()}</p>
            <p className="text-gray-500 text-xs">只股票</p>
          </div>
          
          <div className="glass-card p-4 text-center">
            <p className="text-gray-400 text-xs">有效标的</p>
            <p className="text-2xl font-bold text-emerald-400">{stats.valid_stocks.toLocaleString()}</p>
            <p className="text-gray-500 text-xs">只</p>
          </div>
          
          <div className="glass-card p-4 text-center">
            <p className="text-gray-400 text-xs">第一阶段</p>
            <p className="text-2xl font-bold text-gray-400">~{stats.phase1_count.toLocaleString()}</p>
            <p className="text-gray-500 text-xs">底部横盘</p>
          </div>
          
          <div className="glass-card p-4 text-center border-2 border-emerald-500/30">
            <p className="text-emerald-400 text-xs font-medium">第二阶段</p>
            <p className="text-2xl font-bold text-emerald-400">~{stats.phase2_count.toLocaleString()}</p>
            <p className="text-emerald-500/70 text-xs">上升趋势 ⭐</p>
          </div>
          
          <div className="glass-card p-4 text-center">
            <p className="text-gray-400 text-xs">第三阶段</p>
            <p className="text-2xl font-bold text-amber-400">~{stats.phase3_count.toLocaleString()}</p>
            <p className="text-gray-500 text-xs">顶部横盘</p>
          </div>
          
          <div className="glass-card p-4 text-center">
            <p className="text-gray-400 text-xs">第四阶段</p>
            <p className="text-2xl font-bold text-red-400">~{stats.phase4_count.toLocaleString()}</p>
            <p className="text-gray-500 text-xs">下降趋势</p>
          </div>
        </motion.div>
      )}

      {/* 扫描结果 - 只在实时扫描标签显示 */}
      {activeTab === 'scan' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Target className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-lg font-semibold text-white">
                  第二阶段股票
                  {stocks.length > 0 && (
                    <span className="ml-2 text-sm text-gray-400">({stocks.length}只)</span>
                  )}
                </h3>
                {signalCount > 0 && (
                  <p className="text-sm text-emerald-400 mt-1">
                    ✓ 已生成 {signalCount} 个交易信号并加入监测
                  </p>
                )}
              </div>
            </div>
            
            {stocks.length > 0 && (
              <div className="flex items-center gap-3">
                {signalCount > 0 && (
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      window.location.href = '/?tab=signals';
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors text-sm"
                  >
                    <Activity className="w-4 h-4" />
                    查看交易信号
                  </a>
                )}
                <button
                  onClick={() => {
                    setStocks([]);
                    setGeneratedSignals([]);
                    setSignalCount(0);
                  }}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  清空结果
                </button>
              </div>
            )}
          </div>

          {scanning ? (
            <div className="text-center py-12">
              <RefreshCw className="w-10 h-10 animate-spin mx-auto mb-4 text-primary" />
              <p className="text-gray-400">正在扫描全市场股票...</p>
              <p className="text-gray-500 text-sm mt-2">预计需要1-3分钟</p>
            </div>
          ) : stocks.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>点击"开始扫描"查找第二阶段股票</p>
              <p className="text-sm text-gray-500 mt-2">
                系统会排除ST、创业板、科创板等股票
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-white/10">
                    <th className="pb-4 text-gray-400 font-medium text-sm">股票代码</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">股票名称</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">当前价格</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">30周均线</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">趋势强度</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">进入阶段</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">突破确认</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {stocks.map((stock, index) => (
                    <motion.tr
                      key={stock.code}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="hover:bg-white/5 transition-colors"
                    >
                      <td className="py-4 font-mono text-white">{stock.code}</td>
                      <td className="py-4 text-white">{stock.name || '--'}</td>
                      <td className="py-4 text-emerald-400 font-medium">
                        ¥{stock.current_price?.toFixed(2)}
                      </td>
                      <td className="py-4 text-gray-400">
                        ¥{stock.ma30?.toFixed(2)}
                      </td>
                      <td className="py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500"
                              style={{ width: `${Math.min(stock.trend_strength * 1000, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400">
                            {(stock.trend_strength * 100).toFixed(2)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-4 text-gray-400">
                        {stock.weeks_in_phase2}周
                      </td>
                      <td className="py-4">
                        {stock.breakout_confirmed ? (
                          <span className="flex items-center gap-1 text-emerald-400 text-sm">
                            <CheckCircle2 className="w-4 h-4" />
                            已确认
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-amber-400 text-sm">
                            <XCircle className="w-4 h-4" />
                            观察中
                          </span>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      )}

      {/* 历史记录 - 只在历史标签显示 */}
      {activeTab === 'history' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <History className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-semibold text-white">扫描历史记录</h3>
            </div>
            
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              <select
                value={historyDateFilter}
                onChange={(e) => setHistoryDateFilter(e.target.value as '7' | '30' | '90' | 'all')}
                className="bg-white/5 text-white text-sm border border-white/20 rounded-lg px-3 py-2 focus:outline-none focus:border-primary"
              >
                <option value="7">近7天</option>
                <option value="30">近30天</option>
                <option value="90">近90天</option>
                <option value="all">全部</option>
              </select>
            </div>
          </div>

          {historyLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-10 h-10 animate-spin mx-auto mb-4 text-primary" />
              <p className="text-gray-400">加载历史记录...</p>
            </div>
          ) : historyRecords.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>暂无历史记录</p>
              <p className="text-sm text-gray-500 mt-2">扫描结果会自动保存到数据库</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-white/10">
                    <th className="pb-4 text-gray-400 font-medium text-sm">扫描日期</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">股票代码</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">股票名称</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">价格</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">30周均线</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">趋势强度</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">持续周数</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {historyRecords.map((record) => (
                    <tr key={record.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-4 text-gray-400 text-sm">
                        {record.scan_date}
                      </td>
                      <td className="py-4 font-mono text-white">{record.stock_code}</td>
                      <td className="py-4 text-white">{record.stock_name || '--'}</td>
                      <td className="py-4 text-emerald-400">
                        ¥{record.current_price?.toFixed(2)}
                      </td>
                      <td className="py-4 text-gray-400">
                        ¥{record.ma30?.toFixed(2)}
                      </td>
                      <td className="py-4">
                        <span className={`text-xs ${
                          record.trend_strength > 0.02 ? 'text-emerald-400' : 'text-gray-400'
                        }`}>
                          {(record.trend_strength * 100).toFixed(2)}%
                        </span>
                      </td>
                      <td className="py-4 text-gray-400">
                        {record.weeks_in_phase2}周
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      )}

      {/* 持续强势股 - 只在持续强势标签显示 */}
      {activeTab === 'persistent' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                <h3 className="text-lg font-semibold text-white">持续强势股</h3>
              </div>
              <p className="text-gray-400 text-sm mt-1">
                多日持续出现在第二阶段的股票（复盘模式）
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">最少出现:</span>
              <select
                value={minDays}
                onChange={(e) => setMinDays(parseInt(e.target.value))}
                className="bg-white/5 text-white text-sm border border-white/20 rounded-lg px-3 py-2 focus:outline-none focus:border-primary"
              >
                <option value={2}>2天</option>
                <option value={3}>3天</option>
                <option value={5}>5天</option>
                <option value={7}>7天</option>
                <option value={10}>10天</option>
              </select>
            </div>
          </div>

          {persistentLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-10 h-10 animate-spin mx-auto mb-4 text-primary" />
              <p className="text-gray-400">分析持续强势股...</p>
            </div>
          ) : persistentStocks.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>暂无持续强势股</p>
              <p className="text-sm text-gray-500 mt-2">
                在选定期间内连续{minDays}天以上出现在第二阶段
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-white/10">
                    <th className="pb-4 text-gray-400 font-medium text-sm">股票代码</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">股票名称</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">出现天数</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">平均价格</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">平均趋势强度</th>
                    <th className="pb-4 text-gray-400 font-medium text-sm">持续性评级</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {persistentStocks.map((stock) => (
                    <tr key={stock.stock_code} className="hover:bg-white/5 transition-colors">
                      <td className="py-4 font-mono text-white">{stock.stock_code}</td>
                      <td className="py-4 text-white font-medium">{stock.stock_name}</td>
                      <td className="py-4">
                        <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-sm">
                          {stock.appearance_count}天
                        </span>
                      </td>
                      <td className="py-4 text-emerald-400">
                        ¥{stock.avg_price?.toFixed(2)}
                      </td>
                      <td className="py-4 text-gray-400">
                        {(stock.avg_strength * 100).toFixed(2)}%
                      </td>
                      <td className="py-4">
                        {stock.appearance_count >= 7 ? (
                          <span className="flex items-center gap-1 text-emerald-400 text-sm">
                            <CheckCircle2 className="w-4 h-4" />
                            极强
                          </span>
                        ) : stock.appearance_count >= 5 ? (
                          <span className="flex items-center gap-1 text-emerald-400 text-sm">
                            <TrendingUp className="w-4 h-4" />
                            强势
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-amber-400 text-sm">
                            <Target className="w-4 h-4" />
                            一般
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      )}

      {/* 说明 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-6 border-l-4 border-emerald-500"
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h4 className="text-white font-semibold mb-2">第二阶段选股标准</h4>
            <ul className="text-gray-400 text-sm space-y-1">
              <li>• 30周均线向上（上升趋势确认）</li>
              <li>• 股价运行在30周均线上方</li>
              <li>• 排除ST、创业板(300/301)、科创板(688)、北交所股票</li>
              <li>• 仅保留上海主板(60开头)和深圳主板(00开头)</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
