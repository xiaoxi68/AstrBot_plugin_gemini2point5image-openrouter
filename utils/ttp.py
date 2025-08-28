import random
import aiohttp
import asyncio
import aiofiles
import base64
import os
import re
from datetime import datetime, timedelta
import glob

# 全局变量存储最后保存的图像信息
_last_saved_image = {"url": None, "path": None}

async def cleanup_old_images():
    """
    清理超过15分钟的图像文件
    """
    try:
        # 获取当前脚本所在目录的上级目录（插件根目录）
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        images_dir = os.path.join(script_dir, "images")

        if not os.path.exists(images_dir):
            return

        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=15)

        # 查找images目录下的所有图像文件
        image_patterns = ["gemini_image_*.png", "gemini_image_*.jpg", "gemini_image_*.jpeg"]

        for pattern in image_patterns:
            full_pattern = os.path.join(images_dir, pattern)
            for file_path in glob.glob(full_pattern):
                try:
                    # 获取文件的修改时间
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    # 如果文件超过15分钟，删除它
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        print(f"已清理过期图像: {file_path}")

                except Exception as e:
                    print(f"清理文件 {file_path} 时出错: {e}")

    except Exception as e:
        print(f"图像清理过程出错: {e}")

async def save_base64_image(base64_string, image_format="png"):
    """
    保存base64图像数据到images文件夹

    Args:
        base64_string (str): base64编码的图像数据
        image_format (str): 图像格式

    Returns:
        bool: 是否保存成功
    """
    global _last_saved_image
    try:
        # 获取当前脚本所在目录的上级目录（插件根目录）
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        images_dir = os.path.join(script_dir, "images")
        # 确保images目录存在
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        # 先清理旧图像
        await cleanup_old_images()

        # 解码 base64 数据
        image_data = base64.b64decode(base64_string)

        # 生成文件名（使用时间戳避免冲突）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(images_dir, f"gemini_image_{timestamp}.{image_format}")

        # 保存图像文件
        async with aiofiles.open(image_path, "wb") as f:
            await f.write(image_data)

        # 获取绝对路径
        abs_path = os.path.abspath(image_path)
        file_url = f"file://{abs_path}"

        # 存储信息
        _last_saved_image = {"url": file_url, "path": image_path}

        print(f"✅ 图像已保存到: {abs_path}")
        print(f"文件大小: {len(image_data)} bytes")

        return True

    except Exception as decode_error:
        print(f"Base64 解码/保存失败: {decode_error}")
        return False

async def get_saved_image_info():
    """
    获取最后保存的图像信息

    Returns:
        tuple: (image_url, image_path)
    """
    global _last_saved_image
    return _last_saved_image["url"], _last_saved_image["path"]

