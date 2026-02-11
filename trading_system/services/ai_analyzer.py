"""
AI分析服务模块
集成OpenAI兼容大模型进行市场分析
"""
import json
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from loguru import logger

from models import (
    AnalysisResult, MarketContext, AIAnalysisResponse,
    AIAnalysisRequest, StockPhase
)
from config import get_settings


class AIAnalyzer:
    """
    AI分析器
    
    使用OpenAI兼容的大模型API进行：
    1. 股票阶段分析解读
    2. 交易信号验证
    3. 风险因素识别
    4. 市场趋势预测
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.model = self.settings.openai_model
        
        # 只在配置了API key时初始化client
        if self.settings.openai_api_key:
            try:
                self.client = AsyncOpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_api_base
                )
            except Exception as e:
                logger.warning(f"初始化OpenAI客户端失败: {e}")
        else:
            logger.info("OpenAI API未配置，AI分析功能不可用")
    
    async def analyze_stock(
        self,
        analysis_result: AnalysisResult,
        market_context: Optional[MarketContext] = None,
        question: Optional[str] = None
    ) -> Optional[AIAnalysisResponse]:
        """
        分析单只股票
        
        Args:
            analysis_result: 阶段分析结果
            market_context: 市场环境
            question: 用户特定问题
            
        Returns:
            AI分析响应
        """
        if not self.settings.openai_api_key or not self.client:
            logger.warning("OpenAI API未配置，跳过AI分析")
            return None
        
        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(
                analysis_result,
                market_context,
                question
            )
            
            # 调用大模型
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # 解析响应
            content = response.choices[0].message.content
            parsed = self._parse_response(content, analysis_result.stock_code)
            
            return parsed
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return None
    
    async def validate_signal(
        self,
        analysis_result: AnalysisResult,
        signal_reason: str
    ) -> Dict[str, Any]:
        """
        验证交易信号
        
        让AI判断信号是否可靠，并给出置信度评分
        """
        if not self.settings.openai_api_key:
            return {"valid": True, "confidence": 0.5, "reason": "AI未配置"}
        
        try:
            prompt = f"""
请验证以下交易信号的可靠性：

股票: {analysis_result.stock_name} ({analysis_result.stock_code})
当前阶段: {self._phase_to_chinese(analysis_result.phase)}

技术指标:
- 30周均线斜率: {analysis_result.metrics.ma30_slope:.4f}
- 均线方向: {analysis_result.metrics.ma30_direction}
- 价格/均线比率: {analysis_result.metrics.price_to_ma_ratio:.2f}
- 横盘周数: {analysis_result.metrics.consolidation_weeks}
- 突破确认: {'是' if analysis_result.metrics.breakout_confirmed else '否'}
- 成交量确认: {'是' if analysis_result.metrics.volume_confirmation else '否'}

信号原因: {signal_reason}

请分析：
1. 这个信号是否符合史丹·温斯坦的交易原则？
2. 存在哪些潜在风险？
3. 给出置信度评分（0-100%）

