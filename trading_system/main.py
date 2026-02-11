"""
30周均线交易系统 - 主入口
基于史丹·温斯坦《一条均线定乾坤》
"""
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from config import get_settings
from scheduler import TaskScheduler, run_analysis_task, TradingSystem
from services import MultiNotifier, AIAnalyzer
from core import DataCollector, PhaseAnalyzer


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/trading_system.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

# 全局实例
trading_system: Optional[TradingSystem] = None
task_scheduler: Optional[TaskScheduler] = None


# 请求模型
class AnalyzeRequest(BaseModel):
    stock_codes: Optional[list] = None
    send_notification: bool = True
    run_ai_analysis: bool = False


class NotifyRequest(BaseModel):
    message: str
    title: Optional[str] = "交易系统通知"


class StockAnalysisRequest(BaseModel):
    stock_code: str
    stock_name: Optional[str] = ""


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global trading_system, task_scheduler
    
    # 启动时初始化
    logger.info("启动30周均线交易系统...")
    
    trading_system = TradingSystem()
    task_scheduler = TaskScheduler()
    
    # 启动定时任务
    task_scheduler.start()
    
    logger.info("系统启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("关闭系统...")
    if task_scheduler:
        task_scheduler.shutdown()
    if trading_system:
        await trading_system.close()
    logger.info("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="30周均线交易系统",
    description="基于史丹·温斯坦《一条均线定乾坤》的量化交易系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "30周均线交易系统",
        "version": "1.0.0",
        "description": "基于史丹·温斯坦《一条均线定乾坤》",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": trading_system.analysis_results[0].analysis_date if trading_system and trading_system.analysis_results else None}


@app.post("/api/analyze/run")
async def run_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    执行分析任务
    
    - 分析股票池中的所有股票
    - 生成交易信号
    - 可选：发送通知、AI分析
    """
    try:
        if request.stock_codes:
            # 分析指定股票
            results = []
            for code in request.stock_codes:
                result = await trading_system.analyze_single_stock(code)
                if result:
                    results.append(result)
            signals = [s for r in results for s in r.signals]
            # 保存信号到系统存储
            trading_system.trade_signals.extend(signals)
        else:
            # 分析股票池
            signals = await trading_system.run_full_analysis()
        
        # 后台任务
        if request.send_notification:
            background_tasks.add_task(trading_system.send_notifications, signals)
        
        if request.run_ai_analysis:
            background_tasks.add_task(trading_system.run_ai_analysis)
        
        return {
            "success": True,
            "message": f"分析完成，生成 {len(signals)} 个信号",
            "signals_count": len(signals),
            "signals": [
                {
                    "stock_code": s.stock_code,
                    "stock_name": s.stock_name,
                    "signal_type": s.signal_type.value,
                    "phase": s.phase.name,
                    "current_price": s.current_price,
                    "reason": s.reason[:100] + "..." if len(s.reason) > 100 else s.reason
                }
                for s in signals[:10]  # 最多返回10个
            ]
        }
        
    except Exception as e:
        logger.error(f"分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyze/stock/{stock_code}")
async def analyze_single_stock_get(stock_code: str):
    """分析单只股票 - GET版本"""
    try:
        result = await trading_system.analyze_single_stock(stock_code)
        
        if not result:
            raise HTTPException(status_code=404, detail="无法获取股票数据")
        
        return {
            "success": True,
            "stock_code": result.stock_code,
            "stock_name": result.stock_name,
            "phase": result.phase.name,
            "current_price": result.signals[0].current_price if result.signals else None,
            "ma30_week": result.signals[0].ma30_week if result.signals else None,
            "signals": [
                {
                    "type": s.signal_type.value,
                    "current_price": s.current_price,
                    "ma30_week": s.ma30_week,
                    "volume_ratio": s.volume_ratio,
                    "reason": s.reason,
                    "stop_loss": s.stop_loss,
                    "position_size": s.position_size
                }
                for s in result.signals
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/stock")
async def analyze_single_stock(request: StockAnalysisRequest):
    """分析单只股票"""
    try:
        result = await trading_system.analyze_single_stock(
            request.stock_code,
            request.stock_name
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="无法获取股票数据")
        
        return {
            "success": True,
            "stock_code": result.stock_code,
            "stock_name": result.stock_name,
            "phase": result.phase.name,
            "metrics": {
                "ma30_slope": result.metrics.ma30_slope,
                "ma30_direction": result.metrics.ma30_direction,
                "price_to_ma_ratio": result.metrics.price_to_ma_ratio,
                "consolidation_weeks": result.metrics.consolidation_weeks,
                "breakout_confirmed": result.metrics.breakout_confirmed,
                "volume_confirmation": result.metrics.volume_confirmation
            },
            "signals": [
                {
                    "type": s.signal_type.value,
                    "current_price": s.current_price,
                    "ma30_week": s.ma30_week,
                    "volume_ratio": s.volume_ratio,
                    "reason": s.reason,
                    "stop_loss": s.stop_loss,
                    "position_size": s.position_size
                }
                for s in result.signals
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals")
async def get_signals(signal_type: Optional[str] = None, limit: int = 50):
    """获取交易信号列表"""
    if not trading_system or not trading_system.trade_signals:
        return {"signals": [], "total": 0}
    
    signals = trading_system.trade_signals
    
    # 过滤
    if signal_type:
        signals = [s for s in signals if s.signal_type.value == signal_type.upper()]
    
    # 限制数量
    signals = signals[:limit]
    
    return {
        "signals": [
            {
                "stock_code": s.stock_code,
                "stock_name": s.stock_name,
                "signal_type": s.signal_type.value,
                "phase": s.phase.name,
                "current_price": s.current_price,
                "ma30_week": s.ma30_week,
                "volume_ratio": s.volume_ratio,
                "reason": s.reason[:200] + "..." if len(s.reason) > 200 else s.reason,
                "stop_loss": s.stop_loss,
                "position_size": s.position_size,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None
            }
            for s in signals
        ],
        "total": len(trading_system.trade_signals)
    }


@app.get("/api/market/context")
async def get_market_context():
    """获取市场环境"""
    try:
        context = await trading_system.get_market_context()
        if not context:
            return {"error": "无法获取市场环境"}
        
        return {
            "index_code": context.index_code,
            "index_name": context.index_name,
            "index_phase": context.index_phase.name,
            "index_ma30": context.index_ma30,
            "market_sentiment": context.market_sentiment,
            "risk_level": context.risk_level
        }
        
    except Exception as e:
        logger.error(f"获取市场环境失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notify")
async def send_notification(request: NotifyRequest):
    """发送测试通知"""
    try:
        notifier = MultiNotifier()
        success = await notifier.send_text(request.message, request.title)
        
        return {
            "success": success,
            "message": "通知已发送" if success else "通知发送失败"
        }
        
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/analyze")
async def run_ai_analysis(stock_code: Optional[str] = None):
    """运行AI分析"""
    try:
        if not trading_system.settings.openai_api_key:
            return {"error": "OpenAI API未配置"}
        
        # 找到对应的分析结果
        if stock_code:
            result = next(
                (r for r in trading_system.analysis_results if r.stock_code == stock_code),
                None
            )
            if not result:
                raise HTTPException(status_code=404, detail="未找到该股票的分析结果")
            
            market_context = await trading_system.get_market_context()
            ai_response = await trading_system.ai_analyzer.analyze_stock(
                result, market_context
            )
            
            if ai_response:
                return {
                    "success": True,
                    "stock_code": ai_response.stock_code,
                    "recommendation": ai_response.recommendation,
                    "confidence": ai_response.confidence,
                    "risk_factors": ai_response.risk_factors,
                    "analysis": ai_response.analysis_text
                }
            else:
                return {"error": "AI分析失败"}
        else:
            # 批量分析
            await trading_system.run_ai_analysis()
            return {
                "success": True,
                "message": f"AI分析完成，共 {len(trading_system.ai_responses)} 个结果"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quote")
async def get_quote(code: str):
    """获取实时行情"""
    try:
        collector = DataCollector()
        quote = await collector.get_realtime_quote(code)
        
        if quote:
            return {
                "success": True,
                "code": code,
                "data": quote
            }
        else:
            raise HTTPException(status_code=404, detail="无法获取行情数据")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """获取配置信息（隐藏敏感信息）"""
    settings = get_settings()
    
    return {
        "stock_pool": settings.get_stock_list(),
        "index_code": settings.index_code,
        "max_loss_percent": settings.max_loss_percent,
        "stop_loss_percent": settings.stop_loss_percent,
        "schedule_day": settings.schedule_day,
        "schedule_time": settings.schedule_time,
        "dingtalk_configured": bool(settings.dingtalk_webhook_url),
        "feishu_configured": bool(settings.feishu_webhook_url),
        "ai_configured": bool(settings.openai_api_key)
    }


@app.get("/api/market/scan")
async def scan_market(
    max_stocks: int = 0,
    exclude_st: bool = True,
    exclude_gem: bool = True,
    exclude_star: bool = True,
    generate_signals: bool = True
):
    """
    全市场扫描 - 找出第二阶段股票并生成交易信号
    
    Args:
        max_stocks: 最大返回数量（0表示不限制，默认0）
        exclude_st: 排除ST股票
        exclude_gem: 排除创业板(300/301)
        exclude_star: 排除科创板(688)
        generate_signals: 是否生成交易信号（默认True）
    """
    try:
        from core.stock_scanner import StockScanner, StockFilter
        
        filter_config = StockFilter(
            exclude_st=exclude_st,
            exclude_gem=exclude_gem,
            exclude_star=exclude_star,
            exclude_bse=True,
            exclude_delisting=True
        )
        
        async with StockScanner(filter_config) as scanner:
            if max_stocks > 0:
                logger.info(f"开始全市场扫描，最多返回 {max_stocks} 只股票...")
            else:
                logger.info("开始全市场扫描，不限制返回数量...")
            
            phase2_stocks, trade_signals = await scanner.scan_phase2_stocks(
                max_stocks=max_stocks,
                batch_size=10,
                generate_signals=generate_signals
            )
            
            # 将信号添加到全局交易信号列表
            if generate_signals and trade_signals:
                global trading_system
                if trading_system:
                    for signal in trade_signals:
                        # 避免重复添加
                        existing = [s for s in trading_system.trade_signals 
                                  if s.stock_code == signal.stock_code and 
                                  s.signal_type == signal.signal_type]
                        if not existing:
                            trading_system.trade_signals.append(signal)
                            logger.info(f"已将 {signal.stock_code} 的 {signal.signal_type.value} 信号加入监测")
                
                logger.info(f"扫描完成，共生成 {len(trade_signals)} 个交易信号并加入监测")
            
            return {
                "success": True,
                "count": len(phase2_stocks),
                "signal_count": len(trade_signals),
                "stocks": phase2_stocks,
                "signals": [
                    {
                        "stock_code": s.stock_code,
                        "stock_name": s.stock_name,
                        "signal_type": s.signal_type.value,
                        "phase": s.phase.name,
                        "current_price": s.current_price,
                        "reason": s.reason[:100] + "..." if len(s.reason) > 100 else s.reason
                    }
                    for s in trade_signals[:20]  # 最多返回20个信号详情
                ],
                "filter": {
                    "exclude_st": exclude_st,
                    "exclude_gem": exclude_gem,
                    "exclude_star": exclude_star
                }
            }
            
    except Exception as e:
        logger.error(f"市场扫描失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/statistics")
async def market_statistics():
    """获取市场统计信息"""
    try:
        from core.stock_scanner import StockScanner
        
        async with StockScanner() as scanner:
            stats = await scanner.get_market_statistics()
            return {
                "success": True,
                "data": stats
            }
            
    except Exception as e:
        logger.error(f"获取市场统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/scan/history")
async def get_scan_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stock_code: Optional[str] = None,
    limit: int = 100
):
    """
    获取扫描历史记录
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        stock_code: 股票代码过滤
        limit: 返回数量限制
    """
    try:
        from models import get_scan_db
        
        db = get_scan_db()
        records = db.get_scan_history(start_date, end_date, stock_code, limit)
        
        return {
            "success": True,
            "count": len(records),
            "records": records
        }
        
    except Exception as e:
        logger.error(f"获取扫描历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/scan/statistics")
async def get_scan_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 30
):
    """
    获取扫描统计历史
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数量限制
    """
    try:
        from models import get_scan_db
        
        db = get_scan_db()
        stats = db.get_scan_statistics(start_date, end_date, limit)
        
        return {
            "success": True,
            "count": len(stats),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"获取扫描统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/scan/latest")
async def get_latest_scan_results(stock_code: Optional[str] = None):
    """
    获取最新一次扫描的结果
    
    Args:
        stock_code: 股票代码过滤
    """
    try:
        from models import get_scan_db
        
        db = get_scan_db()
        results = db.get_latest_scan_results(stock_code)
        
        return {
            "success": True,
            "count": len(results),
            "stocks": results
        }
        
    except Exception as e:
        logger.error(f"获取最新扫描结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/scan/persistent")
async def get_persistent_phase2_stocks(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_days: int = 3
):
    """
    获取持续出现在第二阶段的股票（多日复盘）
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        min_days: 最小出现天数
    """
    try:
        from models import get_scan_db
        
        db = get_scan_db()
        stocks = db.get_stock_appearance_count(start_date, end_date, min_days)
        
        return {
            "success": True,
            "count": len(stocks),
            "message": f"过去期间持续{min_days}天以上出现在第二阶段的股票",
            "stocks": stocks
        }
        
    except Exception as e:
        logger.error(f"获取持续强势股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CLI入口
def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="30周均线交易系统")
    parser.add_argument("--run", action="store_true", help="执行分析任务")
    parser.add_argument("--stock", type=str, help="分析单只股票")
    parser.add_argument("--serve", action="store_true", help="启动API服务")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务主机")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    
    args = parser.parse_args()
    
    if args.serve:
        # 启动服务
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port)
    
    elif args.run:
        # 执行分析任务
        asyncio.run(run_analysis_task())
    
    elif args.stock:
        # 分析单只股票
        async def analyze_one():
            ts = TradingSystem()
            try:
                result = await ts.analyze_single_stock(args.stock)
                if result:
                    print(f"\n股票: {result.stock_name} ({result.stock_code})")
                    print(f"阶段: {result.phase.name}")
                    print(f"信号:")
                    for s in result.signals:
                        print(f"  - {s.signal_type.value}: {s.reason[:100]}...")
                else:
                    print("分析失败")
            finally:
                await ts.close()
        
        asyncio.run(analyze_one())
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
