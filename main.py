from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import requests
import re
import subprocess
import os
import tempfile
import asyncio

@register("kards_deck_screenshot", "YourName", "艾特机器人并发送卡组代码获取截图", "1.0.0")
class KardsDeckScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # Kards卡组构建器URL
        self.deck_builder_url = "https://www.kards.com/decks/deck-builder?hash="
        
        # 调整Kards卡组代码的正则模式
        self.deck_code_pattern = re.compile(r'%%[a-zA-Z0-9|;o0j4bQJKnW7X9AiR8F1]+')
        
        # 获取当前文件目录，构建puppeteer脚本路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_script_path = os.path.join(current_dir, "puppeteer.js")

    async def initialize(self):
        """插件初始化"""
        logger.info("Kards卡组截图截图插件已加载，等待艾特并发送卡组代码")
        
        # 检查截图截图脚本是否存在
        if not os.path.exists(self.screenshot_script_path):
            logger.warning(f"截图脚本不存在: {self.screenshot_script_path}")
            logger.warning("请确保puppeteer.js与main.py在同一目录")

    @filter.at_me()  # 只处理艾特机器人的消息
    async def handle_deck_request(self, event: AstrMessageEvent):
        """处理艾特消息中的卡组代码并生成截图"""
        try:
            # 从消息中提取卡组代码
            message_content = event.message_str
            match = self.deck_code_pattern.search(message_content)
            
            if match:
                deck_code = match.group(0)
                logger.info(f"收到艾特消息，识别到卡组代码: {deck_code}")
                
                # 生成完整的卡组构建器URL
                encoded_code = requests.utils.quote(deck_code)
                full_url = f"{self.deck_builder_url}{encoded_code}"
                logger.info(f"卡组URL: {full_url}")
                
                # 调用Puppeteer脚本生成截图
                image_data = await self.generate_screenshot(full_url)
                
                if image_data:
                    yield event.image_result(image_data)
                else:
                    yield event.plain_result("无法生成卡组图片，请稍后再试")
            else:
                # 如果没有识别到卡组代码，提示用户正确格式
                yield event.plain_result("请在艾特我时附上有效的Kards卡组代码，例如：\n@机器人 %%45|o0o5j4;bQbJbKnW7Kbs;7X9AiRbN;847Fo1")
                
        except Exception as e:
            logger.error(f"处理卡组时出错: {str(e)}")
            yield event.plain_result("处理请求时发生错误，请稍后再试")

    async def generate_screenshot(self, url):
        """调用Puppeteer脚本生成截图"""
        try:
            # 创建临时文件保存截图
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_filename = tmp_file.name
            
            # 检查Node.js是否安装
            node_check = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True
            )
            if node_check.returncode != 0:
                logger.error("未检测到Node.js，请先安装Node.js")
                return None
            
            # 调用外部Node.js脚本进行截图
            result = subprocess.run(
                ['node', self.screenshot_script_path, url, temp_filename],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                # 读取截图文件内容
                with open(temp_filename, 'rb') as f:
                    image_data = f.read()
                
                # 清理临时文件
                os.unlink(temp_filename)
                return image_data
            else:
                logger.error(f"截图脚本执行失败: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("截图超时")
            return None
        except Exception as e:
            logger.error(f"截图过程出错: {str(e)}")
            return None
        finally:
            # 确保临时文件被清理
            if 'temp_filename' in locals() and os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    async def terminate(self):
        """插件停止时调用"""
        logger.info("Kards卡组截图插件已停止")
    