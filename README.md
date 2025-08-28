# AstrBot Gemini 2.5 图像生成插件

基于 OpenRouter API 的 AstrBot 图像生成插件，使用 Google Gemini 2.5 Flash 模型免费生成高质量图像。

## 功能特点

- 🎨 **免费图像生成**: 使用 OpenRouter 的免费 Gemini 2.5 Flash 模型
- 🖼️ **参考图片支持**: 支持基于用户提供的图片进行生成或修改
- 🚀 **异步处理**: 基于 asyncio 的高性能异步图像生成
- 🔗 **智能文件传输**: 支持本地和远程服务器的文件传输
- 🧹 **自动清理**: 自动清理超过15分钟的历史图像文件
- 🛡️ **错误处理**: 完善的异常处理和错误提示
- 🌐 **多语言支持**: 自动将中文提示词翻译为英文

## 安装配置

### 1. 获取 API Key

前往 [OpenRouter](https://openrouter.ai/) 注册账号并获取 API Key。

### 2. 配置参数

在插件配置中设置以下参数：

- **openrouter_api_key**: OpenRouter API 密钥
- **nap_server_address**: NAP cat 服务地址（同服务器填写 `localhost`）
- **nap_server_port**: 文件传输端口（默认 3658）

## 使用方法

### LLM 工具调用

插件注册了一个名为 `gemini-pic-gen` 的 LLM 工具，支持以下参数：

- `image_description`: 图像生成或修改描述（必需）
- `use_reference_images`: 是否使用用户消息中的图片作为参考（默认为 True）

### 使用场景

#### 1. 纯文本生成图像
```python
# 在对话中直接请求生成图像
"帮我画一张可爱的小猫咪"
"Generate a beautiful sunset landscape"
"创建一个科幻风格的机器人"
```

#### 2. 基于参考图片生成/修改
```python
# 用户发送图片后，可以请求基于该图片进行修改
"将这张图片改成卡通风格"
"给这张照片添加一些梦幻效果"
"基于这张图片创建一个类似的场景，但是改成夜晚"
```

#### 3. 智能参考控制
插件会自动判断：
- 如果用户消息包含图片且 `use_reference_images=True`，则使用参考图片
- 如果没有图片或 `use_reference_images=False`，则进行纯文本生成

## 技术实现

### 核心组件

- **main.py**: 插件主要逻辑，继承自 AstrBot 的 Star 类
- **utils/ttp.py**: OpenRouter API 调用和图像处理逻辑
- **utils/file_send_server.py**: 文件传输服务器通信

### 工作流程

1. 接收用户的图像生成请求和可选的参考图片
2. 根据 `use_reference_images` 参数决定是否使用参考图片
3. 构建多模态请求消息（文本+图片）发送到 OpenRouter API
4. 调用 Gemini 2.5 Flash 模型进行图像生成或修改
5. 解析返回的 base64 图像数据
6. 自动清理超过15分钟的历史图像文件
7. 保存新生成的图像到本地文件系统
8. 通过文件传输服务发送图像（如需要）
9. 返回图像链到聊天

### 支持的模型

- `google/gemini-2.5-flash-image-preview:free`（默认免费模型）

## 文件结构

```
AstrBot_plugin_gemini2.5image-openrouter/
├── main.py                 # 插件主文件
├── metadata.yaml          # 插件元数据
├── _conf_schema.json      # 配置模式定义
├── utils/
│   ├── ttp.py            # OpenRouter API 调用
│   └── file_send_server.py # 文件传输工具
├── images/               # 生成的图像存储目录
├── LICENSE              # 许可证文件
└── README.md           # 项目说明文档
```

## 错误处理

插件包含完善的错误处理机制：

- **API 调用失败处理**: 详细的 OpenRouter API 错误信息记录
- **Base64 图像解码错误处理**: 自动检测和修复格式问题
- **参考图片处理异常捕获**: 当参考图片转换失败时的回退机制
- **文件传输异常捕获**: 网络传输失败时的错误提示
- **自动清理失败处理**: 清理历史文件时的异常保护
- **详细的错误日志输出**: 便于调试和问题定位

## 版本信息

- **当前版本**: v1.1
- **更新内容**:
  - 新增参考图片支持功能
  - 优化LLM工具名称为 `gemini-pic-gen`
  - 添加自动清理机制
  - 改进错误处理和日志记录

## 开发信息

- **作者**: 喵喵
- **版本**: v1.1
- **许可证**: 见 LICENSE 文件
- **项目地址**: [GitHub Repository](https://github.com/miaoxutao123/AstrBot_plugin_gemini2point5image-openrouter)

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个插件。

## 许可证

本项目采用开源许可证，详见 LICENSE 文件。