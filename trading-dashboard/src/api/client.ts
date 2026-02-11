// API客户端
const API_BASE_URL = 'http://localhost:8000';

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`API请求: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    console.log(`API响应: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API错误: ${errorText}`);
      throw new Error(`API请求失败 (${response.status}): ${errorText}`);
    }
    
    return response.json();
  } catch (error: any) {
    console.error(`API请求异常: ${error.message}`);
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('无法连接到后端服务 (http://localhost:8000)，请确认后端已启动');
    }
    throw error;
  }
}

// 获取股票分析数据
export async function getStockAnalysis(code: string) {
  return fetchAPI(`/api/analyze/stock/${code}`);
}

// 获取所有信号
export async function getSignals() {
  const response = await fetchAPI('/api/signals');
  // 后端返回 { signals: [...], total: N }
  return response.signals || [];
}

// 获取市场环境
export async function getMarketContext() {
  return fetchAPI('/api/market/context');
}

// 执行分析
export async function runAnalysis(stockCodes?: string[]) {
  return fetchAPI('/api/analyze/run', { 
    method: 'POST',
    body: JSON.stringify({
      stock_codes: stockCodes || [],
      send_notification: false,
      run_ai_analysis: false
    })
  });
}

// 获取实时行情
export async function getRealtimeQuote(code: string) {
  try {
    const data = await fetchAPI(`/api/quote?code=${code}`);
    return data;
  } catch (e) {
    return null;
  }
}

// 全市场扫描 - 找出第二阶段股票并生成交易信号
export async function scanMarket(
  maxStocks: number = 0,  // 0表示不限制
  excludeST: boolean = true,
  excludeGEM: boolean = true,
  excludeSTAR: boolean = true,
  generateSignals: boolean = true
) {
  const params = new URLSearchParams({
    exclude_st: excludeST.toString(),
    exclude_gem: excludeGEM.toString(),
    exclude_star: excludeSTAR.toString(),
    generate_signals: generateSignals.toString()
  });
  // 只有当maxStocks>0时才添加参数
  if (maxStocks > 0) {
    params.append('max_stocks', maxStocks.toString());
  }
  return fetchAPI(`/api/market/scan?${params}`);
}

// 获取市场统计
export async function getMarketStatistics() {
  return fetchAPI('/api/market/statistics');
}

// 获取扫描历史记录
export async function getScanHistory(startDate?: string, endDate?: string, limit: number = 100) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  params.append('limit', limit.toString());
  return fetchAPI(`/api/market/scan/history?${params}`);
}

// 获取最新扫描结果
export async function getLatestScanResults() {
  return fetchAPI('/api/market/scan/latest');
}

// 获取持续强势股（多日出现在第二阶段）
export async function getPersistentPhase2Stocks(minDays: number = 3) {
  return fetchAPI(`/api/market/scan/persistent?min_days=${minDays}`);
}
