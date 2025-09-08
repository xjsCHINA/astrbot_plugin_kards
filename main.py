from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import re
import tempfile
import subprocess
import asyncio

# 按照文档规范注册插件，包含必要的元信息
@register(
    name="kards_deck_screenshot",
    author="xjsCHINA",
    description="艾特机器人并发送卡组代码生成截图",
    version="1.0.0"
)
class KardsDeckScreenshotPlugin(Star):
    """Kards卡组截图插件
    
    当用户艾特机器人并发送包含特定格式的卡组代码时，
    自动生成卡组截图并回复。
    """
    def __init__(self, context: Context):
        super().__init__(context)
        # 获取机器人账号（用于艾特检测）
        self.bot_account = context.bot_config.account
        # 卡组构建器基础URL
        self.base_url = "https://www.kards.com/decks/deck-builder?hash="
        # Puppeteer脚本路径（文档推荐使用相对路径）
        self.script_path = os.path.join(os.path.dirname(__file__), "puppeteer.js")
        # 卡组代码正则匹配模式（文档建议明确业务规则）
        self.code_pattern = re.compile(r'%%[A-Za-z0-9|;]+')
        
        # 检查必要文件是否存在
        if not os.path.exists(self.script_path):
            logger.warning(f"未找到Puppeteer脚本: {self.script_path}")

    async def initialize(self):
        """插件初始化方法（文档要求的生命周期方法）"""
        logger.info("KardsDeckScreenshotPlugin 初始化完成")

    @filter.all()  # 监听所有消息，符合文档的事件过滤方式
    async def on_message(self, event: AstrMessageEvent):
        """消息处理主方法
        
        按照文档规范，处理逻辑应清晰分离
        """
        # 检查是否满足处理条件：被艾特且包含卡组代码
        if not self._is_triggered(event):
            return
        
        # 提取卡组代码
        deck_code = self._extract_deck_code(event.message_str)
        if not deck_code:
            return
        
        # 处理核心业务：生成截图并回复
        await self._process_deck_request(event, deck_code)

    def _is_triggered(self, event: AstrMessageEvent) -> bool:
        """判断是否触发插件处理
        
        私有方法以下划线开头，符合文档的代码规范
        """
        # 检查是否被艾特
        if not self._is_mentioned(event):
            return False
            
        # 检查消息中是否包含卡组代码
        if not self.code_pattern.search(event.message_str):
            return False
            
        return True

    def _is_mentioned(self, event: AstrMessageEvent) -> bool:
        """判断机器人是否被艾特
        
        实现文档中提到的艾特检测机制
        """
        # 优先检查mentions字段（文档推荐的方式）
        if hasattr(event, 'mentions') and isinstance(event.mentions, list):
            return self.bot_account in event.mentions
            
        # 兼容文本形式的艾特
        return str(self.bot_account) in event.message_str

    def _extract_deck_code(self, message: str) -> str:
        """提取卡组代码"""
        match = self.code_pattern.search(message)
        return match.group(0) if match else None

    async def _process_deck_request(self, event: AstrMessageEvent, deck_code: str):
        """处理卡组请求的核心逻辑"""
        try:
            # 生成截图
            image_path = await self._generate_screenshot(deck_code)
            
            if image_path and os.path.getsize(image_path) > 0:
                # 发送图片（符合文档的响应方式）
                with open(image_path, 'rb') as f:
                    yield event.image_result(f.read())
                # 清理临时文件
                os.remove(image_path)
            else:
                yield event.plain_result("生成卡组截图失败：未获取到有效图片")
                
        except Exception as e:
            logger.error(f"处理卡组请求出错: {str(e)}", exc_info=True)
            yield event.plain_result("处理请求时发生错误，请稍后再试")

    async def _generate_screenshot(self, deck_code: str) -> str:
        """调用Puppeteer生成截图"""
        try:
            # 创建临时文件（文档建议的临时文件处理方式）
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
            
            # 构建完整URL
            full_url = f"{self.base_url}{deck_code}"
            
            # 调用外部脚本（文档允许的外部程序调用方式）
            result = await asyncio.to_thread(
                subprocess.run,
                ['node', self.script_path, full_url, temp_path],
                capture_output=True,
                text=True,
                timeout=30  # 增加超时控制
            )
            
            if result.returncode != 0:
                logger.error(f"Puppeteer执行失败: {result.stderr}")
                return None
                
            return temp_path if os.path.exists(temp_path) else None
            
        except subprocess.TimeoutExpired:
            logger.error("生成截图超时")
            return None
        except Exception as e:
            logger.error(f"截图生成过程出错: {str(e)}")
            return None

    async def terminate(self):
        """插件终止方法（文档要求的生命周期方法）"""
        logger.info("KardsDeckScreenshotPlugin 已终止")
    