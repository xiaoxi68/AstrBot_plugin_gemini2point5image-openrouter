# AstrBot Gemini 2.5 图像生成插件

基于 OpenRouter API 的 AstrBot 图像生成插件，使用 Google Gemini 2.5 Flash 模型免费生成高质量图像。

## 功能特点

- 🎨 **免费图像生成**: 使用 OpenRouter 的免费 Gemini 2.5 Flash 模型
- 🚀 **异步处理**: 基于 asyncio 的高性能异步图像生成
- 🔗 **智能文件传输**: 支持本地和远程服务器的文件传输
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

插件注册了一个名为 `pic-gen` 的 LLM 工具，支持以下参数：

- `prompt`: 图像生成提示词
- `model`: 使用的模型（默认为 `google/gemini-2.5-flash-image-preview:free`）

### 示例用法

```python
# 在对话中直接请求生成图像
"帮我画一张可爱的小猫咪"
"Generate a beautiful sunset landscape"
"创建一个科幻风格的机器人"
```

## 技术实现

### 核心组件

- **main.py**: 插件主要逻辑，继承自 AstrBot 的 Star 类
- **utils/ttp.py**: OpenRouter API 调用和图像处理逻辑
- **utils/file_send_server.py**: 文件传输服务器通信

### 工作流程

1. 接收用户的图像生成请求
2. 调用 OpenRouter API 生成图像
3. 解析返回的 base64 图像数据
4. 保存图像到本地文件系统
5. 通过文件传输服务发送图像（如需要）
6. 返回图像链到聊天

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

- API 调用失败时的重试机制
- Base64 图像解码错误处理
- 文件传输异常捕获
- 详细的错误日志输出

## 开发信息

- **作者**: 喵喵
- **版本**: v1.0
- **许可证**: 见 LICENSE 文件
- **项目地址**: [GitHub Repository](https://github.com/miaoxutao123/AstrBot_plugin_gemini2.5image-openrouter)

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个插件。

## 许可证

本项目采用开源许可证，详见 LICENSE 文件。