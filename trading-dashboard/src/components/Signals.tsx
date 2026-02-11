import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Filter, 
  Search, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronDown,
  Loader2,
  RefreshCw
} from 'lucide-react'
import { getSignals, runAnalysis } from '../api/client'

interface SignalsProps {
  onStockSelect: (code: string) => void
}

interface Signal {
  stock_code: string
  stock_name: string
  signal_type: string
  current_price: number
  ma30_week: number
  volume_ratio: number
  phase: string
  reason: string
  stop_loss: number
  position_size: number
  timestamp: string
}

const signalFilters = [
  { value: 'all', label: '全部信号' },
  { value: 'BUY', label: '买入信号' },
  { value: 'SELL', label: '卖出信号' },
  { value: 'HOLD', label: '持有' },
  { value: 'ADD_POSITION', label: '加仓' },
  { value: 'WATCH', label: '观察' },
]

const phaseFilters = [
  { value: 'all', label: '全部阶段' },
  { value: 'PHASE_1_BOTTOM', label: '第一阶段（底部）' },
  { value: 'PHASE_2_RISING', label: '第二阶段（上升）' },
  { value: 'PHASE_3_TOP', label: '第三阶段（顶部）' },
  { value: 'PHASE_4_FALLING', label: '第四阶段（下降）' },
]

const phaseNames: Record<string, string> = {
  'PHASE_1_BOTTOM': '第一阶段（底部）',
  'PHASE_2_RISING': '第二阶段（上升）',
  'PHASE_3_TOP': '第三阶段（顶部）',
  'PHASE_4_FALLING': '第四阶段（下降）',
}

