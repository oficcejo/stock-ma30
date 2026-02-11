import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  AlertCircle,
  Target,
  Shield,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  PlayCircle,
  BookOpen,
  ExternalLink,
  Search,
  PieChart,
  Zap,
  Scan
} from 'lucide-react'
import { getSignals, getMarketContext, runAnalysis, getStockAnalysis } from '../api/client'

interface DashboardProps {
  onStockSelect: (code: string) => void
  marketData: {
    indexPhase: string
    sentiment: string
    lastUpdate: string
  }
}

interface Signal {
  stock_code: string
  stock_name: string
  signal_type: string
  current_price: number
  phase: string
  timestamp: string
  reason?: string
}

// 系统特点说明
const systemFeatures = [
  { 
    icon: 'TrendingUp', 
    title: '四阶段理论', 
    desc: '基于史丹·温斯坦的四阶段分析法，精准识别股票所处阶段',
    color: 'emerald'
  },
  { 
    icon: 'Target', 
    title: '30周均线', 
    desc: '以30周移动平均线为核心指标，判断中长期趋势方向',
    color: 'blue'
  },
  { 
    icon: 'Shield', 
    title: '风险控制', 
    desc: '自动计算止损位，单笔亏损控制在2-3%以内',
    color: 'amber'
  },
  { 
    icon: 'Scan', 
    title: '全市场扫描', 
    desc: '自动扫描全市场A股，筛选出处于第二阶段的股票',
    color: 'cyan'
  },
]

