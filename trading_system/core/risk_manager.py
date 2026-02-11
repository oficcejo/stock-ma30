"""
风险管理模块
实现止损、仓位计算、金字塔加仓等功能
"""
from typing import Optional, List, Dict
from dataclasses import dataclass
from loguru import logger

from models import Position, RiskConfig, TradeSignal, SignalType
from config import get_settings


@dataclass
class PositionSizing:
    """仓位计算结果"""
    shares: int                 # 建议股数
    position_value: float       # 仓位金额
    risk_amount: float          # 风险金额
    risk_percent: float         # 风险比例
    stop_loss_price: float      # 止损价格


class RiskManager:
    """
    风险管理器
    
    遵循史丹·温斯坦的风险管理原则：
    1. 单笔交易亏损不超过总资金的2-3%
    2. 止损位只能上移，不能下移
    3. 金字塔加仓法：只在盈利时加仓，每次加仓量递减
    4. 分散投资：持有5-10只股票
    """
    
    def __init__(self, total_capital: float = 1000000.0):
        """
        Args:
            total_capital: 总资金（默认100万）
        """
        self.settings = get_settings()
        self.total_capital = total_capital
        self.config = RiskConfig(
            max_loss_percent=self.settings.max_loss_percent,
            stop_loss_percent=self.settings.stop_loss_percent,
            max_positions=10,
            single_position_max=20.0
        )
        self.positions: Dict[str, Position] = {}
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        confidence: float = 1.0
    ) -> PositionSizing:
        """
        计算仓位大小
        
        公式：仓位 = (总资金 × 最大亏损比例) / (入场价 - 止损价)
        
        Args:
            entry_price: 入场价格
            stop_loss_price: 止损价格
            confidence: 信心系数（0.5-1.5），影响仓位大小
        """
        # 计算每股风险
        risk_per_share = entry_price - stop_loss_price
        if risk_per_share <= 0:
            logger.error("止损价必须低于入场价")
            risk_per_share = entry_price * 0.08  # 默认8%止损
        
        # 计算最大可承受亏损金额
        max_risk_amount = self.total_capital * (self.config.max_loss_percent / 100)
        
        # 根据信心调整
        adjusted_risk = max_risk_amount * confidence
        
        # 计算股数（向下取整到100的倍数，A股习惯）
        shares = int(adjusted_risk / risk_per_share / 100) * 100
        if shares < 100:
            shares = 100  # 最少100股
        
        # 计算仓位金额
        position_value = shares * entry_price
        
        # 检查是否超过单只股票最大仓位
        max_position_value = self.total_capital * (self.config.single_position_max / 100)
        if position_value > max_position_value:
            shares = int(max_position_value / entry_price / 100) * 100
            position_value = shares * entry_price
        
        # 重新计算实际风险
        actual_risk = shares * risk_per_share
        actual_risk_percent = (actual_risk / self.total_capital) * 100
        
        return PositionSizing(
            shares=shares,
            position_value=position_value,
            risk_amount=actual_risk,
            risk_percent=actual_risk_percent,
            stop_loss_price=stop_loss_price
        )
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        support_level: Optional[float] = None,
        atr: Optional[float] = None
    ) -> float:
        """
        计算止损价格
        
        优先级：
        1. 如果有支撑位，设在支撑位下方
        2. 如果有ATR，使用ATR倍数
        3. 使用固定百分比止损
        """
        if support_level and support_level < entry_price:
            # 设在支撑位下方2%
            stop_loss = support_level * 0.98
        elif atr:
            # 使用2倍ATR
            stop_loss = entry_price - 2 * atr
        else:
            # 使用固定百分比
            stop_loss = entry_price * (1 - self.config.stop_loss_percent / 100)
        
        # 确保止损不超过最大允许亏损
        max_stop = entry_price * (1 - self.config.stop_loss_percent / 100)
        return max(stop_loss, max_stop)
    
    def update_stop_loss(
        self,
        position: Position,
        current_price: float,
        new_support_level: Optional[float] = None
    ) -> float:
        """
        更新止损价格（移动止损）
        
        原则：止损只能上移，不能下移
        """
        # 计算新的止损候选
        if new_support_level and new_support_level > position.stop_loss:
            candidate_stop = new_support_level * 0.98
        else:
            # 使用跟踪止损（例如，价格涨10%，止损上移5%）
            profit_percent = (current_price - position.entry_price) / position.entry_price
            if profit_percent > 0.1:  # 盈利超过10%
                candidate_stop = position.entry_price + (current_price - position.entry_price) * 0.5
            else:
                return position.stop_loss
        
        # 确保止损只上移
        new_stop_loss = max(candidate_stop, position.stop_loss)
        
        return new_stop_loss
    
    def calculate_pyramid_add_position(
        self,
        position: Position,
        current_price: float,
        add_price: float
    ) -> Optional[PositionSizing]:
        """
        计算金字塔加仓
        
        原则：
        1. 只在盈利时加仓
        2. 每次加仓量递减（如：第一次100%，第二次50%，第三次25%）
        3. 新的止损统一上移
        """
        # 检查是否盈利
        if current_price <= position.entry_price:
            logger.info("未盈利，不建议加仓")
            return None
        
        # 计算已加仓次数
        add_count = getattr(position, 'add_count', 0)
        
        # 计算本次加仓比例（递减）
        add_ratio = 1.0 / (2 ** add_count)  # 1, 0.5, 0.25, ...
        
        # 计算原始仓位大小
        original_sizing = self.calculate_position_size(
            position.entry_price,
            position.stop_loss
        )
        
        # 本次加仓股数
        add_shares = int(original_sizing.shares * add_ratio / 100) * 100
        if add_shares < 100:
            return None
        
        # 计算新的统一止损（设在本次加仓价下方）
        new_stop_loss = add_price * 0.95  # 5%止损
        
        # 确保新止损高于原止损
        new_stop_loss = max(new_stop_loss, position.stop_loss)
        
        position_value = add_shares * add_price
        risk_amount = add_shares * (add_price - new_stop_loss)
        
        return PositionSizing(
            shares=add_shares,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_percent=(risk_amount / self.total_capital) * 100,
            stop_loss_price=new_stop_loss
        )
    
    def check_risk_limits(self, positions: List[Position]) -> Dict[str, any]:
        """
        检查风险限制
        
        Returns:
            风险检查报告
        """
        total_market_value = sum(p.market_value for p in positions)
        total_profit_loss = sum(p.profit_loss for p in positions)
        
        # 计算集中度
        if total_market_value > 0:
            max_position_percent = max(p.market_value for p in positions) / total_market_value * 100
        else:
            max_position_percent = 0
        
        # 检查各项限制
        checks = {
            "total_positions": len(positions),
            "max_positions_allowed": self.config.max_positions,
            "positions_ok": len(positions) <= self.config.max_positions,
            
            "max_concentration": max_position_percent,
            "max_concentration_allowed": self.config.single_position_max,
            "concentration_ok": max_position_percent <= self.config.single_position_max,
            
            "total_exposure": (total_market_value / self.total_capital) * 100,
            "total_pnl": total_profit_loss,
            "total_pnl_percent": (total_profit_loss / self.total_capital) * 100
        }
        
        return checks
    
    def should_take_profit(
        self,
        position: Position,
        current_phase: str,
        rsi: Optional[float] = None
    ) -> bool:
        """
        判断是否该止盈
        
        条件：
        1. 进入第三阶段（顶部横盘）
        2. 跌破30周均线
        3. RSI超买（>70）
        """
        profit_percent = position.profit_loss_percent
        
        # 已经盈利，进入第三阶段
        if current_phase == "PHASE_3_TOP" and profit_percent > 10:
            return True
        
        # RSI超买
        if rsi and rsi > 70 and profit_percent > 15:
            return True
        
        return False
    
    def apply_risk_management(
        self,
        signal: TradeSignal,
        current_price: float,
        support_level: Optional[float] = None
    ) -> TradeSignal:
        """
        对信号应用风险管理
        
        计算止损价、仓位大小等
        """
        if signal.signal_type == SignalType.BUY:
            # 计算止损价
            stop_loss = self.calculate_stop_loss(
                current_price,
                support_level
            )
            
            # 计算仓位
            sizing = self.calculate_position_size(current_price, stop_loss)
            
            # 更新信号
            signal.stop_loss = stop_loss
            signal.position_size = sizing.shares
            
            # 添加风险信息到原因
            signal.reason += f"\n【风险管理】建议仓位{sizing.shares}股（约{sizing.position_value:,.0f}元），"
            signal.reason += f"止损价¥{stop_loss:.2f}，风险{sizing.risk_percent:.2f}%"
            
        elif signal.signal_type == SignalType.ADD_POSITION:
            # 查找现有持仓
            position = self.positions.get(signal.stock_code)
            if position:
                add_sizing = self.calculate_pyramid_add_position(
                    position,
                    current_price,
                    current_price
                )
                if add_sizing:
                    signal.position_size = add_sizing.shares
                    signal.stop_loss = add_sizing.stop_loss_price
                    signal.reason += f"\n【加仓建议】建议加仓{add_sizing.shares}股，"
                    signal.reason += f"统一止损价上调至¥{add_sizing.stop_loss_price:.2f}"
        
        return signal
    
    def get_position_summary(self) -> str:
        """获取持仓摘要"""
        if not self.positions:
            return "当前无持仓"
        
        total_value = sum(p.market_value for p in self.positions.values())
        total_pnl = sum(p.profit_loss for p in self.positions.values())
        
        summary = f"持仓概况：{len(self.positions)}只股票，"
        summary += f"总市值¥{total_value:,.0f}，"
        summary += f"总盈亏¥{total_pnl:,.0f}({total_pnl/self.total_capital*100:.2f}%)"
        
        return summary


# 便捷函数
def calculate_position(
    entry_price: float,
    stop_loss: float,
    total_capital: float = 1000000.0,
    max_loss_percent: float = 2.0
) -> int:
    """计算仓位（便捷函数）"""
    risk_per_share = entry_price - stop_loss
    if risk_per_share <= 0:
        return 0
    
    max_risk = total_capital * (max_loss_percent / 100)
    shares = int(max_risk / risk_per_share / 100) * 100
    
    return max(shares, 100)
