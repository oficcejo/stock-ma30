"""
通知服务模块
支持钉钉和飞书Webhook推送
"""
import json
import hmac
import hashlib
import base64
import urllib.parse
import httpx
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger

from models import TradeSignal, AIAnalysisResponse
from config import get_settings


class NotifierService(ABC):
    """通知服务基类"""
    
    @abstractmethod
    async def send_text(self, text: str, title: Optional[str] = None) -> bool:
        """发送文本消息"""
        pass
    
    @abstractmethod
    async def send_markdown(self, title: str, content: str) -> bool:
        """发送Markdown消息"""
        pass
    
    async def send_trade_signal(self, signal: TradeSignal) -> bool:
        """发送交易信号"""
        text = signal.to_notification_text()
        return await self.send_markdown(
            title=f"交易信号: {signal.stock_name}",
            content=text
        )
    
    async def send_ai_analysis(self, analysis: AIAnalysisResponse) -> bool:
        """发送AI分析结果"""
        content = f"""
# AI分析报告: {analysis.stock_code}

{analysis.analysis_text}

---
**建议**: {analysis.recommendation}
**信心度**: {analysis.confidence:.1%}

**风险因素**:
"""
        for factor in analysis.risk_factors:
            content += f"- {factor}\n"
        
        content += f"\n⏰ 分析时间: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_markdown(
            title=f"AI分析: {analysis.stock_code}",
            content=content
        )


class DingTalkNotifier(NotifierService):
    """钉钉通知器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.webhook_url = self.settings.dingtalk_webhook_url
        self.secret = self.settings.dingtalk_secret
        self.client = httpx.AsyncClient(timeout=10.0)
    
    def _generate_sign(self, timestamp: str) -> str:
        """生成钉钉签名"""
        if not self.secret:
            return ""
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    async def send_text(self, text: str, title: Optional[str] = None) -> bool:
        """发送文本消息"""
        if not self.webhook_url:
            logger.warning("钉钉Webhook未配置")
            return False
        
        try:
            timestamp = str(round(datetime.now().timestamp() * 1000))
            sign = self._generate_sign(timestamp)
            
            url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": text
                }
            }
            
            response = await self.client.post(url, json=payload)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info("钉钉消息发送成功")
                return True
            else:
                logger.error(f"钉钉消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"钉钉消息发送异常: {e}")
            return False
    
    async def send_markdown(self, title: str, content: str) -> bool:
        """发送Markdown消息"""
        if not self.webhook_url:
            logger.warning("钉钉Webhook未配置")
            return False
        
        try:
            timestamp = str(round(datetime.now().timestamp() * 1000))
            sign = self._generate_sign(timestamp)
            
            url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": content
                }
            }
            
            response = await self.client.post(url, json=payload)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"钉钉Markdown消息发送成功: {title}")
                return True
            else:
                logger.error(f"钉钉Markdown消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"钉钉Markdown消息发送异常: {e}")
            return False
    
    async def send_action_card(
        self, 
        title: str, 
        markdown: str, 
        single_title: str = "查看详情",
        single_url: str = ""
    ) -> bool:
        """发送ActionCard消息（带按钮）"""
        if not self.webhook_url:
            logger.warning("钉钉Webhook未配置")
            return False
        
        try:
            timestamp = str(round(datetime.now().timestamp() * 1000))
            sign = self._generate_sign(timestamp)
            
            url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            
            payload = {
                "msgtype": "action_card",
                "action_card": {
                    "title": title,
                    "markdown": markdown,
                    "single_title": single_title,
                    "single_url": single_url
                }
            }
            
            response = await self.client.post(url, json=payload)
            result = response.json()
            
            return result.get("errcode") == 0
            
        except Exception as e:
            logger.error(f"钉钉ActionCard发送异常: {e}")
            return False


class FeishuNotifier(NotifierService):
    """飞书通知器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.webhook_url = self.settings.feishu_webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send_text(self, text: str, title: Optional[str] = None) -> bool:
        """发送文本消息"""
        if not self.webhook_url:
            logger.warning("飞书Webhook未配置")
            return False
        
        try:
            content = text
            if title:
                content = f"**{title}**\n\n{text}"
            
            payload = {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }
            
            response = await self.client.post(self.webhook_url, json=payload)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("飞书消息发送成功")
                return True
            else:
                logger.error(f"飞书消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False
    
    async def send_markdown(self, title: str, content: str) -> bool:
        """发送Markdown消息"""
        if not self.webhook_url:
            logger.warning("飞书Webhook未配置")
            return False
        
        try:
            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": content
                            }
                        }
                    ]
                }
            }
            
            response = await self.client.post(self.webhook_url, json=payload)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"飞书Markdown消息发送成功: {title}")
                return True
            else:
                logger.error(f"飞书Markdown消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"飞书Markdown消息发送异常: {e}")
            return False
    
    async def send_rich_text(
        self,
        title: str,
        content: List[Dict[str, Any]]
    ) -> bool:
        """发送富文本消息"""
        if not self.webhook_url:
            logger.warning("飞书Webhook未配置")
            return False
        
        try:
            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": content
                        }
                    }
                }
            }
            
            response = await self.client.post(self.webhook_url, json=payload)
            result = response.json()
            
            return result.get("code") == 0
            
        except Exception as e:
            logger.error(f"飞书富文本消息发送异常: {e}")
            return False