export default function Dashboard({ onStockSelect, marketData }: DashboardProps) {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // 单股票分析状态
  const [stockCode, setStockCode] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  // 分析单只股票
  const handleAnalyzeStock = async () => {
    if (!stockCode.trim()) {
      alert('请输入股票代码')
      return
    }
    
    try {
      setAnalyzing(true)
      setAnalysisError(null)
      setAnalysisResult(null)
      
      const code = stockCode.trim()
      console.log('分析股票:', code)
      const result = await getStockAnalysis(code)
      
      if (result.success) {
        setAnalysisResult(result)
        console.log('分析结果:', result)
      } else {
        setAnalysisError('分析失败')
      }
    } catch (err: any) {
      console.error('分析股票失败:', err)
      setAnalysisError(err.message || '分析失败，请检查股票代码是否正确')
    } finally {
      setAnalyzing(false)
    }
  }

  // 获取真实数据
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('正在获取信号数据...')
      const data = await getSignals()
      console.log('获取到信号:', data)
      if (data && Array.isArray(data)) {
        setSignals(data.slice(0, 10)) // 只显示前10条
      } else {
        setSignals([])
      }
    } catch (err: any) {
      console.error('获取信号失败:', err)
      const msg = err.message || '获取信号失败'
      setError(msg)
      // 只在非自动刷新时显示alert
      if (!loading) {
        alert('错误: ' + msg)
      }
    } finally {
      setLoading(false)
    }
  }

  // 运行分析
  const [error, setError] = useState<string | null>(null)
  
  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      setError(null)
      console.log('开始运行分析...')
      const result = await runAnalysis()
      console.log('分析完成:', result)
      await fetchData()
    } catch (err: any) {
      console.error('运行分析失败:', err)
      const msg = err.message || '运行分析失败，请检查后端服务是否启动'
      setError(msg)
      alert('错误: ' + msg)
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
    // 每30秒自动刷新
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // 统计计算
  const buySignals = signals.filter(s => s.signal_type === 'BUY').length
  const sellSignals = signals.filter(s => s.signal_type === 'SELL').length
  const holdSignals = signals.filter(s => s.signal_type === 'HOLD').length

  const statsData = [
    { 
      label: '买入信号', 
      value: buySignals, 
      change: '+0', 
      trend: 'up', 
      icon: TrendingUp, 
      color: 'emerald' 
    },
    { 
      label: '卖出信号', 
      value: sellSignals, 
      change: '-0', 
      trend: 'down', 
      icon: TrendingDown, 
      color: 'red' 
    },
    { 
      label: '持仓股票', 
      value: holdSignals, 
      change: '+0', 
      trend: 'up', 
      icon: Target, 
      color: 'blue' 
    },
    { 
      label: '总信号数', 
      value: signals.length, 
      change: '+0', 
      trend: 'up', 
      icon: Shield, 
      color: 'amber' 
    },
  ]

  const getSignalBadge = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return { text: '买入', class: 'bg-emerald-500/20 text-emerald-400' }
      case 'SELL':
        return { text: '卖出', class: 'bg-red-500/20 text-red-400' }
      case 'HOLD':
        return { text: '持有', class: 'bg-blue-500/20 text-blue-400' }
      default:
        return { text: '观察', class: 'bg-gray-500/20 text-gray-400' }
    }
  }

  const getPhaseText = (phase: string) => {
    switch (phase) {
      case 'PHASE_1_BOTTOM':
        return { text: '底部', class: 'text-gray-400' }
      case 'PHASE_2_RISING':
        return { text: '上升', class: 'text-emerald-400' }
      case 'PHASE_3_TOP':
        return { text: '顶部', class: 'text-amber-400' }
      case 'PHASE_4_FALLING':
        return { text: '下降', class: 'text-red-400' }
      default:
        return { text: '未知', class: 'text-gray-400' }
    }
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsData.map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="glass-card p-6 hover:border-white/20 transition-all duration-300"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-gray-400 text-sm">{stat.label}</p>
                  <h3 className="text-3xl font-bold text-white mt-2">{stat.value}</h3>
                  <div className={`flex items-center gap-1 mt-2 text-sm ${
                    stat.trend === 'up' ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {stat.trend === 'up' ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                    <span>{stat.change}</span>
                  </div>
                </div>
                <div className={`w-12 h-12 rounded-xl bg-${stat.color}-500/20 flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-400`} />
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Stock Analysis Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-6 border-l-4 border-cyan-500"
      >
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
              <Search className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-white font-semibold">股票阶段分析</h3>
              <p className="text-gray-400 text-sm">输入股票代码查看所处阶段</p>
            </div>
          </div>
          
          <div className="flex-1 flex items-center gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyzeStock()}
                placeholder="输入股票代码，如：000001 或 600519"
                className="w-full pl-4 pr-4 py-3 bg-dark-lighter border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
              />
            </div>
            <button
              onClick={handleAnalyzeStock}
              disabled={analyzing}
              className="flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white rounded-xl hover:bg-cyan-600 transition-colors disabled:opacity-50 font-medium"
            >
              {analyzing ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Zap className="w-5 h-5" />
              )}
              {analyzing ? '分析中...' : '分析'}
            </button>
          </div>
        </div>

        {/* Analysis Result */}
        {analysisError && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
            <p className="text-red-400 text-sm">{analysisError}</p>
          </div>
        )}

        {analysisResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 pt-4 border-t border-white/10"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Stock Info */}
              <div className="p-4 bg-white/5 rounded-xl">
                <p className="text-gray-400 text-sm mb-1">股票信息</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-bold text-white">{analysisResult.stock_name}</span>
                  <span className="text-gray-400 font-mono">{analysisResult.stock_code}</span>
                </div>
              </div>

              {/* Phase */}
              <div className="p-4 bg-white/5 rounded-xl">
                <p className="text-gray-400 text-sm mb-1">当前阶段</p>
                <div className="flex items-center gap-2">
                  {analysisResult.phase === 'PHASE_1_BOTTOM' && (
                    <>
                      <PieChart className="w-5 h-5 text-gray-400" />
                      <span className="text-lg font-bold text-gray-400">第一阶段 - 底部横盘</span>
                    </>
                  )}
                  {analysisResult.phase === 'PHASE_2_RISING' && (
                    <>
                      <TrendingUp className="w-5 h-5 text-emerald-400" />
                      <span className="text-lg font-bold text-emerald-400">第二阶段 - 上升趋势</span>
                    </>
                  )}
                  {analysisResult.phase === 'PHASE_3_TOP' && (
                    <>
                      <Target className="w-5 h-5 text-amber-400" />
                      <span className="text-lg font-bold text-amber-400">第三阶段 - 顶部横盘</span>
                    </>
                  )}
                  {analysisResult.phase === 'PHASE_4_FALLING' && (
                    <>
                      <TrendingDown className="w-5 h-5 text-red-400" />
                      <span className="text-lg font-bold text-red-400">第四阶段 - 下降趋势</span>
                    </>
                  )}
                </div>
              </div>

              {/* Price & MA */}
              <div className="p-4 bg-white/5 rounded-xl">
                <p className="text-gray-400 text-sm mb-1">价格与均线</p>
                <div className="flex items-baseline gap-3">
                  <span className="text-xl font-bold text-emerald-400">¥{analysisResult.current_price?.toFixed(2)}</span>
                  <span className="text-gray-400">/</span>
                  <span className="text-gray-400">MA30: ¥{analysisResult.ma30_week?.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Signals */}
            {analysisResult.signals && analysisResult.signals.length > 0 && (
              <div className="mt-4">
                <h4 className="text-white font-medium mb-3">交易信号</h4>
                <div className="space-y-2">
                  {analysisResult.signals.map((signal: any, idx: number) => (
                    <div key={idx} className="p-3 bg-white/5 rounded-lg flex items-start gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        signal.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' :
                        signal.type === 'SELL' ? 'bg-red-500/20 text-red-400' :
                        signal.type === 'HOLD' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {signal.type === 'BUY' ? '买入' :
                         signal.type === 'SELL' ? '卖出' :
                         signal.type === 'HOLD' ? '持有' : '观察'}
                      </span>
                      <p className="text-gray-300 text-sm flex-1">{signal.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metrics */}
            {analysisResult.metrics && (
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 bg-white/5 rounded-lg text-center">
                  <p className="text-gray-400 text-xs">均线斜率</p>
                  <p className={`text-lg font-bold ${analysisResult.metrics.ma30_slope > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(analysisResult.metrics.ma30_slope * 100).toFixed(2)}%
                  </p>
                </div>
                <div className="p-3 bg-white/5 rounded-lg text-center">
                  <p className="text-gray-400 text-xs">均线方向</p>
                  <p className="text-white font-medium">
                    {analysisResult.metrics.ma30_direction === 'up' ? '向上 ↑' :
                     analysisResult.metrics.ma30_direction === 'down' ? '向下 ↓' : '走平 →'}
                  </p>
                </div>
                <div className="p-3 bg-white/5 rounded-lg text-center">
                  <p className="text-gray-400 text-xs">价格/均线比</p>
                  <p className="text-white font-bold">{analysisResult.metrics.price_to_ma_ratio?.toFixed(3)}</p>
                </div>
                <div className="p-3 bg-white/5 rounded-lg text-center">
                  <p className="text-gray-400 text-xs">突破确认</p>
                  <p className={`font-medium ${analysisResult.metrics.breakout_confirmed ? 'text-emerald-400' : 'text-gray-400'}`}>
                    {analysisResult.metrics.breakout_confirmed ? '已确认' : '未确认'}
                  </p>
                </div>
              </div>
            )}

            {/* View Detail Button */}
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => onStockSelect(analysisResult.stock_code)}
                className="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors text-sm"
              >
                查看详细分析 →
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* System Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-card p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-6">系统特点</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {systemFeatures.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors"
            >
              <div className={`w-10 h-10 rounded-lg bg-${feature.color}-500/20 flex items-center justify-center mb-3`}>
                {feature.icon === 'TrendingUp' && <TrendingUp className={`w-5 h-5 text-${feature.color}-400`} />}
                {feature.icon === 'Target' && <Target className={`w-5 h-5 text-${feature.color}-400`} />}
                {feature.icon === 'Shield' && <Shield className={`w-5 h-5 text-${feature.color}-400`} />}
                {feature.icon === 'Scan' && <Scan className={`w-5 h-5 text-${feature.color}-400`} />}
              </div>
              <h4 className="text-white font-medium mb-1">{feature.title}</h4>
              <p className="text-gray-400 text-sm">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recent Signals */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">最新交易信号</h3>
          <div className="flex items-center gap-4">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="text-sm">刷新</span>
            </button>
            <button className="text-primary text-sm hover:underline">查看全部</button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p>加载中...</p>
          </div>
        ) : signals.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>暂无交易信号</p>
            <button
              onClick={handleRefresh}
              className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
            >
              运行分析
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-white/10">
                  <th className="pb-4 text-gray-400 font-medium text-sm">股票</th>
                  <th className="pb-4 text-gray-400 font-medium text-sm">信号</th>
                  <th className="pb-4 text-gray-400 font-medium text-sm">当前价格</th>
                  <th className="pb-4 text-gray-400 font-medium text-sm">阶段</th>
                  <th className="pb-4 text-gray-400 font-medium text-sm">时间</th>
                  <th className="pb-4 text-gray-400 font-medium text-sm">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {signals.map((signal, index) => {
                  const badge = getSignalBadge(signal.signal_type)
                  const phase = getPhaseText(signal.phase)
                  return (
                    <motion.tr
                      key={signal.stock_code}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + index * 0.05 }}
                      className="hover:bg-white/5 transition-colors"
                    >
                      <td className="py-4">
                        <div>
                          <p className="text-white font-medium">{signal.stock_name || signal.stock_code}</p>
                          <p className="text-gray-500 text-sm">{signal.stock_code}</p>
                        </div>
                      </td>
                      <td className="py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.class}`}>
                          {badge.text}
                        </span>
                      </td>
                      <td className="py-4 text-white">¥{signal.current_price?.toFixed(2) || '--'}</td>
                      <td className="py-4">
                        <span className={`text-xs ${phase.class}`}>
                          {phase.text}
                        </span>
                      </td>
                      <td className="py-4 text-gray-400 text-sm">
                        {signal.timestamp ? new Date(signal.timestamp).toLocaleString('zh-CN') : '--'}
                      </td>
                      <td className="py-4">
                        <button
                          onClick={() => onStockSelect(signal.stock_code)}
                          className="text-primary text-sm hover:underline"
                        >
                          详情
                        </button>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Trading Rules Reminder */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="glass-card p-6 border-l-4 border-primary"
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center flex-shrink-0">
            <AlertCircle className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h4 className="text-white font-semibold mb-2">交易纪律提醒</h4>
            <p className="text-gray-400 text-sm leading-relaxed">
              根据史丹·温斯坦的交易原则：只在第二阶段（上升趋势）买入，单笔亏损不超过总资金的2-3%，
              止损位只能上移不能下移。当前大盘处于
              {marketData.indexPhase === 'PHASE_2_RISING' ? '上升趋势，适合积极操作' 
                : marketData.indexPhase === 'PHASE_4_FALLING' ? '下降趋势，建议减仓观望'
                : '震荡阶段，保持谨慎'}
              。
            </p>
          </div>
        </div>
      </motion.div>

      {/* Theory Source & Video */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="glass-card p-6 border-l-4 border-cyan-500"
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex-1">
            <h4 className="text-white font-semibold mb-2">理论来源</h4>
            <p className="text-gray-400 text-sm leading-relaxed mb-4">
              本系统基于史丹·温斯坦（Stan Weinstein）的经典著作《笑傲牛熊》（Secrets for Profiting in Bull and Bear Markets）
              中的"四阶段理论"和"30周均线交易系统"构建。
            </p>
            <a
              href="https://www.bilibili.com/video/BV1twFSzNE75"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition-colors"
            >
              <PlayCircle className="w-5 h-5" />
              <span className="font-medium">观看理论讲解视频</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
