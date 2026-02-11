"""
交易信号生成器
基于阶段分析结果生成买入/卖出信号
"""
import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime
from loguru import logger

from models import (
    StockPhase, SignalType, TradeSignal, 
    PhaseMetrics, MarketContext
)
from core.phase_analyzer import PhaseAnalyzer
from config import get_settings


class SignalGenerator:
    """
    交易信号生成器
    
    根据史丹·温斯坦的交易规则生成信号：
    - 买入信号：第二阶段突破 + 成交量放大 + 30周均线向上
    - 卖出信号：第三阶段/第四阶段 + 跌破均线 + 趋势转弱
    - 加仓信号：回调至30周均线附近止跌回升
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.analyzer = PhaseAnalyzer()
    
    def generate_signals(
        self,
        stock_code: str,
        stock_name: str,
        df: pd.DataFrame,
        market_context: Optional[MarketContext] = None
    ) -> List[TradeSignal]:
        """
        生成交易信号
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            df: 周线数据
            market_context: 市场环境
            
        Returns:
            交易信号列表
        """
        signals = []
        
        if len(df) < 30:
            logger.warning(f"{stock_code} 数据不足，无法生成信号")
            return signals
        
        # 分析阶段
        phase, metrics = self.analyzer.analyze_phase(df)
        
        latest = df.iloc[-1]
        current_price = latest["close"]
        ma30 = latest["ma30"]
        
        # 计算成交量比率
        avg_volume = df["volume"].tail(10).mean()
        volume_ratio = latest["volume"] / avg_volume if avg_volume > 0 else 1.0
        
        # 获取大盘趋势描述
        index_trend = self._get_index_trend_description(market_context)
        
        # 根据阶段生成信号
        if phase == StockPhase.PHASE_1_BOTTOM:
            # 第一阶段：观察
            signal = TradeSignal(
                stock_code=stock_code,
                stock_name=stock_name,
                signal_type=SignalType.WATCH,
                phase=phase,
                current_price=current_price,
                ma30_week=ma30,
                volume_ratio=volume_ratio,
                index_trend=index_trend,
                reason=f"处于第一阶段（底部横盘），30周均线走平。建议放入关注名单，等待突破信号。"
            )
            signals.append(signal)
            
        elif phase == StockPhase.PHASE_2_RISING:
            # 第二阶段：买入或持有
            if self._is_new_entry(df, metrics):
                # 新买入机会
                signal = TradeSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type=SignalType.BUY,
                    phase=phase,
                    current_price=current_price,
                    ma30_week=ma30,
                    volume_ratio=volume_ratio,
                    index_trend=index_trend,
                    reason=self._generate_buy_reason(df, metrics, True),
                    stop_loss=self._calculate_stop_loss(df, current_price),
                )
                signals.append(signal)
            elif self._is_add_position_opportunity(df):
                # 加仓机会
                signal = TradeSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type=SignalType.ADD_POSITION,
                    phase=phase,
                    current_price=current_price,
                    ma30_week=ma30,
                    volume_ratio=volume_ratio,
                    index_trend=index_trend,
                    reason=f"股价回调至30周均线附近止跌回升，符合金字塔加仓条件。"
                )
                signals.append(signal)
            else:
                # 持有
                signal = TradeSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type=SignalType.HOLD,
                    phase=phase,
                    current_price=current_price,
                    ma30_week=ma30,
                    volume_ratio=volume_ratio,
                    index_trend=index_trend,
                    reason=f"处于第二阶段（上升趋势），30周均线向上，继续持有。"
                )
                signals.append(signal)
                
        elif phase == StockPhase.PHASE_3_TOP:
            # 第三阶段：考虑卖出
            if self._should_sell(df, metrics):
                signal = TradeSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type=SignalType.SELL,
                    phase=phase,
                    current_price=current_price,
                    ma30_week=ma30,
                    volume_ratio=volume_ratio,
                    index_trend=index_trend,
                    reason=self._generate_sell_reason(df, metrics)
                )
                signals.append(signal)
            else:
                signal = TradeSignal(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    signal_type=SignalType.HOLD,
                    phase=phase,
                    current_price=current_price,
                    ma30_week=ma30,
                    volume_ratio=volume_ratio,
                    index_trend=index_trend,
                    reason=f"处于第三阶段（顶部横盘），密切关注卖出信号。"
                )
                signals.append(signal)
                
        elif phase == StockPhase.PHASE_4_FALLING:
            # 第四阶段：远离
            signal = TradeSignal(
                stock_code=stock_code,
                stock_name=stock_name,
                signal_type=SignalType.SELL,
                phase=phase,
                current_price=current_price,
                ma30_week=ma30,
                volume_ratio=volume_ratio,
                index_trend=index_trend,
                reason=f"处于第四阶段（下降趋势），30周均线向下，建议离场观望。"
            )
            signals.append(signal)
        
        return signals
    
    def _is_new_entry(self, df: pd.DataFrame, metrics: PhaseMetrics) -> bool:
        """判断是否是新买入机会"""
        # 检查是否刚突破
        if not metrics.breakout_confirmed:
            return False
        
        # 检查成交量
        if not metrics.volume_confirmation:
            return False
        
        # 检查均线方向
        if metrics.ma30_direction != "up":
            return False
        
        # 检查是否处于突破初期（最近3周内）
        recent_data = df.tail(3)
        if len(recent_data) < 3:
            return False
        
        # 价格应该在均线上方
        latest = df.iloc[-1]
        if latest["close"] <= latest["ma30"]:
            return False
        
        return True
    
    def _is_add_position_opportunity(self, df: pd.DataFrame) -> bool:
        """判断是否是加仓机会"""
        if len(df) < 10:
            return False
        
        # 获取最近数据
        recent = df.tail(5)
        
        # 检查是否回调到均线附近
        for idx in range(len(recent) - 1):
            row = recent.iloc[idx]
            # 价格接近均线（±3%）
            price_ma_ratio = row["close"] / row["ma30"]
            if 0.97 <= price_ma_ratio <= 1.03:
                # 下一周期上涨
                next_row = recent.iloc[idx + 1]
                if next_row["close"] > row["close"]:
                    return True
        
        return False
    
    def _should_sell(self, df: pd.DataFrame, metrics: PhaseMetrics) -> bool:
        """判断是否应该卖出"""
        latest = df.iloc[-1]
        
        # 条件1：均线走平或向下
        if metrics.ma30_direction == "up":
            return False
        
        # 条件2：股价跌破均线
        if latest["close"] >= latest["ma30"]:
            return False
        
        # 条件3：反弹无法站回均线
        # 检查最近几周
        recent = df.tail(4)
        below_ma_count = sum(recent["close"] < recent["ma30"])
        if below_ma_count >= 2:  # 至少2周在均线下方
            return True
        
        return False
    
    def _generate_buy_reason(
        self, 
        df: pd.DataFrame, 
        metrics: PhaseMetrics,
        is_breakout: bool
    ) -> str:
        """生成买入原因"""
        reasons = []
        
        if is_breakout:
            reasons.append("股价放量突破底部横盘区间")
        
        if metrics.ma30_direction == "up":
            reasons.append("30周均线开始向上拐头")
        
        if metrics.volume_confirmation:
            reasons.append("成交量明显放大，确认突破有效")
        
        latest = df.iloc[-1]
        if latest["close"] > latest["ma30"]:
            reasons.append("股价站稳30周均线上方")
        
        return "；".join(reasons) + "。符合史丹·温斯坦第二阶段买入条件。"
    
    def _generate_sell_reason(self, df: pd.DataFrame, metrics: PhaseMetrics) -> str:
        """生成卖出原因"""
        reasons = []
        latest = df.iloc[-1]
        
        if metrics.ma30_direction == "flat":
            reasons.append("30周均线走平")
        elif metrics.ma30_direction == "down":
            reasons.append("30周均线向下")
        
        if latest["close"] < latest["ma30"]:
            reasons.append("股价跌破30周均线")
        
        if metrics.volume_confirmation:
            reasons.append("成交量放大，资金出逃迹象")
        
        return "；".join(reasons) + "。趋势转弱，建议止盈或止损离场。"
    
    def _calculate_stop_loss(self, df: pd.DataFrame, entry_price: float) -> float:
        """计算止损价格"""
        # 找到最近的支撑位
        recent_lows = df["low"].tail(20)
        support_level = recent_lows.min()
        
        # 止损设在支撑位下方一点
        stop_loss = support_level * 0.98
        
        # 确保止损不超过8%
        max_stop = entry_price * (1 - self.settings.stop_loss_percent / 100)
        
        return max(stop_loss, max_stop)
    
    def _get_index_trend_description(
        self, 
        market_context: Optional[MarketContext]
    ) -> str:
        """获取大盘趋势描述"""
        if market_context is None:
            return "未获取大盘数据"
        
        phase_names = {
            StockPhase.PHASE_1_BOTTOM: "底部阶段",
            StockPhase.PHASE_2_RISING: "上升阶段",
            StockPhase.PHASE_3_TOP: "顶部阶段",
            StockPhase.PHASE_4_FALLING: "下降阶段"
        }
        
        phase_name = phase_names.get(market_context.index_phase, "未知")
        return f"{market_context.index_name}处于{phase_name}"
    
    def filter_signals_by_market(
        self,
        signals: List[TradeSignal],
        market_context: MarketContext
    ) -> List[TradeSignal]:
        """
        根据市场环境过滤信号
        
        规则：
        - 大盘第四阶段：过滤掉所有买入信号
        - 大盘第一阶段：谨慎买入
        """
        filtered = []
        
        for signal in signals:
            # 大盘第四阶段，不买入
            if (market_context.index_phase == StockPhase.PHASE_4_FALLING and 
                signal.signal_type == SignalType.BUY):
                logger.info(f"{signal.stock_code} 买入信号被过滤：大盘处于第四阶段")
                continue
            
            # 大盘第一阶段，谨慎处理
            if (market_context.index_phase == StockPhase.PHASE_1_BOTTOM and 
                signal.signal_type == SignalType.BUY):
                signal.reason += "【注意】大盘处于第一阶段，建议小仓位试探。"
            
            filtered.append(signal)
        
        return filtered


# 便捷函数
def generate_trade_signals(
    stock_code: str,
    stock_name: str,
    df: pd.DataFrame,
    market_context: Optional[MarketContext] = None
) -> List[TradeSignal]:
    """生成交易信号（便捷函数）"""
    generator = SignalGenerator()
    return generator.generate_signals(stock_code, stock_name, df, market_context)
