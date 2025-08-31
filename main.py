from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from astrbot.core.message.components import Reply
from .utils.ttp import generate_image_openrouter
from .utils.file_send_server import send_file

@register("gemini-25-image-openrouter", "喵喵", "使用openrouter的免费api生成图片", "1.3")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        # 支持多个API密钥
        self.openrouter_api_keys = config.get("openrouter_api_keys", [])
        # 向后兼容：如果还在使用旧的单个API密钥配置
        old_api_key = config.get("openrouter_api_key")
        if old_api_key and not self.openrouter_api_keys:
            self.openrouter_api_keys = [old_api_key]
        
        self.nap_server_address = config.get("nap_server_address")
        self.nap_server_port = config.get("nap_server_port")

    async def send_image_with_callback_api(self, image_path: str) -> Image:
        """
        优先使用callback_api_base发送图片，失败则退回到本地文件发送
        
        Args:
            image_path (str): 图片文件路径
            
        Returns:
            Image: 图片组件
        """
        try:
            # 获取框架配置的callback_api_base
            callback_api_base = self.context.get_config().get("callback_api_base")
            
            if callback_api_base:
                logger.info(f"检测到配置了callback_api_base: {callback_api_base}")
                try:
                    # 创建Image组件并尝试转换为下载链接
                    image_component = Image.fromFileSystem(image_path)
                    download_url = await image_component.convert_to_web_link()
                    
                    logger.info(f"成功生成下载链接: {download_url}")
                    # 使用URL形式发送图片
                    return Image.fromURL(download_url)
                    
                except Exception as e:
                    logger.warning(f"使用callback_api_base生成下载链接失败: {e}，将退回到本地文件发送")
                    # 如果生成下载链接失败，退回到本地文件发送
                    return Image.fromFileSystem(image_path)
            else:
                logger.info("未配置callback_api_base，使用本地文件发送")
                return Image.fromFileSystem(image_path)
                
        except Exception as e:
            logger.error(f"发送图片时出错: {e}")
            # 发生任何错误都退回到本地文件发送
            return Image.fromFileSystem(image_path)

    @llm_tool(name="gemini-pic-gen")
    async def pic_gen(self, event: AstrMessageEvent, image_description: str, use_reference_images: bool = True):
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
        openrouter_api_keys = self.openrouter_api_keys
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
                            logger.warning(f"转换当前消息中的参考图片到base64失败: {e}")
                    elif isinstance(comp, Reply):
                        # 处理引用消息中的图片
                        if hasattr(comp, 'chain') and comp.chain:
                            for reply_comp in comp.chain:
                                if isinstance(reply_comp, Image):
                                    try:
                                        base64_data = await reply_comp.convert_to_base64()
                                        input_images.append(base64_data)
                                        logger.info(f"从引用消息中获取到图片")
                                    except Exception as e:
                                        logger.warning(f"转换引用消息中的参考图片到base64失败: {e}")
            
            # 记录使用的图片数量
            if input_images:
                logger.info(f"使用了 {len(input_images)} 张参考图片进行图像生成")
            else:
                logger.info("未找到参考图片，执行纯文本图像生成")

        # 调用生成图像的函数
        try:
            image_url, image_path = await generate_image_openrouter(
                image_description, 
                openrouter_api_keys, 
                input_images=input_images
            )
            
            if not image_url or not image_path:
                # 生成失败，发送错误消息
                error_chain = [Plain("图像生成失败，请检查API配置和网络连接。")]
                yield event.chain_result(error_chain)
                return
            
            # 处理文件传输和图片发送
            if self.nap_server_address and self.nap_server_address != "localhost":
                image_path = await send_file(image_path, HOST=nap_server_address, PORT=nap_server_port)
            
            # 使用新的发送方法，优先使用callback_api_base
            image_component = await self.send_image_with_callback_api(image_path)
            chain = [image_component]
            yield event.chain_result(chain)
            return
                
        except Exception as e:
            logger.error(f"图像生成过程出错: {e}")
            # 发送错误消息
            error_chain = [Plain(f"图像生成失败: {str(e)}")]
            yield event.chain_result(error_chain)
            return