class MultiNotifier(NotifierService):
    """多通道通知器（同时发送到多个平台）"""
    
    def __init__(self):
        self.notifiers: List[NotifierService] = []
        
        # 初始化钉钉
        if get_settings().dingtalk_webhook_url:
            self.notifiers.append(DingTalkNotifier())
        
        # 初始化飞书
        if get_settings().feishu_webhook_url:
            self.notifiers.append(FeishuNotifier())
    
    async def send_text(self, text: str, title: Optional[str] = None) -> bool:
        """发送文本消息到所有平台"""
        results = []
        for notifier in self.notifiers:
            result = await notifier.send_text(text, title)
            results.append(result)
        return any(results)  # 至少一个成功
    
    async def send_markdown(self, title: str, content: str) -> bool:
        """发送Markdown消息到所有平台"""
        results = []
        for notifier in self.notifiers:
            result = await notifier.send_markdown(title, content)
            results.append(result)
        return any(results)
    
    async def send_batch_signals(self, signals: List[TradeSignal]) -> bool:
        """批量发送交易信号"""
        if not signals:
            return True
        
        # 生成汇总报告
        buy_signals = [s for s in signals if s.signal_type.value == "BUY"]
        sell_signals = [s for s in signals if s.signal_type.value == "SELL"]
        
        summary = f"""
# 📊 交易信号汇总报告

**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**买入信号**: {len(buy_signals)}只
**卖出信号**: {len(sell_signals)}只

---

"""
        
        if buy_signals:
            summary += "## 🟢 买入信号\n\n"
            for s in buy_signals:
                summary += f"- **{s.stock_name}** ({s.stock_code}): ¥{s.current_price:.2f}\n"
        
        if sell_signals:
            summary += "\n## 🔴 卖出信号\n\n"
            for s in sell_signals:
                summary += f"- **{s.stock_name}** ({s.stock_code}): ¥{s.current_price:.2f}\n"
        
        return await self.send_markdown("交易信号汇总", summary)


# 便捷函数
async def notify_signal(signal: TradeSignal) -> bool:
    """发送交易信号通知（便捷函数）"""
    notifier = MultiNotifier()
    return await notifier.send_trade_signal(signal)


async def notify_text(text: str, title: Optional[str] = None) -> bool:
    """发送文本通知（便捷函数）"""
    notifier = MultiNotifier()
    return await notifier.send_text(text, title)
