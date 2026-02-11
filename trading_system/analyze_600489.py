"""分析中金黄金(600489)为何被判定为第二阶段"""
import asyncio
import sys
sys.path.insert(0, '.')
from core.data_collector import DataCollector
from core.phase_analyzer import PhaseAnalyzer, StockPhase

async def analyze():
    async with DataCollector() as collector:
        df = await collector.get_weekly_data('600489', weeks=35)
        if df is not None:
            print(f'数据条数: {len(df)}')
            print(f'\n最新价格: {df.iloc[-1]["close"]:.2f}')
            
            # 计算30周均线
            analyzer = PhaseAnalyzer()
            df['ma30'] = analyzer.calculate_ma30(df)
            
            print(f'30周均线: {df.iloc[-1]["ma30"]:.2f}')
            print(f'价均比: {df.iloc[-1]["close"]/df.iloc[-1]["ma30"]:.2%}')
            
            # 计算均线斜率
            slope = analyzer.calculate_ma_slope(df['ma30'])
            print(f'均线斜率: {slope:.4f} ({slope*100:.2f}%)')
            
            # 判断方向
            direction = analyzer.get_ma_direction(slope)
            print(f'均线方向: {direction}')
            
            # 分析阶段
            phase, metrics = analyzer.analyze_phase(df)
            print(f'\n判定阶段: {phase.name}')
            print(f'趋势强度: {metrics.ma30_slope:.4f}')
            print(f'突破确认: {metrics.breakout_confirmed}')
            
            # 显示最近10周数据
            print('\n最近10周收盘价和30周均线:')
            for i in range(-10, 0):
                row = df.iloc[i]
                ma_val = row["ma30"]
                if pd.notna(ma_val):
                    print(f'{row["date"].strftime("%Y-%m-%d")}: 收盘={row["close"]:7.2f} MA30={ma_val:7.2f}')

if __name__ == "__main__":
    import pandas as pd
    asyncio.run(analyze())