请以JSON格式返回：
{{
    "valid": true/false,
    "confidence": 0.85,
    "risks": ["风险1", "风险2"],
    "suggestion": "建议"
}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的技术分析专家，精通史丹·温斯坦的阶段分析法。请客观分析交易信号。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0]
                else:
                    json_str = content
                
                result = json.loads(json_str.strip())
                return result
            except:
                return {
                    "valid": True,
                    "confidence": 0.6,
                    "risks": ["AI解析失败"],
                    "suggestion": content[:200]
                }
                
        except Exception as e:
            logger.error(f"信号验证失败: {e}")
            return {"valid": True, "confidence": 0.5, "reason": str(e)}
    
    async def batch_analyze(
        self,
        analysis_results: List[AnalysisResult],
        market_context: Optional[MarketContext] = None
    ) -> List[AIAnalysisResponse]:
        """批量分析多只股票"""
        responses = []
        for result in analysis_results:
            response = await self.analyze_stock(result, market_context)
            if response:
                responses.append(response)
        return responses
    
    def _build_analysis_prompt(
        self,
        analysis_result: AnalysisResult,
        market_context: Optional[MarketContext],
        question: Optional[str]
    ) -> str:
        """构建分析提示词"""
        
        phase_names = {
            StockPhase.PHASE_1_BOTTOM: "第一阶段（底部横盘/冬天）",
            StockPhase.PHASE_2_RISING: "第二阶段（上升趋势/春夏）",
            StockPhase.PHASE_3_TOP: "第三阶段（顶部横盘/秋天）",
            StockPhase.PHASE_4_FALLING: "第四阶段（下降趋势/冬天）"
        }
        
        prompt = f"""
请对以下股票进行专业分析：

## 股票信息
- 代码: {analysis_result.stock_code}
- 名称: {analysis_result.stock_name}
- 当前阶段: {phase_names.get(analysis_result.phase, '未知')}

## 技术指标
- 30周均线斜率: {analysis_result.metrics.ma30_slope:.4f}
- 均线方向: {analysis_result.metrics.ma30_direction}
- 价格/均线比率: {analysis_result.metrics.price_to_ma_ratio:.2f}
- 横盘周数: {analysis_result.metrics.consolidation_weeks}
- 突破确认: {'是' if analysis_result.metrics.breakout_confirmed else '否'}
- 成交量确认: {'是' if analysis_result.metrics.volume_confirmation else '否'}

## 市场环境
"""
        
        if market_context:
            prompt += f"""
- 大盘指数: {market_context.index_name} ({market_context.index_code})
- 大盘阶段: {phase_names.get(market_context.index_phase, '未知')}
- 市场情绪: {market_context.market_sentiment}
- 风险等级: {market_context.risk_level}
"""
        else:
            prompt += "未获取市场环境数据\n"
        
        prompt += """
## 分析要求
请基于史丹·温斯坦的《笑傲牛熊》阶段分析法，提供以下分析：

1. **阶段解读**: 当前阶段的特点和含义
2. **操作建议**: 根据当前阶段应该采取的操作
3. **关键价位**: 支撑位、阻力位、止损位
4. **风险因素**: 主要风险点和注意事项
5. **综合评级**: 买入/持有/观望/卖出

"""
        
        if question:
            prompt += f"\n## 用户问题\n{question}\n"
        
        prompt += """
请用中文回答，格式清晰，观点明确。
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位专业的股票技术分析专家，精通史丹·温斯坦的《笑傲牛熊》（How to Make Money in Stocks）中的阶段分析法。

你的分析基于以下核心原则：
1. 股票价格走势分为四个阶段：底部横盘、上升趋势、顶部横盘、下降趋势
2. 30周均线是判断趋势的关键指标
3. 成交量是确认突破有效性的重要依据
4. 顺势而为，不要与趋势作对
5. 严格的风险管理：止损保护、金字塔加仓

请提供客观、专业的分析，帮助投资者做出明智的决策。
"""
    
    def _parse_response(self, content: str, stock_code: str) -> AIAnalysisResponse:
        """解析AI响应"""
        
        # 提取建议
        recommendation = "观望"
        if "买入" in content or "BUY" in content.upper():
            recommendation = "买入"
        elif "卖出" in content or "SELL" in content.upper():
            recommendation = "卖出"
        elif "持有" in content or "HOLD" in content.upper():
            recommendation = "持有"
        
        # 提取信心度（从文本中尝试提取百分比）
        confidence = 0.7  # 默认
        import re
        confidence_match = re.search(r'(\d+)%', content)
        if confidence_match:
            confidence = int(confidence_match.group(1)) / 100
        
        # 提取风险因素
        risk_factors = []
        if "风险" in content:
            # 简单提取包含"风险"的句子
            lines = content.split('\n')
            for line in lines:
                if '风险' in line and len(line) > 10:
                    risk_factors.append(line.strip().lstrip('- ').lstrip('* '))
        
        if not risk_factors:
            risk_factors = ["请仔细阅读完整分析"]
        
        return AIAnalysisResponse(
            stock_code=stock_code,
            analysis_text=content,
            recommendation=recommendation,
            confidence=confidence,
            risk_factors=risk_factors[:5]  # 最多5个
        )
    
    def _phase_to_chinese(self, phase: StockPhase) -> str:
        """阶段转中文"""
        phase_names = {
            StockPhase.PHASE_1_BOTTOM: "第一阶段（底部）",
            StockPhase.PHASE_2_RISING: "第二阶段（上升）",
            StockPhase.PHASE_3_TOP: "第三阶段（顶部）",
            StockPhase.PHASE_4_FALLING: "第四阶段（下降）"
        }
        return phase_names.get(phase, "未知")


# 便捷函数
async def analyze_with_ai(
    analysis_result: AnalysisResult,
    market_context: Optional[MarketContext] = None
) -> Optional[AIAnalysisResponse]:
    """AI分析便捷函数"""
    analyzer = AIAnalyzer()
    return await analyzer.analyze_stock(analysis_result, market_context)