export default function Signals({ onStockSelect }: SignalsProps) {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [signalFilter, setSignalFilter] = useState('all')
  const [phaseFilter, setPhaseFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null)

  const fetchSignals = async () => {
    try {
      setLoading(true)
      const data = await getSignals()
      if (data && Array.isArray(data)) {
        setSignals(data)
      }
    } catch (error) {
      console.error('获取信号失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      await runAnalysis()
      await fetchSignals()
    } catch (error) {
      console.error('刷新失败:', error)
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchSignals()
  }, [])

  const filteredSignals = signals.filter(signal => {
    const matchesSignal = signalFilter === 'all' || signal.signal_type === signalFilter
    const matchesPhase = phaseFilter === 'all' || signal.phase === phaseFilter
    const matchesSearch = signal.stock_code?.includes(searchQuery) || 
                         signal.stock_name?.includes(searchQuery)
    return matchesSignal && matchesPhase && matchesSearch
  })

  const getSignalBadge = (signalType: string) => {
    const configs: Record<string, { bg: string; text: string; label: string; icon: any }> = {
      BUY: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: '买入', icon: TrendingUp },
      SELL: { bg: 'bg-red-500/20', text: 'text-red-400', label: '卖出', icon: TrendingDown },
      HOLD: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: '持有', icon: CheckCircle },
      ADD_POSITION: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '加仓', icon: TrendingUp },
      WATCH: { bg: 'bg-gray-500/20', text: 'text-gray-400', label: '观察', icon: Clock },
    }
    return configs[signalType] || configs.WATCH
  }

  const getPhaseColor = (phase: string) => {
    const colors: Record<string, string> = {
      PHASE_1_BOTTOM: 'text-gray-400',
      PHASE_2_RISING: 'text-emerald-400',
      PHASE_3_TOP: 'text-amber-400',
      PHASE_4_FALLING: 'text-red-400',
    }
    return colors[phase] || 'text-gray-400'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center justify-between gap-4"
      >
        <div>
          <h2 className="text-2xl font-bold text-white">交易信号</h2>
          <p className="text-gray-400 mt-1">基于30周均线阶段分析法生成的交易建议</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">刷新</span>
          </button>
          <span className="text-sm text-gray-400">共 {filteredSignals.length} 个信号</span>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-4"
      >
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索股票代码或名称..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          {/* Signal Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={signalFilter}
              onChange={(e) => setSignalFilter(e.target.value)}
              className="pl-10 pr-8 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors appearance-none cursor-pointer"
            >
              {signalFilters.map(filter => (
                <option key={filter.value} value={filter.value}>{filter.label}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Phase Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={phaseFilter}
              onChange={(e) => setPhaseFilter(e.target.value)}
              className="pl-10 pr-8 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors appearance-none cursor-pointer"
            >
              {phaseFilters.map(filter => (
                <option key={filter.value} value={filter.value}>{filter.label}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </motion.div>

      {/* Signals List */}
      <div className="space-y-4">
        {filteredSignals.map((signal, index) => {
          const signalConfig = getSignalBadge(signal.signal_type)
          const SignalIcon = signalConfig.icon
          const isExpanded = expandedSignal === signal.stock_code

          return (
            <motion.div
              key={signal.stock_code}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.05 }}
              className={`glass-card overflow-hidden transition-all duration-300 ${
                isExpanded ? 'border-primary/30' : ''
              }`}
            >
              {/* Main Row */}
              <div
                className="p-6 cursor-pointer hover:bg-white/5 transition-colors"
                onClick={() => setExpandedSignal(isExpanded ? null : signal.stock_code)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6">
                    {/* Signal Badge */}
                    <div className={`w-12 h-12 ${signalConfig.bg} rounded-xl flex items-center justify-center`}>
                      <SignalIcon className={`w-6 h-6 ${signalConfig.text}`} />
                    </div>

                    {/* Stock Info */}
                    <div>
                      <h3 className="text-white font-semibold text-lg">{signal.stock_name || signal.stock_code}</h3>
                      <p className="text-gray-500 text-sm">{signal.stock_code}</p>
                    </div>

                    {/* Signal Type */}
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${signalConfig.bg} ${signalConfig.text}`}>
                      {signalConfig.label}信号
                    </span>

                    {/* Phase */}
                    <span className={`text-sm ${getPhaseColor(signal.phase)}`}>
                      {phaseNames[signal.phase] || signal.phase}
                    </span>
                  </div>

                  <div className="flex items-center gap-8">
                    {/* Price Info */}
                    <div className="text-right">
                      <p className="text-white font-semibold text-lg">¥{signal.current_price?.toFixed(2) || '--'}</p>
                      <p className="text-gray-400 text-sm">30周均线: ¥{signal.ma30_week?.toFixed(2) || '--'}</p>
                    </div>

                    {/* Expand Icon */}
                    <motion.div
                      animate={{ rotate: isExpanded ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    </motion.div>
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              <motion.div
                initial={false}
                animate={{ height: isExpanded ? 'auto' : 0, opacity: isExpanded ? 1 : 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="px-6 pb-6 border-t border-white/10">
                  <div className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Analysis */}
                    <div className="md:col-span-2 space-y-4">
                      <div>
                        <h4 className="text-white font-medium mb-2 flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-primary" />
                          信号分析
                        </h4>
                        <p className="text-gray-400 text-sm leading-relaxed">{signal.reason || '暂无分析'}</p>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div className="glass p-3 rounded-lg">
                          <p className="text-gray-500 text-xs mb-1">30周均线</p>
                          <p className="text-white font-semibold">¥{signal.ma30_week?.toFixed(2) || '--'}</p>
                        </div>
                        <div className="glass p-3 rounded-lg">
                          <p className="text-gray-500 text-xs mb-1">成交量比</p>
                          <p className={`font-semibold ${(signal.volume_ratio || 0) >= 2 ? 'text-emerald-400' : 'text-white'}`}>
                            {(signal.volume_ratio || 0).toFixed(2)}x
                          </p>
                        </div>
                        <div className="glass p-3 rounded-lg">
                          <p className="text-gray-500 text-xs mb-1">生成时间</p>
                          <p className="text-white text-sm">{signal.timestamp ? new Date(signal.timestamp).toLocaleString('zh-CN') : '--'}</p>
                        </div>
                      </div>
                    </div>

                    {/* Risk Management */}
                    <div className="space-y-4">
                      <h4 className="text-white font-medium">风险管理</h4>
                      
                      {signal.stop_loss && (
                        <div className="glass p-3 rounded-lg">
                          <p className="text-gray-500 text-xs mb-1">建议止损价</p>
                          <p className="text-red-400 font-semibold">¥{signal.stop_loss.toFixed(2)}</p>
                        </div>
                      )}
                      
                      {signal.position_size && (
                        <div className="glass p-3 rounded-lg">
                          <p className="text-gray-500 text-xs mb-1">建议仓位</p>
                          <p className="text-emerald-400 font-semibold">{signal.position_size}股</p>
                          <p className="text-gray-500 text-xs mt-1">
                            约 ¥{(signal.position_size * signal.current_price / 10000).toFixed(1)}万
                          </p>
                        </div>
                      )}

                      <div className="flex gap-2">
                        <button
                          onClick={() => onStockSelect(signal.stock_code)}
                          className="flex-1 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors text-sm font-medium"
                        >
                          查看详情
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )
        })}
      </div>

      {filteredSignals.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <div className="w-16 h-16 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Filter className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-white font-semibold mb-2">暂无符合条件的信号</h3>
          <p className="text-gray-400 text-sm mb-4">请调整筛选条件或运行分析</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            运行分析
          </button>
        </motion.div>
      )}
    </div>
  )
}
