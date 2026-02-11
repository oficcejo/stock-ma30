"""
30周均线阶段分析引擎
基于史丹·温斯坦的阶段分析法
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from loguru import logger

from models import StockPhase, PhaseMetrics, StockData


@dataclass
class ConsolidationRange:
    """横盘区间"""
    start_idx: int
    end_idx: int
    high: float
    low: float
    avg_volume: float
    duration_weeks: int


class PhaseAnalyzer:
    """
    阶段分析器
    
    根据史丹·温斯坦的理论，股票走势分为四个阶段：
    - 第一阶段：底部横盘（冬天）- 30周均线走平
    - 第二阶段：上升趋势（春天/夏天）- 30周均线向上
    - 第三阶段：顶部横盘（秋天）- 30周均线走平
    - 第四阶段：下降趋势（冬天）- 30周均线向下
    """
    
    def __init__(
        self,
        ma_period: int = 30,           # 均线周期（30周）
        slope_threshold: float = 0.02,  # 斜率阈值（判断走平）
        consolidation_threshold: float = 0.15,  # 横盘阈值（15%波动范围）
        volume_threshold: float = 2.0    # 成交量阈值（突破需2倍以上）
    ):
        self.ma_period = ma_period
        self.slope_threshold = slope_threshold
        self.consolidation_threshold = consolidation_threshold
        self.volume_threshold = volume_threshold
    
    def calculate_ma30(self, df: pd.DataFrame) -> pd.Series:
        """计算30周均线"""
        return df["close"].rolling(window=self.ma_period, min_periods=20).mean()
    
    def calculate_ma_slope(self, ma_series: pd.Series, periods: int = 5) -> float:
        """
        计算均线斜率
        
        Args:
            ma_series: 均线序列
            periods: 计算斜率使用的周期数
        """
        if len(ma_series) < periods:
            return 0.0
        
        recent_ma = ma_series.tail(periods).dropna()
        if len(recent_ma) < 2:
            return 0.0
        
        # 使用线性回归计算斜率
        x = np.arange(len(recent_ma))
        y = recent_ma.values
        
        # 归一化斜率（相对于均线值）
        slope = np.polyfit(x, y, 1)[0]
        normalized_slope = slope / recent_ma.mean()
        
        return normalized_slope
    
    def get_ma_direction(self, slope: float) -> str:
        """根据斜率判断均线方向"""
        if slope > self.slope_threshold:
            return "up"
        elif slope < -self.slope_threshold:
            return "down"
        else:
            return "flat"
    
    def find_consolidation_ranges(
        self, 
        df: pd.DataFrame, 
        min_weeks: int = 8
    ) -> List[ConsolidationRange]:
        """
        寻找横盘区间
        
        Args:
            df: 股票数据DataFrame
            min_weeks: 最小横盘周数
        """
        if len(df) < min_weeks:
            return []
        
        ranges = []
        ma = df["ma30"].values
        close = df["close"].values
        volume = df["volume"].values
        
        # 使用滑动窗口寻找横盘区间
        window_size = min_weeks
        for i in range(len(df) - window_size + 1):
            window_close = close[i:i+window_size]
            window_ma = ma[i:i+window_size]
            window_volume = volume[i:i+window_size]
            
            # 检查是否横盘
            price_range = (window_close.max() - window_close.min()) / window_close.mean()
            ma_flat = np.std(window_ma) / np.mean(window_ma) < self.slope_threshold
            
            if price_range < self.consolidation_threshold and ma_flat:
                # 找到横盘区间
                consolidation = ConsolidationRange(
                    start_idx=i,
                    end_idx=i + window_size - 1,
                    high=float(window_close.max()),
                    low=float(window_close.min()),
                    avg_volume=float(np.mean(window_volume)),
                    duration_weeks=window_size
                )
                ranges.append(consolidation)
        
        return ranges
    
    def detect_breakout(
        self, 
        df: pd.DataFrame, 
        consolidation: ConsolidationRange
    ) -> Tuple[bool, bool]:
        """
        检测突破
        
        Returns:
            (向上突破, 成交量确认)
        """
        if len(df) <= consolidation.end_idx:
            return False, False
        
        # 获取突破后的数据
        breakout_data = df.iloc[consolidation.end_idx:]
        if len(breakout_data) < 2:
            return False, False
        
        # 检查是否向上突破阻力位
        resistance = consolidation.high
        breakout_price = breakout_data["close"].iloc[0]
        
        upward_breakout = breakout_price > resistance * 1.03  # 突破3%以上
        
        # 检查成交量
        if len(breakout_data) > 0:
            current_volume = breakout_data["volume"].iloc[0]
            volume_confirmed = current_volume > consolidation.avg_volume * self.volume_threshold
        else:
            volume_confirmed = False
        
        return upward_breakout, volume_confirmed
    
    def detect_breakdown(
        self, 
        df: pd.DataFrame, 
        consolidation: ConsolidationRange
    ) -> Tuple[bool, bool]:
        """
        检测跌破（向下突破）
        
        Returns:
            (向下突破, 成交量确认)
        """
        if len(df) <= consolidation.end_idx:
            return False, False
        
        breakdown_data = df.iloc[consolidation.end_idx:]
        if len(breakdown_data) < 2:
            return False, False
        
        support = consolidation.low
        breakdown_price = breakdown_data["close"].iloc[0]
        
        downward_breakdown = breakdown_price < support * 0.97  # 跌破3%以下
        
        if len(breakdown_data) > 0:
            current_volume = breakdown_data["volume"].iloc[0]
            volume_confirmed = current_volume > consolidation.avg_volume * self.volume_threshold
        else:
            volume_confirmed = False
        
        return downward_breakdown, volume_confirmed
    
    def analyze_phase(self, df: pd.DataFrame) -> Tuple[StockPhase, PhaseMetrics]:
        """
        分析股票当前阶段
        
        Args:
            df: 包含周线数据的DataFrame（至少150周数据）
            
        Returns:
            (阶段, 阶段指标)
        """
        if len(df) < self.ma_period:
            logger.warning(f"数据不足，需要至少{self.ma_period}周数据")
            return StockPhase.UNKNOWN, self._empty_metrics()
        
        # 计算30周均线
        df = df.copy()
        df["ma30"] = self.calculate_ma30(df)
        df["volume_ma"] = df["volume"].rolling(window=10).mean()
        
        # 获取最新数据
        latest = df.iloc[-1]
        current_price = latest["close"]
        current_ma = latest["ma30"]
        current_volume = latest["volume"]
        avg_volume = latest["volume_ma"]
        
        # 计算均线斜率和方向
        ma_slope = self.calculate_ma_slope(df["ma30"])
        ma_direction = self.get_ma_direction(ma_slope)
        
        # 计算价格与均线关系
        price_to_ma_ratio = current_price / current_ma if current_ma > 0 else 1.0
        
        # 计算成交量比率
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # 寻找横盘区间
        consolidation_ranges = self.find_consolidation_ranges(df)
        latest_consolidation = consolidation_ranges[-1] if consolidation_ranges else None
        
        # 判断阶段
        phase = self._determine_phase(
            df, 
            ma_direction, 
            price_to_ma_ratio,
            latest_consolidation
        )
        
        # 检测突破/跌破
        breakout_confirmed = False
        if latest_consolidation:
            upward, vol_confirm = self.detect_breakout(df, latest_consolidation)
            breakout_confirmed = upward and vol_confirm
        
        # 构建指标
        metrics = PhaseMetrics(
            ma30_slope=ma_slope,
            ma30_direction=ma_direction,
            price_to_ma_ratio=price_to_ma_ratio,
            consolidation_weeks=latest_consolidation.duration_weeks if latest_consolidation else 0,
            breakout_confirmed=breakout_confirmed,
            volume_confirmation=volume_ratio > self.volume_threshold
        )
        
        return phase, metrics
    
    def _determine_phase(
        self, 
        df: pd.DataFrame,
        ma_direction: str,
        price_to_ma_ratio: float,
        consolidation: Optional[ConsolidationRange]
    ) -> StockPhase:
        """确定股票阶段"""
        
        # 获取近期价格走势
        recent_prices = df["close"].tail(20).values
        price_trend = "up" if recent_prices[-1] > recent_prices[0] else "down"
        
        # 第二阶段：上升趋势
        if ma_direction == "up" and price_to_ma_ratio > 1.0:
            # 检查是否刚从横盘突破
            if consolidation and consolidation.end_idx >= len(df) - 5:
                return StockPhase.PHASE_2_RISING
            # 持续上涨
            return StockPhase.PHASE_2_RISING
        
        # 第四阶段：下降趋势
        if ma_direction == "down" and price_to_ma_ratio < 1.0:
            return StockPhase.PHASE_4_FALLING
        
        # 第一阶段：底部横盘
        if ma_direction == "flat" and price_to_ma_ratio <= 1.05:
            # 检查是否处于低位
            historical_low = df["close"].tail(100).min()
            if recent_prices[-1] < historical_low * 1.2:  # 在低位20%范围内
                return StockPhase.PHASE_1_BOTTOM
        
        # 第三阶段：顶部横盘
        if ma_direction == "flat" and price_to_ma_ratio >= 0.95:
            # 检查是否处于高位
            historical_high = df["close"].tail(100).max()
            if recent_prices[-1] > historical_high * 0.8:  # 在高位20%范围内
                return StockPhase.PHASE_3_TOP
        
        # 默认根据均线方向判断
        if ma_direction == "up":
            return StockPhase.PHASE_2_RISING
        elif ma_direction == "down":
            return StockPhase.PHASE_4_FALLING
        else:
            # 根据价格位置判断是底部还是顶部横盘
            mid_price = (df["close"].max() + df["close"].min()) / 2
            if recent_prices[-1] < mid_price:
                return StockPhase.PHASE_1_BOTTOM
            else:
                return StockPhase.PHASE_3_TOP
    
    def _empty_metrics(self) -> PhaseMetrics:
        """创建空指标"""
        return PhaseMetrics(
            ma30_slope=0.0,
            ma30_direction="flat",
            price_to_ma_ratio=1.0,
            consolidation_weeks=0,
            breakout_confirmed=False,
            volume_confirmation=False
        )
    
    def is_valid_buy_setup(
        self, 
        df: pd.DataFrame,
        metrics: PhaseMetrics
    ) -> Tuple[bool, str]:
        """
        检查是否是有效买入设置
        
        Returns:
            (是否有效, 原因)
        """
        latest = df.iloc[-1]
        
        # 条件1：30周均线向上
        if metrics.ma30_direction != "up":
            return False, "30周均线未向上"
        
        # 条件2：股价在均线上方
        if latest["close"] <= latest["ma30"]:
            return False, "股价未站上30周均线"
        
        # 条件3：成交量放大
        if not metrics.volume_confirmation:
            return False, "成交量未放大"
        
        # 条件4：突破确认
        if not metrics.breakout_confirmed:
            return False, "未确认有效突破"
        
        return True, "符合买入条件"
    
    def is_valid_sell_setup(
        self, 
        df: pd.DataFrame,
        metrics: PhaseMetrics
    ) -> Tuple[bool, str]:
        """
        检查是否是有效卖出设置
        
        Returns:
            (是否有效, 原因)
        """
        latest = df.iloc[-1]
        
        # 条件1：30周均线走平或向下
        if metrics.ma30_direction == "up":
            return False, "30周均线仍向上，继续持有"
        
        # 条件2：股价跌破均线
        if latest["close"] >= latest["ma30"]:
            return False, "股价未跌破30周均线"
        
        # 条件3：成交量异常（放量下跌）
        if metrics.volume_confirmation:
            return True, "放量下跌，建议卖出"
        
        return True, "趋势转弱，建议卖出"


# 便捷函数
def analyze_stock_phase(df: pd.DataFrame) -> Tuple[StockPhase, PhaseMetrics]:
    """分析股票阶段（便捷函数）"""
    analyzer = PhaseAnalyzer()
    return analyzer.analyze_phase(df)
