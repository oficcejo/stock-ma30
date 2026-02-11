"""测试TDX API可用接口"""
import asyncio
import httpx

API_BASE = "http://43.138.33.77:8080"

async def test_endpoint(client, endpoint, params=None):
    """测试单个接口"""
    try:
        url = f"{API_BASE}{endpoint}"
        resp = await client.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                return True, data.get('data')
            return False, f"API错误: {data.get('message')}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

async def main():
    async with httpx.AsyncClient() as client:
        # 测试各种可能的接口
        endpoints = [
            ('/api/codes', None, '股票代码列表'),
            ('/api/stock-codes', None, '股票代码列表2'),
            ('/api/etf', None, 'ETF列表'),
            ('/api/etf-codes', None, 'ETF代码'),
            ('/api/market-stats', None, '市场统计'),
            ('/api/market-count', None, '市场数量'),
            ('/api/index/all', None, '全部指数'),
            ('/api/kline', {'code': '000001', 'type': 'day'}, '日K线'),
            ('/api/quote', {'code': '000001'}, '行情'),
        ]
        
        print("=" * 60)
        print("测试TDX API接口")
        print("=" * 60)
        
        for endpoint, params, desc in endpoints:
            success, result = await test_endpoint(client, endpoint, params)
            status = "✓" if success else "✗"
            print(f"\n{status} {desc}")
            print(f"  接口: {endpoint}")
            if success:
                if isinstance(result, list):
                    print(f"  数据: 列表，共 {len(result)} 条")
                    if len(result) > 0:
                        print(f"  示例: {result[0]}")
                elif isinstance(result, dict):
                    print(f"  数据: 字典，键: {list(result.keys())[:5]}")
                else:
                    print(f"  数据: {type(result)}")
            else:
                print(f"  错误: {result}")

if __name__ == "__main__":
    asyncio.run(main())
