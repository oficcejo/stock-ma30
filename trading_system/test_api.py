"""
测试tdx-api连接
"""
import asyncio
import sys
sys.path.insert(0, '.')

from core.data_collector import DataCollector


async def test():
    print("=" * 50)
    print("测试 tdx-api 连接")
    print("=" * 50)
    
    async with DataCollector() as collector:
        # 测试服务器状态
        print("\n1. 测试服务器状态...")
        status = await collector.get_server_status()
        print(f"   连接状态: {'OK' if status.get('connected') else 'FAIL'}")
        if status.get('health'):
            print(f"   Health: {status['health']}")
        
        # 测试搜索
        print("\n2. 测试搜索股票...")
        search_results = await collector.search_stocks("平安")
        if search_results:
            print(f"   找到 {len(search_results)} 个结果")
            for item in search_results[:3]:
                print(f"   - {item.get('code')}: {item.get('name')}")
        else:
            print("   搜索无结果或API不支持")
        
        # 测试获取日线数据
        print("\n3. 测试获取日线数据 (000001 平安银行)...")
        df = await collector.get_daily_data("000001", days=30)
        if df is not None and len(df) > 0:
            print(f"   [OK] 获取到 {len(df)} 条日线数据")
            print(f"   最新数据: {df.iloc[-1].to_dict()}")
        else:
            print("   [FAIL] 获取失败")
        
        # 测试获取周线数据
        print("\n4. 测试获取周线数据 (000001 平安银行)...")
        weekly_df = await collector.get_weekly_data("000001", weeks=30)
        if weekly_df is not None and len(weekly_df) > 0:
            print(f"   [OK] 获取到 {len(weekly_df)} 条周线数据")
            print(f"   最新数据: {weekly_df.iloc[-1][['date', 'close', 'volume']].to_dict()}")
        else:
            print("   [FAIL] 获取失败")
        
        # 测试实时行情
        print("\n5. 测试获取实时行情 (000001)...")
        quote = await collector.get_realtime_quote("000001")
        if quote:
            print(f"   [OK] 获取成功: {quote}")
        else:
            print("   [FAIL] 获取失败或API不支持")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test())
