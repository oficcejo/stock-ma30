import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  X, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  BarChart3,
  Target,
  AlertCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Loader2
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, AreaChart, Area, ReferenceLine } from 'recharts'
import { getStockAnalysis } from '../api/client'

interface StockDetailProps {
  stockCode: string
  onClose: () => void
}

interface StockData {
  stock_code: string
  stock_name: string
  current_price: number
  ma30_week: number
  phase: string
  signals: Array<{
    type: string
    current_price: number
    ma30_week: number
    volume_ratio: number
    reason: string
    stop_loss: number
    position_size: number
  }>
}

const analysisPointsTemplate = [
  { title: '趋势判断', content: '30周均线向上倾斜，股价站稳均线上方，处于健康的上升趋势中。', positive: true },
  { title: '成交量分析', content: '近期成交量明显放大，显示有资金介入。', positive: true },
  { title: '支撑阻力', content: '支撑位在前期低点附近，关注突破情况。', positive: true },
  { title: '风险提示', content: '需关注大盘整体走势，建议严格执行止损纪律。', positive: false },
]

export default function StockDetail({ stockCode, onClose }: StockDetailProps) {
  const [stockData, setStockData] = useState<StockData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStockData()
  }, [stockCode])

  const fetchStockData = async () => {
    try {
      setLoading(true)
      const data = await getStockAnalysis(stockCode)
      if (data && data.success) {
        setStockData(data)
      } else {
        setError('无法获取股票数据')
      }
    } catch (err) {
      setError('网络错误')
    } finally {
      setLoading(false)
    }
  }

  const getPhaseInfo = (phase: string) => {
    const phases: Record<string, { name: string; color: string }> = {
      'PHASE_1_BOTTOM': { name: '第一阶段（底部）', color: 'bg-gray-500/20 text-gray-400' },
      'PHASE_2_RISING': { name: '第二阶段（上升）', color: 'bg-emerald-500/20 text-emerald-400' },
      'PHASE_3_TOP': { name: '第三阶段（顶部）', color: 'bg-amber-500/20 text-amber-400' },
      'PHASE_4_FALLING': { name: '第四阶段（下降）', color: 'bg-red-500/20 text-red-400' },
    }
    return phases[phase] || { name: '未知', color: 'bg-gray-500/20 text-gray-400' }
  }

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      >
        <div className="glass-card p-8 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-gray-400">加载中...</p>
        </div>
      </motion.div>
    )
  }

  if (error || !stockData) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <div className="glass-card p-8 text-center" onClick={(e) => e.stopPropagation()}>
          <AlertCircle className="w-8 h-8 mx-auto mb-4 text-red-400" />
          <p className="text-gray-400">{error || '暂无数据'}</p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg"
          >
            关闭
          </button>
        </div>
      </motion.div>
    )
  }

  const phaseInfo = getPhaseInfo(stockData.phase)
  const signal = stockData.signals[0]
  const currentPrice = stockData.current_price || signal?.current_price || 0
  const ma30 = stockData.ma30_week || signal?.ma30_week || 0
  const volumeRatio = signal?.volume_ratio || 1.0

  // 构建图表数据
  const chartData = [
    { date: '前期', price: ma30 * 0.9, ma30: ma30 * 0.95 },
    { date: '近期', price: ma30 * 0.95, ma30: ma30 * 0.98 },
    { date: '当前', price: currentPrice, ma30: ma30 },
  ]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="w-full max-w-5xl max-h-[90vh] overflow-y-auto glass-strong rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 glass-strong border-b border-white/10 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-cyan-400 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{stockData.stock_name || stockCode}</h2>
              <p className="text-gray-400 text-sm">{stockCode}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${phaseInfo.color}`}>
              {phaseInfo.name}
            </span>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Price Header */}
          <div className="flex items-end justify-between">
            <div>
              <div className="flex items-baseline gap-3">
                <span className="text-4xl font-bold text-white">¥{currentPrice.toFixed(2)}</span>
              </div>
              <p className="text-gray-400 text-sm mt-2">30周均线: ¥{ma30.toFixed(2)}</p>
            </div>
            
            <div className="flex gap-3">
              <button className="px-6 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors font-medium">
                买入
              </button>
              <button className="px-6 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors font-medium">
                卖出
              </button>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: '30周均线', value: `¥${ma30.toFixed(2)}`, icon: Activity },
              { label: '成交量比', value: `${volumeRatio.toFixed(2)}x`, icon: BarChart3 },
              { label: '信号类型', value: signal?.type || 'HOLD', icon: Target },
              { label: '止损价', value: signal?.stop_loss ? `¥${signal.stop_loss.toFixed(2)}` : '未设置', icon: Clock },
            ].map((metric, index) => {
              const Icon = metric.icon
              return (
                <motion.div
                  key={metric.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass p-4 rounded-xl"
                >
                  <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                    <Icon className="w-4 h-4" />
                    {metric.label}
                  </div>
                  <p className="text-xl font-semibold text-white">{metric.value}</p>
                </motion.div>
              )
            })}
          </div>

          {/* Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">价格走势与30周均线</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} domain={['dataMin - 5', 'dataMax + 5']} />
                  <Area 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    fill="url(#priceGradient)" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="ma30" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                  <ReferenceLine y={ma30} stroke="#10B981" strokeDasharray="3 3" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center gap-6 mt-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-primary"></span>
                <span className="text-sm text-gray-400">股价</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                <span className="text-sm text-gray-400">30周均线</span>
              </div>
            </div>
          </motion.div>

          {/* Analysis */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {analysisPointsTemplate.map((point, index) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.05 }}
                className={`glass p-4 rounded-xl border-l-4 ${
                  point.positive ? 'border-emerald-500' : 'border-amber-500'
                }`}
              >
                <h4 className="text-white font-medium mb-2 flex items-center gap-2">
                  {point.positive ? (
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-400" />
                  )}
                  {point.title}
                </h4>
                <p className="text-gray-400 text-sm leading-relaxed">{point.content}</p>
              </motion.div>
            ))}
          </motion.div>

          {/* Signal Reason */}
          {signal?.reason && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="glass-card p-6 border-l-4 border-primary"
            >
              <h3 className="text-lg font-semibold text-white mb-4">信号分析</h3>
              <p className="text-gray-300 text-sm leading-relaxed">{signal.reason}</p>
            </motion.div>
          )}

          {/* Trading Suggestion */}
          {signal && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="glass-card p-6 border-l-4 border-primary"
            >
              <h3 className="text-lg font-semibold text-white mb-4">交易建议</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-gray-400 text-sm mb-2">建议操作</p>
                  <p className={`font-semibold text-lg ${
                    signal.type === 'BUY' ? 'text-emerald-400' :
                    signal.type === 'SELL' ? 'text-red-400' :
                    'text-blue-400'
                  }`}>
                    {signal.type === 'BUY' ? '买入' :
                     signal.type === 'SELL' ? '卖出' :
                     signal.type === 'HOLD' ? '持有' : '观察'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-2">建议仓位</p>
                  <p className="text-white font-semibold text-lg">
                    {signal.position_size ? `${signal.position_size}股` : '未计算'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-2">止损设置</p>
                  <p className="text-red-400 font-semibold text-lg">
                    {signal.stop_loss ? `¥${signal.stop_loss.toFixed(2)}` : '未设置'}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
