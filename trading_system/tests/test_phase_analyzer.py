"""
阶段分析器测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.phase_analyzer import PhaseAnalyzer
from models import StockPhase


def create_mock_data(phase_type: str, weeks: int = 150) -> pd.DataFrame:
    """创建模拟数据"""
    dates = [datetime.now() - timedelta(weeks=i) for i in range(weeks, 0, -1)]
    
    if phase_type == "rising":
        # 上升趋势：价格持续上涨
        prices = np.linspace(10, 25, weeks) + np.random.normal(0, 0.5, weeks)
    elif phase_type == "falling":
        # 下降趋势：价格持续下跌
        prices = np.linspace(25, 10, weeks) + np.random.normal(0, 0.5, weeks)
    elif phase_type == "bottom":
        # 底部横盘
        prices = np.ones(weeks) * 15 + np.random.normal(0, 0.3, weeks)
    elif phase_type == "top":
        # 顶部横盘
        prices = np.ones(weeks) * 25 + np.random.normal(0, 0.3, weeks)
    else:
        prices = np.ones(weeks) * 20 + np.random.normal(0, 1, weeks)
    
    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.02,
        "low": prices * 0.98,
        "close": prices,
        "volume": np.random.randint(1000000, 5000000, weeks),
        "amount": prices * np.random.randint(1000000, 5000000, weeks)
    })
    
    return df


def test_calculate_ma30():
    """测试30周均线计算"""
    analyzer = PhaseAnalyzer()
    df = create_mock_data("rising", weeks=50)
    
    ma30 = analyzer.calculate_ma30(df)
    
    assert len(ma30) == len(df)
    assert ma30.iloc[-1] > 0  # 最后一个值应该有效
    assert pd.isna(ma30.iloc[0])  # 前29个应该是NaN


def test_calculate_ma_slope():
    """测试均线斜率计算"""
    analyzer = PhaseAnalyzer()
    
    # 上升趋势
    rising_ma = pd.Series(np.linspace(10, 20, 30))
    slope = analyzer.calculate_ma_slope(rising_ma)
    assert slope > 0
    
    # 下降趋势
    falling_ma = pd.Series(np.linspace(20, 10, 30))
    slope = analyzer.calculate_ma_slope(falling_ma)
    assert slope < 0
    
    # 横盘
    flat_ma = pd.Series(np.ones(30) * 15)
    slope = analyzer.calculate_ma_slope(flat_ma)
    assert abs(slope) < 0.02


def test_get_ma_direction():
    """测试均线方向判断"""
    analyzer = PhaseAnalyzer()
    
    assert analyzer.get_ma_direction(0.05) == "up"
    assert analyzer.get_ma_direction(-0.05) == "down"
    assert analyzer.get_ma_direction(0.01) == "flat"


def test_analyze_phase_rising():
    """测试上升趋势阶段识别"""
    analyzer = PhaseAnalyzer()
    df = create_mock_data("rising", weeks=150)
    
    phase, metrics = analyzer.analyze_phase(df)
    
    assert phase == StockPhase.PHASE_2_RISING
    assert metrics.ma30_direction == "up"


def test_analyze_phase_falling():
    """测试下降趋势阶段识别"""
    analyzer = PhaseAnalyzer()
    df = create_mock_data("falling", weeks=150)
    
    phase, metrics = analyzer.analyze_phase(df)
    
    assert phase == StockPhase.PHASE_4_FALLING
    assert metrics.ma30_direction == "down"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
