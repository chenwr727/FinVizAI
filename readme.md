# FinVizAI 股票分析与视频生成系统

## 项目简介
本项目旨在通过集成多种技术和工具，实现对股票数据的获取、分析、可视化，并最终生成带有字幕和语音解说的视频内容。主要功能包括：
- 获取指定股票的历史数据
- 计算技术指标并进行分析，deepseek-r1 + 联网搜索
- 绘制K线图并生成图片
- 使用TTS（Text-to-Speech）技术生成语音解说
- 将图片和语音合成视频

https://github.com/user-attachments/assets/b7e5ef8c-d979-4ba4-9b3e-d6a6adadcd1e

## 功能模块
### 1. 数据获取与处理
- **utils/data.py**：提供`get_stock_data`函数用于从东方财富网获取股票历史数据；`calc_indicators`函数计算各种技术指标如均线、布林带、MACD等。

### 2. K线图绘制
- **utils/chart/kline.py**：使用PyEcharts库绘制K线图，并通过Pyppeteer生成静态图片。

### 3. LLM分析
- **core/llm.py**：利用腾讯元宝大模型对股票数据进行分析，生成通俗易懂的股市解盘文案。

    - [yuanbao-free-api](https://github.com/chenwr727/yuanbao-free-api.git)

### 4. TTS语音生成
- **core/tts/base.py, dashscope.py, hailuo.py**：支持多种TTS引擎（如Dashscope和Hailuo），将文本转换为语音文件。

    - [dashscope](https://help.aliyun.com/zh/model-studio/developer-reference/cosyvoice-python-api)
    - [hailuo](https://github.com/LLM-Red-Team/minimax-free-api.git)

### 5. 视频生成
- **utils/video.py**：使用MoviePy库将图片和语音合成为视频，并添加字幕。

## 安装与运行

### 克隆项目
```bash
git clone https://github.com/chenwr727/FinVizAI.git\
cd FinVizAI
```

### 环境准备
确保已安装以下依赖项：
```bash
pip install -r requirements.txt
```

### 配置文件
编辑`config.toml`文件，配置相关参数，例如API密钥、模型名称、输出目录等。

### 启动服务
```bash
python main.py
```

## 目录结构
```
.
├── main.py                # 主程序入口
├── assets/v5              # 存放前端资源文件
│   └── echarts.min.js
├── utils                  # 其他工具类
│   ├── config.py          # 配置管理
│   ├── data.py            # 数据处理
│   ├── log.py             # 日志管理
│   ├── subtitle.py        # 字幕生成
│   ├── video.py           # 视频生成
│   └── chart              # 图表相关工具
│       ├── kline.py       # K线图绘制
│       └── snapshot.py    # 截图工具
├── core                   # 核心逻辑
│   ├── llm.py             # LLM客户端
│   ├── schemas.py         # 数据模型定义
│   ├── stock.py           # 股票视频生成
│   └── tts                # TTS相关
│       ├── base.py        # 基础TTS类
│       ├── dashscope.py   # Dashscope TTS实现
│       └── hailuo.py      # Hailuo TTS实现
└── output                 # 输出目录
```

## 示例
在`main.py`中调用`StockVideo`类生成平安银行一年的日线视频：
```python
async def main():
    llm_client = LLMClient()
    stock_client = StockVideo(llm_client)

    stock_name = "平安银行"
    stock_code = "000001"
    start_date = (datetime.datetime.now() - datetime.timedelta(365)).strftime("%Y%m%d")
    end_date = datetime.datetime.now().strftime("%Y%m%d")

    stock = StockBase(
        name=stock_name, symbol=stock_code, start_date=start_date, end_date=end_date, adjust="qfq", period="daily"
    )
    await stock_client.generate_video(stock, config.tts, config.video)
```

## 注意事项
- 请确保所有第三方API密钥正确无误。
- 运行环境需安装必要的库和工具，如`ffmpeg`等。
- 生成的视频文件会保存在`output`目录下。

## 贡献
欢迎提交Issues和Pull Requests！

## 许可证
MIT