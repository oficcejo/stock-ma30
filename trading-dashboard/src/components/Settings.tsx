import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Bell, 
  Database, 
  Brain,
  Save,
  CheckCircle,
  Webhook,
  Clock
} from 'lucide-react'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('notifications')
  const [saved, setSaved] = useState(false)

  const [config, setConfig] = useState({
    // 通知设置
    dingtalkEnabled: true,
    dingtalkWebhook: 'https://oapi.dingtalk.com/robot/send?access_token=***',
    dingtalkSecret: '',
    feishuEnabled: false,
    feishuWebhook: '',
    
    // AI设置
    aiEnabled: true,
    aiApiKey: '',
    aiApiBase: 'https://api.openai.com/v1',
    aiModel: 'gpt-4',
    
    // 定时任务
    scheduleEnabled: true,
    scheduleDay: 5,
    scheduleTime: '15:30',
    
    // 数据源
    dataSource: 'tdx-api',
    tdxApiUrl: 'http://43.138.33.77:8080',
  })

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const tabs = [
    { id: 'notifications', label: '通知设置', icon: Bell },
    { id: 'ai', label: 'AI分析', icon: Brain },
    { id: 'schedule', label: '定时任务', icon: Clock },
    { id: 'data', label: '数据源', icon: Database },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-2xl font-bold text-white">系统设置</h2>
        <p className="text-gray-400 mt-1">配置交易系统参数和集成服务</p>
      </motion.div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Tabs */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:w-64 space-y-2"
        >
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  activeTab === tab.id
                    ? 'bg-primary/20 text-primary border border-primary/30'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            )
          })}
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex-1"
        >
          <div className="glass-card p-6">
            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Webhook className="w-5 h-5 text-primary" />
                  Webhook通知配置
                </h3>

                {/* DingTalk */}
                <div className="glass p-4 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                        <Bell className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium">钉钉通知</h4>
                        <p className="text-gray-500 text-sm">通过钉钉机器人发送交易信号</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.dingtalkEnabled}
                        onChange={(e) => setConfig({ ...config, dingtalkEnabled: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  {config.dingtalkEnabled && (
                    <div className="space-y-3 pt-4 border-t border-white/10">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Webhook地址</label>
                        <input
                          type="text"
                          value={config.dingtalkWebhook}
                          onChange={(e) => setConfig({ ...config, dingtalkWebhook: e.target.value })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                          placeholder="https://oapi.dingtalk.com/robot/send?access_token=..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Secret密钥（可选）</label>
                        <input
                          type="password"
                          value={config.dingtalkSecret}
                          onChange={(e) => setConfig({ ...config, dingtalkSecret: e.target.value })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                          placeholder="SEC..."
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Feishu */}
                <div className="glass p-4 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                        <Bell className="w-5 h-5 text-emerald-400" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium">飞书通知</h4>
                        <p className="text-gray-500 text-sm">通过飞书机器人发送交易信号</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.feishuEnabled}
                        onChange={(e) => setConfig({ ...config, feishuEnabled: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  {config.feishuEnabled && (
                    <div className="pt-4 border-t border-white/10">
                      <label className="block text-sm text-gray-400 mb-2">Webhook地址</label>
                      <input
                        type="text"
                        value={config.feishuWebhook}
                        onChange={(e) => setConfig({ ...config, feishuWebhook: e.target.value })}
                        className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                        placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AI Tab */}
            {activeTab === 'ai' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Brain className="w-5 h-5 text-primary" />
                  AI分析配置
                </h3>

                <div className="glass p-4 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-white font-medium">启用AI分析</h4>
                      <p className="text-gray-500 text-sm">使用大模型进行深度分析</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.aiEnabled}
                        onChange={(e) => setConfig({ ...config, aiEnabled: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  {config.aiEnabled && (
                    <div className="space-y-3 pt-4 border-t border-white/10">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">API Key</label>
                        <input
                          type="password"
                          value={config.aiApiKey}
                          onChange={(e) => setConfig({ ...config, aiApiKey: e.target.value })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                          placeholder="sk-..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">API Base URL</label>
                        <input
                          type="text"
                          value={config.aiApiBase}
                          onChange={(e) => setConfig({ ...config, aiApiBase: e.target.value })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                          placeholder="https://api.openai.com/v1"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">模型</label>
                        <select
                          value={config.aiModel}
                          onChange={(e) => setConfig({ ...config, aiModel: e.target.value })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                        >
                          <option value="gpt-4">GPT-4</option>
                          <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                          <option value="deepseek-chat">DeepSeek Chat</option>
                          <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Schedule Tab */}
            {activeTab === 'schedule' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  定时任务配置
                </h3>

                <div className="glass p-4 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-white font-medium">启用定时分析</h4>
                      <p className="text-gray-500 text-sm">每周自动执行股票分析</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.scheduleEnabled}
                        onChange={(e) => setConfig({ ...config, scheduleEnabled: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  {config.scheduleEnabled && (
                    <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">执行日期</label>
                        <select
                          value={config.scheduleDay}
                          onChange={(e) => setConfig({ ...config, scheduleDay: parseInt(e.target.value) })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                        >
                          <option value={0}>周日</option>
                          <option value={1}>周一</option>
                          <option value={2}>周二</option>
                          <option value={3}>周三</option>
                          <option value={4}>周四</option>
                          <option value={5}>周五</option>
                          <option value={6}>周六</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">执行时间</label>
                        <input
                          type="time"
                          value={config.scheduleTime}
                          onChange={(e) => setConfig({ ...config, scheduleTime: e.target.value })}
                          className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="glass p-4 rounded-xl">
                  <h4 className="text-white font-medium mb-3">股票池配置</h4>
                  <textarea
                    defaultValue="000001,000002,000333,000858,002594,300750,600000,600519,601012,601318"
                    rows={3}
                    className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                    placeholder="输入股票代码，用逗号分隔..."
                  />
                  <p className="text-gray-500 text-xs mt-2">输入要监控的股票代码，用逗号分隔</p>
                </div>
              </div>
            )}

            {/* Data Source Tab */}
            {activeTab === 'data' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary" />
                  数据源配置
                </h3>

                <div className="glass p-4 rounded-xl space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">数据源类型</label>
                    <select
                      value={config.dataSource}
                      onChange={(e) => setConfig({ ...config, dataSource: e.target.value })}
                      className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                    >
                      <option value="tdx-api">TDX API</option>
                      <option value="akshare">AKShare</option>
                      <option value="tushare">Tushare</option>
                    </select>
                  </div>

                  {config.dataSource === 'tdx-api' && (
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">API地址</label>
                      <input
                        type="text"
                        value={config.tdxApiUrl}
                        onChange={(e) => setConfig({ ...config, tdxApiUrl: e.target.value })}
                        className="w-full px-4 py-2 bg-dark border border-white/10 rounded-lg text-sm focus:outline-none focus:border-primary/50 transition-colors"
                        placeholder="http://localhost:8080"
                      />
                    </div>
                  )}
                </div>

                <div className="glass p-4 rounded-xl border-l-4 border-emerald-500">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-white font-medium mb-1">连接状态</h4>
                      <p className="text-gray-400 text-sm">
                        数据源连接正常，上次更新: 2024-01-15 15:00:00
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="flex items-center justify-between pt-6 border-t border-white/10">
              <div>
                {saved && (
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2 text-emerald-400"
                  >
                    <CheckCircle className="w-5 h-5" />
                    <span>设置已保存</span>
                  </motion.div>
                )}
              </div>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium"
              >
                <Save className="w-4 h-4" />
                保存设置
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
