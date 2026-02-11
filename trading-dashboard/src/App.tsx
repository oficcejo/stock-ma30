import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Settings,
  BarChart3,
  PieChart,
  AlertCircle,
  RefreshCw,
  Search,
  Menu,
  X,
  Scan,
  Github
} from 'lucide-react'
import Dashboard from './components/Dashboard'
import Signals from './components/Signals'
import StockDetail from './components/StockDetail'
import SettingsPage from './components/Settings'
import MarketScan from './components/MarketScan'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedStock, setSelectedStock] = useState<string | null>(null)
  const [marketData, setMarketData] = useState({
    indexPhase: 'PHASE_2_RISING',
    sentiment: 'bullish',
    lastUpdate: new Date().toLocaleString('zh-CN')
  })

  const navItems = [
    { id: 'dashboard', label: '监控面板', icon: BarChart3 },
    { id: 'marketscan', label: '全市场扫描', icon: Scan },
    { id: 'signals', label: '交易信号', icon: Activity },
    { id: 'settings', label: '系统设置', icon: Settings },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onStockSelect={setSelectedStock} marketData={marketData} />
      case 'marketscan':
        return <MarketScan />
      case 'signals':
        return <Signals onStockSelect={setSelectedStock} />
      case 'settings':
        return <SettingsPage />
      default:
        return <Dashboard onStockSelect={setSelectedStock} marketData={marketData} />
    }
  }

  return (
    <div className="min-h-screen bg-dark flex">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -280 }}
        animate={{ x: sidebarOpen ? 0 : -280 }}
        transition={{ duration: 0.3 }}
        className="fixed left-0 top-0 h-full w-70 bg-dark-lighter border-r border-white/10 z-50"
      >
        <div className="p-6">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-cyan-400 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">30周均线系统</h1>
              <a
                href="https://www.bilibili.com/video/BV1twFSzNE75"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline transition-colors"
                title="点击观看理论讲解视频"
              >
                基于史丹·温斯坦 ↗
              </a>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    activeTab === item.id
                      ? 'bg-primary/20 text-primary border border-primary/30'
                      : 'text-gray-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              )
            })}
          </nav>

          {/* Market Status */}
          <div className="mt-10 p-4 glass-card">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">市场环境</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">大盘阶段</span>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  marketData.indexPhase === 'PHASE_2_RISING' 
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : marketData.indexPhase === 'PHASE_4_FALLING'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {marketData.indexPhase === 'PHASE_2_RISING' ? '上升趋势'
                    : marketData.indexPhase === 'PHASE_4_FALLING' ? '下降趋势'
                    : '震荡整理'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">市场情绪</span>
                <span className={`text-xs font-medium ${
                  marketData.sentiment === 'bullish' ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {marketData.sentiment === 'bullish' ? '看涨' : '看跌'}
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              更新: {marketData.lastUpdate}
            </p>
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-70' : 'ml-0'}`}>
        {/* Header */}
        <header className="sticky top-0 z-40 glass-strong border-b border-white/10">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索股票代码或名称..."
                  className="w-64 pl-10 pr-4 py-2 bg-dark-lighter border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                />
              </div>
            </div>

            <div className="flex items-center gap-4">
              <a
                href="https://github.com/oficcejo/stock-ma30.git"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 hover:text-white transition-colors"
              >
                <Github className="w-4 h-4" />
                <span className="text-sm font-medium">GitHub</span>
              </a>
              <button 
                onClick={() => window.location.reload()}
                className="flex items-center gap-2 px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span className="text-sm font-medium">刷新页面</span>
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          {renderContent()}
        </div>
      </main>

      {/* Stock Detail Modal */}
      {selectedStock && (
        <StockDetail
          stockCode={selectedStock}
          onClose={() => setSelectedStock(null)}
        />
      )}
    </div>
  )
}

export default App
