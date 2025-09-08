# Kards卡组截图插件（"!"开头触发）
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import re
import tempfile
import subprocess
import asyncio

# 插件注册（符合AstrBot规范）
@register(
    plugin_name="kards_deck_screenshot",
    author="xjsCHINA",
    description="发送'!+卡组代码'生成Kards截图（例：!%%45|o0o5j4...）",
    version="1.0.0"
)
class KardsDeckPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 卡组官方构建器地址
        self.deck_base_url = "https://www.kards.com/decks/deck-builder?hash="
        # Puppeteer脚本路径（与main.py同目录）
        self.puppeteer_script = os.path.join(
            os.path.dirname(__file__), "puppeteer.js"
        )
        # 关键：识别规则——以"!"开头 + 卡组代码（%%开头的字符）
        self.trigger_pattern = re.compile(r'^!%%[A-Za-z0-9|;]+')

    # 插件初始化
    async def initialize(self):
        logger.info("Kards卡组插件已加载（触发格式：!%%卡组代码）")

    # 监听所有消息，仅处理符合"!"开头规则的内容
    @filter.all()
    async def handle_deck_request(self, event: AstrMessageEvent):
        try:
            message_content = event.message_str.strip()  # 去除消息前后空格
            # 1. 检查是否以"!"开头且包含卡组代码
            match = self.trigger_pattern.match(message_content)
            if not match:
                return  # 不符合触发规则，不处理

            # 2. 提取卡组代码（去掉开头的"!"）
            deck_code = match.group(0)[1:]  # 例："!%%123..." → "%%123..."
            logger.info(f"触发卡组生成：{deck_code}")

            # 3. 调用Puppeteer生成截图
            screenshot_path = await self.generate_screenshot(deck_code)

            # 4. 发送截图给用户
            if screenshot_path and os.path.exists(screenshot_path):
                with open(screenshot_path, 'rb') as img_file:
                    img_data = img_file.read()
                yield event.image_result(img_data)  # 返回图片
                os.remove(screenshot_path)  # 清理临时文件
            else:
                yield event.plain_result("卡组截图生成失败，请检查代码是否正确")

        except Exception as e:
            logger.error(f"插件处理错误：{str(e)}")
            yield event.plain_result("处理请求时出错，请稍后再试")

    # 调用Puppeteer生成截图（核心功能）
    async def generate_screenshot(self, deck_code: str) -> str:
        try:
            # 创建临时文件保存截图（自动生成唯一文件名）
            temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_img.close()  # 关闭文件句柄，让Puppeteer可写入

            # 构建完整的卡组页面URL
            full_deck_url = f"{self.deck_base_url}{deck_code}"
            logger.info(f"访问卡组页面：{full_deck_url}")

            # 执行Puppeteer脚本（同步命令转异步，避免阻塞插件）
            result = await asyncio.to_thread(
                subprocess.run,
                ['node', self.puppeteer_script, full_deck_url, temp_img.name],
                capture_output=True,  # 捕获脚本输出（用于调试）
                text=True,
                timeout=60  # 超时时间60秒（防止卡死）
            )

            # 检查脚本执行结果
            if result.returncode == 0:
                logger.info(f"截图成功，保存路径：{temp_img.name}")
                return temp_img.name
            else:
                logger.error(f"Puppeteer执行失败：{result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("截图超时（超过60秒）")
            return None
        except Exception as e:
            logger.error(f"截图生成错误：{str(e)}")
            return None

    # 插件停止时的清理操作
    async def terminate(self):
        logger.info("Kards卡组插件已停止运行")
