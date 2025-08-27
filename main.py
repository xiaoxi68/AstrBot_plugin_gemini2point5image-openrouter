from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from .utils.ttp import generate_image_openrouter
from .utils.file_send_server import send_file

@register("gemini-25-image-openrouter", "喵喵", "使用openrouter的免费api生成图片", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context,config: dict):
        super().__init__(context)
        self.openrouter_api_key = config.get("openrouter_api_key")
        self.nap_server_address = config.get("nap_server_address")
        self.nap_server_port = config.get("nap_server_port")

    @llm_tool(name="pic-gen")
    async def pic_gen(self, event: AstrMessageEvent, image_description: str) -> str:
        """
            When a user requires image generation or drawing, and asks you to create an image,
            or when you need to create a drawing to demonstrate or present something to the user,
            call this function. If the image description provided by the user is not in English,
            translate it into English and reformat it.

            Args:
            - image_description (string): Image description provided by the user, which will be enriched autonomously.
        """
        openrouter_api_key = self.openrouter_api_key
        nap_server_address = self.nap_server_address
        nap_server_port = self.nap_server_port

        # 调用生成图像的函数
        image_url, image_path = await generate_image_openrouter(image_description, openrouter_api_key)
        image_path = await send_file(image_path, HOST=nap_server_address, PORT=nap_server_port) if self.nap_server_address != "localhost" else image_path
        # 返回生成的图像
        chain = [Image.fromFileSystem(image_path)]
        yield event.chain_result(chain)
