"""
SQLite数据库模块
用于存储扫描历史记录
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import os


@dataclass
class ScanRecord:
    """扫描记录"""
    id: Optional[int]
    scan_date: str
    stock_code: str
    stock_name: str
    phase: str
    current_price: float
    ma30: float
    trend_strength: float
    volume_ratio: float
    weeks_in_phase2: int
    breakout_confirmed: bool
    filter_config: str  # JSON字符串


class ScanDatabase:
    """扫描结果数据库"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径，默认在data目录下
        """
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'scan_history.db')
        
        self.db_path = db_path
        self._init_db()
        logger.info(f"扫描数据库初始化完成: {db_path}")
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 扫描记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,
                    scan_batch_id TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    current_price REAL,
                    ma30 REAL,
                    trend_strength REAL,
                    volume_ratio REAL,
                    weeks_in_phase2 INTEGER,
                    breakout_confirmed BOOLEAN,
                    filter_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 扫描统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,
                    scan_batch_id TEXT NOT NULL,
                    total_stocks INTEGER,
                    valid_stocks INTEGER,
                    phase2_count INTEGER,
                    filter_config TEXT,
                    duration_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scan_date ON scan_records(scan_date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_code ON scan_records(stock_code)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_batch_id ON scan_records(scan_batch_id)
            ''')
            
            conn.commit()
    
    def save_scan_results(
        self, 
        stocks: List[Dict], 
        filter_config: Dict,
        statistics: Dict,
        duration_seconds: int = 0
    ) -> str:
        """
        保存扫描结果
        
        Args:
            stocks: 扫描得到的第二阶段股票列表
            filter_config: 过滤配置
            statistics: 统计信息
            duration_seconds: 扫描耗时
            
        Returns:
            scan_batch_id: 批次ID
        """
        scan_date = datetime.now().strftime('%Y-%m-%d')
        scan_batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        filter_json = json.dumps(filter_config, ensure_ascii=False)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 保存统计信息
            cursor.execute('''
                INSERT INTO scan_statistics 
                (scan_date, scan_batch_id, total_stocks, valid_stocks, 
                 phase2_count, filter_config, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_date,
                scan_batch_id,
                statistics.get('total_stocks', 0),
                statistics.get('valid_stocks', 0),
                len(stocks),
                filter_json,
                duration_seconds
            ))
            
            # 保存股票记录
            for stock in stocks:
                cursor.execute('''
                    INSERT INTO scan_records 
                    (scan_date, scan_batch_id, stock_code, stock_name, phase,
                     current_price, ma30, trend_strength, volume_ratio,
                     weeks_in_phase2, breakout_confirmed, filter_config)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_date,
                    scan_batch_id,
                    stock.get('code', ''),
                    stock.get('name', ''),
                    stock.get('phase', ''),
                    stock.get('current_price', 0.0),
                    stock.get('ma30', 0.0),
                    stock.get('trend_strength', 0.0),
                    stock.get('volume_ratio', 1.0),
                    stock.get('weeks_in_phase2', 0),
                    stock.get('breakout_confirmed', False),
                    filter_json
                ))
            
            conn.commit()
        
        logger.info(f"扫描结果已保存，批次ID: {scan_batch_id}，共 {len(stocks)} 只股票")
        return scan_batch_id
    
    def get_scan_history(
        self, 
        start_date: str = None, 
        end_date: str = None,
        stock_code: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取扫描历史
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            stock_code: 股票代码过滤
            limit: 返回数量限制
            
        Returns:
            扫描记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM scan_records WHERE 1=1'
            params = []
            
            if start_date:
                query += ' AND scan_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND scan_date <= ?'
                params.append(end_date)
            if stock_code:
                query += ' AND stock_code = ?'
                params.append(stock_code)
            
            query += ' ORDER BY scan_date DESC, id DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_scan_statistics(
        self,
        start_date: str = None,
        end_date: str = None,
        limit: int = 30
    ) -> List[Dict]:
        """
        获取扫描统计历史
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            
        Returns:
            统计记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM scan_statistics WHERE 1=1'
            params = []
            
            if start_date:
                query += ' AND scan_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND scan_date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY scan_date DESC, created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_stock_appearance_count(
        self,
        start_date: str = None,
        end_date: str = None,
        min_appearances: int = 2
    ) -> List[Dict]:
        """
        获取股票出现频次统计（持续出现在第二阶段的股票）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            min_appearances: 最小出现次数
            
        Returns:
            股票出现频次列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT stock_code, stock_name, COUNT(DISTINCT scan_date) as appearance_count,
                       AVG(current_price) as avg_price, AVG(trend_strength) as avg_strength
                FROM scan_records
                WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += ' AND scan_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND scan_date <= ?'
                params.append(end_date)
            
            query += '''
                GROUP BY stock_code, stock_name
                HAVING appearance_count >= ?
                ORDER BY appearance_count DESC, avg_strength DESC
            '''
            params.append(min_appearances)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_latest_scan_results(self, stock_code: str = None) -> List[Dict]:
        """
        获取最新一次扫描的结果
        
        Args:
            stock_code: 股票代码过滤
            
        Returns:
            最新扫描结果
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取最新批次ID
            cursor.execute(
                'SELECT scan_batch_id FROM scan_statistics ORDER BY created_at DESC LIMIT 1'
            )
            row = cursor.fetchone()
            
            if not row:
                return []
            
            latest_batch = row['scan_batch_id']
            
            query = 'SELECT * FROM scan_records WHERE scan_batch_id = ?'
            params = [latest_batch]
            
            if stock_code:
                query += ' AND stock_code = ?'
                params.append(stock_code)
            
            query += ' ORDER BY trend_strength DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def delete_old_records(self, days: int = 90) -> int:
        """
        删除旧记录
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        cutoff_date = datetime.now()
        for _ in range(days):
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - 1) if cutoff_date.day > 1 else cutoff_date
        
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM scan_records WHERE scan_date < ?', (cutoff_str,))
            records_deleted = cursor.rowcount
            
            cursor.execute('DELETE FROM scan_statistics WHERE scan_date < ?', (cutoff_str,))
            stats_deleted = cursor.rowcount
            
            conn.commit()
        
        logger.info(f"删除旧记录: {records_deleted} 条扫描记录, {stats_deleted} 条统计记录")
        return records_deleted + stats_deleted


# 全局数据库实例
_db_instance: Optional[ScanDatabase] = None


def get_scan_db() -> ScanDatabase:
    """获取数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = ScanDatabase()
    return _db_instance