async def generate_image_openrouter(prompt, api_key, model="google/gemini-2.5-flash-image-preview:free", max_tokens=1000, input_images=None):
    """
    Generate image using OpenRouter API with Gemini model

    Args:
        prompt (str): The prompt for image generation
        api_key (str): OpenRouter API key
        model (str): Model to use (default: google/gemini-2.5-flash-image-preview:free)
        max_tokens (int): Maximum tokens for the response
        input_images (list): List of base64 encoded input images (optional)

    Returns:
        tuple: (image_url, image_path) or (None, None) if failed
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    # 构建消息内容，支持输入图片
    message_content = []
    
    # 添加文本内容
    message_content.append({
        "type": "text",
        "text": f"Generate an image: {prompt}"
    })
    
    # 如果有输入图片，添加到消息中
    if input_images:
        for base64_image in input_images:
            # 确保base64数据包含正确的data URI格式
            if not base64_image.startswith('data:image/'):
                # 假设是PNG格式，添加data URI前缀
                base64_image = f"data:image/png;base64,{base64_image}"
            
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": base64_image
                }
            })

    # 为 Gemini 图像生成构建payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": message_content if len(message_content) > 1 else f"Generate an image: {prompt}"
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/astrbot",
        "X-Title": "AstrBot LLM Draw Plus"
    }

    # 调试输出：打印请求结构
    print(f"\n调试信息:")
    print(f"模型: {model}")
    print(f"输入图片数量: {len(input_images) if input_images else 0}")
    if input_images:
        print(f"第一张图片base64长度: {len(input_images[0])}")
    print(f"消息内容结构: {type(payload['messages'][0]['content'])}")
    if isinstance(payload['messages'][0]['content'], list):
        content_types = [item.get('type', 'unknown') for item in payload['messages'][0]['content']]
        print(f"消息内容类型: {content_types}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                print(f"API响应状态: {response.status}")
                print(f"响应数据键: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")

                if response.status == 200 and "choices" in data:
                    choice = data["choices"][0]
                    message = choice["message"]
                    content = message["content"]

                    # 检查 Gemini 标准的 message.images 字段
                    if "images" in message and message["images"]:
                        print(f"Gemini 返回了 {len(message['images'])} 个图像")

                        for i, image_item in enumerate(message["images"]):
                            if "image_url" in image_item and "url" in image_item["image_url"]:
                                image_url = image_item["image_url"]["url"]

                                # 检查是否是 base64 格式
                                if image_url.startswith("data:image/"):
                                    try:
                                        # 解析 data URI: data:image/png;base64,iVBORw0KGg...
                                        header, base64_data = image_url.split(",", 1)
                                        image_format = header.split("/")[1].split(";")[0]

                                        if await save_base64_image(base64_data, image_format):
                                            return await get_saved_image_info()

                                    except Exception as e:
                                        print(f"解析图像 {i+1} 失败: {e}")
                                        continue

                    # 如果没有找到标准images字段，尝试在content中查找
                    elif isinstance(content, str):
                        # 查找内联的 base64 图像数据
                        base64_pattern = r"data:image/([^;]+);base64,([A-Za-z0-9+/=]+)"
                        matches = re.findall(base64_pattern, content)

                        if matches:
                            image_format, base64_string = matches[0]
                            if await save_base64_image(base64_string, image_format):
                                return await get_saved_image_info()

                    print("未找到图像数据")
                    return None, None

                else:
                    error_msg = data.get("error", {}).get("message", f"HTTP {response.status}")
                    print(f"❌ OpenRouter API 错误: {error_msg}")
                    if "error" in data:
                        print(f"完整错误信息: {data['error']}")
                    return None, None

        except Exception as e:
            print(f"❌ 调用 OpenRouter API 时发生异常: {str(e)}")
            return None, None

async def generate_image(prompt, api_key, model="stabilityai/stable-diffusion-3-5-large", seed=None, image_size="1024x1024"):
    url = "https://api.siliconflow.cn/v1/images/generations"

    if seed is None:
        seed = random.randint(0, 9999999999)

    payload = {
        "model": model,
        "prompt": prompt,
        "image_size": image_size,
        "seed": seed
    }
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()

                if data.get("code") == 50603:
                    print("System is too busy now. Please try again later.")
                    await asyncio.sleep(1)
                    continue

                if "images" in data:
                    for image in data["images"]:
                        image_url = image["url"]
                        async with session.get(image_url) as img_response:
                            if img_response.status == 200:
                                image_path = "downloaded_image.jpeg"
                                async with aiofiles.open(image_path, "wb") as f:
                                    await f.write(await img_response.read())
                                print(f"Image downloaded from {image_url}")
                                return image_url, image_path
                            else:
                                print(f"Failed to download image from {image_url}")
                                return None, None
                else:
                    print("No images found in the response.")
                    return None, None


if __name__ == "__main__":
    async def create_test_image_base64():
        """创建一个测试用的小图片的base64数据"""
        import io
        from PIL import Image as PILImage, ImageDraw
        
        # 创建一个简单的测试图片
        img = PILImage.new('RGB', (100, 100), color='red')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "TEST", fill='white')
        
        # 转换为base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        import base64
        return base64.b64encode(image_bytes).decode()

    async def main():
        print("测试 OpenRouter Gemini 图像生成...")
        openrouter_api_key = ""  # 请设置你的API密钥
        
        if not openrouter_api_key or openrouter_api_key == "":
            print("请先设置真实的 OpenRouter API Key")
            return

        print("\n=== 测试1: 先生成一张图片 ===")
        initial_prompt = "一只可爱的红色小熊猫，数字艺术风格"
        
        image_url, image_path = await generate_image_openrouter(
            initial_prompt,
            openrouter_api_key,
            model="google/gemini-2.5-flash-image-preview:free"
        )
        
        if image_url and image_path:
            print("✅ 初始图像生成成功!")
            print(f"文件路径: {image_path}")
            
            print("\n=== 测试2: 使用生成的图片进行修改 ===")
            try:
                # 读取刚生成的图片并转换为base64
                import base64
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                generated_image_base64 = base64.b64encode(image_bytes).decode()
                
                print(f"生成图片的base64长度: {len(generated_image_base64)}")
                
                # 使用生成的图片进行修改
                modify_prompt = "将这张图片修改为蓝色主题，并添加一些星星装饰"
                input_images = [generated_image_base64]
                
                print("正在使用生成的图片进行修改...")
                modified_url, modified_path = await generate_image_openrouter(
                    modify_prompt,
                    openrouter_api_key,
                    model="google/gemini-2.5-flash-image-preview:free",
                    input_images=input_images
                )
                
                if modified_url and modified_path:
                    print("✅ 图片修改成功!")
                    print(f"修改后文件路径: {modified_path}")
                else:
                    print("❌ 图片修改失败")
                    
            except Exception as e:
                print(f"❌ 图片修改过程出错: {e}")
        else:
            print("❌ 初始图像生成失败，无法进行后续修改测试")

        print("\n=== 测试3: 检查多模态请求格式 ===")
        # 不实际发送请求，只检查构造的payload格式
        try:
            test_image_base64 = await create_test_image_base64()
            
            # 模拟构造请求，检查格式
            message_content = []
            message_content.append({
                "type": "text", 
                "text": f"Generate an image: {initial_prompt}"
            })
            
            base64_image = f"data:image/png;base64,{test_image_base64}"
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": base64_image
                }
            })
            
            payload = {
                "model": "google/gemini-2.5-flash-image-preview:free",
                "messages": [
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            print("✅ 多模态请求格式构造成功")
            print(f"消息内容类型数量: {len(message_content)}")
            print(f"包含文本: {any(item['type'] == 'text' for item in message_content)}")
            print(f"包含图片: {any(item['type'] == 'image_url' for item in message_content)}")
            print(f"图片URL前缀: {message_content[1]['image_url']['url'][:50]}...")
            
        except Exception as e:
            print(f"❌ 请求格式检查出错: {e}")

    asyncio.run(main())
