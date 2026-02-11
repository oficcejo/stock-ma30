"""
定时任务调度器
整合完整交易流程
"""
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config import get_settings
from core import DataCollector, PhaseAnalyzer, SignalGenerator, RiskManager
from services import MultiNotifier, AIAnalyzer
from models import (
    TradeSignal, AnalysisResult, MarketContext, 
    StockPhase, PhaseMetrics, AIAnalysisResponse
)


class TradingSystem:
    """
    交易系统主类
    
    整合所有模块，完成完整的交易流程：
    1. 获取股票数据
    2. 分析阶段
    3. 生成信号
    4. AI分析
    5. 发送通知
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.data_collector = DataCollector()
        self.phase_analyzer = PhaseAnalyzer()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.notifier = MultiNotifier()
        self.ai_analyzer = AIAnalyzer()
        
        # 存储结果
        self.analysis_results: List[AnalysisResult] = []
        self.trade_signals: List[TradeSignal] = []
        self.ai_responses: List[AIAnalysisResponse] = []
    
    async def analyze_single_stock(
        self, 
        stock_code: str,
        stock_name: str = "",
        market_context: Optional[MarketContext] = None
    ) -> Optional[AnalysisResult]:
        """分析单只股票"""
        try:
            logger.info(f"开始分析股票: {stock_code}")
            
            # 1. 获取数据
            df = await self.data_collector.get_weekly_data(stock_code, weeks=150)
            if df is None or len(df) < 30:
                logger.warning(f"{stock_code} 数据不足")
                return None
            
            # 2. 计算30周均线
            df["ma30"] = self.phase_analyzer.calculate_ma30(df)
            df["volume_ma"] = df["volume"].rolling(window=10).mean()
            
            # 3. 分析阶段
            phase, metrics = self.phase_analyzer.analyze_phase(df)
            
            # 4. 生成信号
            signals = self.signal_generator.generate_signals(
                stock_code, stock_name, df, market_context
            )
            
            # 5. 应用风险管理
            for signal in signals:
                self.risk_manager.apply_risk_management(
                    signal,
                    signal.current_price
                )
            
            # 构建结果
            result = AnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name or stock_code,
                phase=phase,
                metrics=metrics,
                signals=signals,
                weekly_data=[],  # 不存储原始数据，节省内存
                analysis_date=datetime.now()
            )
            
            logger.info(f"{stock_code} 分析完成，阶段: {phase.name}")
            return result
            
        except Exception as e:
            logger.error(f"分析股票 {stock_code} 失败: {e}")
            return None
    
    async def get_market_context(self) -> Optional[MarketContext]:
        """获取市场环境"""
        try:
            index_code = self.settings.index_code
            
            # 获取大盘数据
            df = await self.data_collector.get_weekly_data(index_code, weeks=100)
            if df is None:
                return None
            
            # 分析大盘阶段
            phase, metrics = self.phase_analyzer.analyze_phase(df)
            
            # 判断市场情绪
            if phase == StockPhase.PHASE_2_RISING:
                sentiment = " bullish（看涨）"
                risk = "medium"
            elif phase == StockPhase.PHASE_4_FALLING:
                sentiment = "bearish（看跌）"
                risk = "high"
            elif phase == StockPhase.PHASE_1_BOTTOM:
                sentiment = "筑底中"
                risk = "low"
            else:
                sentiment = "震荡"
                risk = "medium"
            
            return MarketContext(
                index_code=index_code,
                index_name="上证指数",
                index_phase=phase,
                index_ma30=df["ma30"].iloc[-1] if "ma30" in df.columns else 0,
                market_sentiment=sentiment,
                risk_level=risk
            )
            
        except Exception as e:
            logger.error(f"获取市场环境失败: {e}")
            return None
    
    async def run_full_analysis(self) -> List[TradeSignal]:
        """
        运行完整分析流程
        
        Returns:
            所有生成的交易信号
        """
        logger.info("=" * 50)
        logger.info("开始执行完整分析流程")
        logger.info("=" * 50)
        
        # 1. 获取市场环境
        market_context = await self.get_market_context()
        if market_context:
            logger.info(f"大盘环境: {market_context.market_sentiment}")
        
        # 2. 获取股票列表
        stock_codes = self.settings.get_stock_list()
        logger.info(f"股票池数量: {len(stock_codes)}")
        
        # 3. 分析每只股票
        self.analysis_results = []
        self.trade_signals = []
        
        for code in stock_codes:
            result = await self.analyze_single_stock(code, market_context=market_context)
            if result:
                self.analysis_results.append(result)
                self.trade_signals.extend(result.signals)
        
        logger.info(f"分析完成，共 {len(self.analysis_results)} 只股票")
        logger.info(f"生成 {len(self.trade_signals)} 个交易信号")
        
        return self.trade_signals
    
    async def send_notifications(self, signals: Optional[List[TradeSignal]] = None):
        """发送通知"""
        if signals is None:
            signals = self.trade_signals
        
        if not signals:
            logger.info("没有信号需要发送")
            return
        
        # 只发送买入和卖出信号
        important_signals = [
            s for s in signals 
            if s.signal_type.value in ["BUY", "SELL"]
        ]
        
        if not important_signals:
            logger.info("没有重要信号需要发送")
            return
        
        logger.info(f"发送 {len(important_signals)} 个重要信号")
        
        # 发送汇总
        await self.notifier.send_batch_signals(important_signals)
        
        # 逐个发送详细信号
        for signal in important_signals[:5]:  # 最多发送5个
            await self.notifier.send_trade_signal(signal)
            await asyncio.sleep(0.5)  # 避免发送过快
    
    async def run_ai_analysis(self, selected_stocks: Optional[List[str]] = None):
        """
        运行AI分析
        
        Args:
            selected_stocks: 指定分析的股票代码，None则分析所有有信号的股票
        """
        if not self.settings.openai_api_key:
            logger.info("OpenAI API未配置，跳过AI分析")
            return
        
        # 获取需要分析的股票
        if selected_stocks:
            results = [r for r in self.analysis_results if r.stock_code in selected_stocks]
        else:
            # 分析有买入信号的股票
            results = [
                r for r in self.analysis_results 
                if any(s.signal_type.value == "BUY" for s in r.signals)
            ]
        
        if not results:
            logger.info("没有需要AI分析的股票")
            return
        
        logger.info(f"开始对 {len(results)} 只股票进行AI分析")
        
        # 获取市场环境
        market_context = await self.get_market_context()
        
        # AI分析
        self.ai_responses = []
        for result in results[:3]:  # 最多分析3只
            try:
                ai_response = await self.ai_analyzer.analyze_stock(
                    result, market_context
                )
                if ai_response:
                    self.ai_responses.append(ai_response)
                    # 发送AI分析结果
                    await self.notifier.send_ai_analysis(ai_response)
                    await asyncio.sleep(1)  # 避免API调用过快
            except Exception as e:
                logger.error(f"AI分析 {result.stock_code} 失败: {e}")
        
        logger.info(f"AI分析完成，共 {len(self.ai_responses)} 个结果")
    
    async def close(self):
        """关闭资源"""
        await self.data_collector.client.aclose()


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.trading_system = TradingSystem()
    
    def start(self):
        """启动调度器"""
        # 解析定时配置
        schedule_day = self.settings.schedule_day  # 0=周日, 5=周五
        schedule_time = self.settings.schedule_time  # "15:30"
        
        hour, minute = map(int, schedule_time.split(":"))
        
        # 添加定时任务（每周执行）
        self.scheduler.add_job(
            self._scheduled_task,
            CronTrigger(day_of_week=schedule_day, hour=hour, minute=minute),
            id="weekly_analysis",
            name="每周股票分析",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"定时任务已启动：每周{schedule_day} {schedule_time}")
    
    async def _scheduled_task(self):
        """定时执行的任务"""
        logger.info("执行定时分析任务")
        
        try:
            # 运行完整分析
            signals = await self.trading_system.run_full_analysis()
            
            # 发送通知
            await self.trading_system.send_notifications(signals)
            
            # AI分析
            await self.trading_system.run_ai_analysis()
            
            logger.info("定时任务执行完成")
            
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
            # 发送错误通知
            await self.trading_system.notifier.send_text(
                f"交易分析任务执行失败: {e}",
                title="系统错误"
            )
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务已停止")


# 便捷函数
async def run_analysis_task():
    """运行单次分析任务（便捷函数）"""
    trading_system = TradingSystem()
    
    try:
        # 运行分析
        signals = await trading_system.run_full_analysis()
        
        # 发送通知
        await trading_system.send_notifications(signals)
        
        # AI分析
        await trading_system.run_ai_analysis()
        
        return signals
        
    finally:
        await trading_system.close()


# 测试代码
if __name__ == "__main__":
    async def test():
        signals = await run_analysis_task()
        print(f"生成 {len(signals)} 个信号")
        for s in signals[:3]:
            print(f"{s.stock_code}: {s.signal_type.value} - {s.reason[:50]}...")
    
    asyncio.run(test())
