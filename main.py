from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from .utils.ttp import generate_image_openrouter
from .utils.file_send_server import send_file

@register("gemini-25-image-openrouter", "喵喵", "使用openrouter的免费api生成图片", "1.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context,config: dict):
        super().__init__(context)
        self.openrouter_api_key = config.get("openrouter_api_key")
        self.nap_server_address = config.get("nap_server_address")
        self.nap_server_port = config.get("nap_server_port")

    @llm_tool(name="gemini-pic-gen")
    async def pic_gen(self, event: AstrMessageEvent, image_description: str, use_reference_images: bool = True) -> str:
        """
            Generate or modify images using Gemini model via OpenRouter API.
            
            When a user requires image generation or drawing, call this function.
            If use_reference_images is True and the user has provided images in their message,
            those images will be used as reference for generation or modification.
            If no images are provided or use_reference_images is False, pure text-to-image generation will be performed.

            Args:
            - image_description (string): Description of the image to generate. Translate to English if needed.
            - use_reference_images (bool): Whether to use images from user's message as reference. Default True.
        """
        openrouter_api_key = self.openrouter_api_key
        nap_server_address = self.nap_server_address
        nap_server_port = self.nap_server_port

        # 根据参数决定是否使用参考图片
        input_images = []
        if use_reference_images:
            # 从当前对话上下文中获取图片信息
            if hasattr(event, 'message_obj') and event.message_obj and hasattr(event.message_obj, 'message'):
                for comp in event.message_obj.message:
                    if isinstance(comp, Image):
                        try:
                            base64_data = await comp.convert_to_base64()
                            input_images.append(base64_data)
                        except Exception as e:
                            logger.warning(f"转换参考图片到base64失败: {e}")
            
            # 记录使用的图片数量
            if input_images:
                logger.info(f"使用了 {len(input_images)} 张参考图片进行图像生成")
            else:
                logger.info("未找到参考图片，执行纯文本图像生成")

        # 调用生成图像的函数
        try:
            image_url, image_path = await generate_image_openrouter(
                image_description, 
                openrouter_api_key, 
                input_images=input_images
            )
            
            if not image_url or not image_path:
                # 生成失败，发送错误消息
                error_chain = [Plain("图像生成失败，请检查API配置和网络连接。")]
                yield event.chain_result(error_chain)
                return
            
            # 处理文件传输
            if self.nap_server_address and self.nap_server_address != "localhost":
                image_path = await send_file(image_path, HOST=nap_server_address, PORT=nap_server_port)
            
            # 返回生成的图像
            chain = [Image.fromFileSystem(image_path)]
            yield event.chain_result(chain)
                
        except Exception as e:
            logger.error(f"图像生成过程出错: {e}")
            # 发送错误消息
            error_chain = [Plain(f"图像生成失败: {str(e)}")]
            yield event.chain_result(error_chain)
