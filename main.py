from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import re
import tempfile
import subprocess
import asyncio

@register(
    name="kards_deck_screenshot",
    author="xjsCHINA",
    description="识别卡组代码并生成截图（无需艾特）",
    version="1.0.0"
)
class KardsDeckScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 卡组构建器URL
        self.deck_builder_url = "https://www.kards.com/decks/deck-builder?hash="
        # Puppeteer脚本路径
        self.puppeteer_script = os.path.join(os.path.dirname(__file__), "puppeteer.js")
        
        # 卡组代码正则模式（根据实际格式调整）
        self.deck_code_pattern = re.compile(r'%%[A-Za-z0-9|;]+')

    async def initialize(self):
        """插件初始化"""
        if not os.path.exists(self.puppeteer_script):
            logger.error(f"未找到Puppeteer脚本: {self.puppeteer_script}")
        else:
            logger.info("Kards卡组截图插件初始化完成（无需艾特，直接识别卡组代码）")

    @filter.all()  # 监听所有消息
    async def on_message(self, event: AstrMessageEvent):
        """处理所有消息，直接识别卡组代码"""
        # 尝试提取卡组代码
        deck_code = self._extract_deck_code(event.message_str)
        if not deck_code:
            return  # 没有找到卡组代码，不处理
        
        # 生成并发送截图
        try:
            image_path = await self._generate_screenshot(deck_code)
            if image_path and os.path.isfile(image_path):
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                yield event.image_result(image_data)
                # 清理临时文件
                os.remove(image_path)
            else:
                yield event.plain_result("无法生成卡组截图，请检查代码是否正确")
        except Exception as e:
            logger.error(f"处理截图请求时出错: {str(e)}")
            # 可以选择不发送错误消息，避免干扰
            # yield event.plain_result("处理请求时发生错误")

    def _extract_deck_code(self, message: str) -> str:
        """从消息中提取卡组代码"""
        match = self.deck_code_pattern.search(message)
        if match:
            return match.group(0)
        return None

    async def _generate_screenshot(self, deck_code: str) -> str:
        """调用Puppeteer生成截图"""
        try:
            # 创建临时文件保存截图
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 构建完整URL
            full_url = f"{self.deck_builder_url}{deck_code}"
            
            # 调用Node.js脚本
            proc = await asyncio.create_subprocess_exec(
                'node', self.puppeteer_script, full_url, temp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Puppeteer执行失败: {stderr.decode('utf-8')}")
                return None
                
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
            else:
                logger.error(f"截图文件生成失败或为空: {temp_path}")
                return None
                
        except Exception as e:
            logger.error(f"生成截图时出错: {str(e)}")
            return None

    async def terminate(self):
        """插件终止时的清理工作"""
        logger.info("Kards卡组截图插件已停止")
    