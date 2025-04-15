# FinVizAI 一键生成股票与期货分析视频

## 项目简介 🎥
FinVizAI 是一个集成了多种技术和工具的强大系统，专注于股票和期货数据的获取、分析、可视化以及视频生成。通过本项目，您可以轻松实现以下功能：

- **📈 数据获取**：从权威数据源（如东方财富网）获取股票或期货的历史数据和最新资讯。
- **📊 数据分析**：计算技术指标（如均线、布林带、MACD等），整合最新市场资讯，结合大模型进行多维度深度解析，提供全面的市场洞察。
- **🖼️ 图表绘制**：使用 PyEcharts 和 Pyppeteer 绘制精美的 K 线图并生成静态图片。
- **🗣️ 语音生成**：通过 TTS 技术（支持 Dashscope 和 Hailuo 引擎）将分析结果转化为语音解说。
- **🎥 视频合成**：使用 MoviePy 将图表图片和语音解说合成为带有字幕的高质量视频。

无论您是投资者、分析师还是内容创作者，FinVizAI 都能为您提供一站式的解决方案！

## 示例 📂

<table>
    <thead>
        <tr>
            <th align="center"><g-emoji class="g-emoji" alias="chart_with_upwards_trend">📈</g-emoji> 比亚迪（002594）</th>
            <th align="center"><g-emoji class="g-emoji" alias="bar_chart">📊</g-emoji> 塑料主连</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td align="center">
                <video controls width="320" height="240" src="https://github.com/user-attachments/assets/46f47854-9054-46c2-90a3-d85900ac974b"></video>
            </td>
            <td align="center">
                <video controls width="320" height="240" src="https://github.com/user-attachments/assets/87fd1625-64a6-44d5-8bf2-69ef0be5b3b1"></video>
            </td>
        </tr>
    </tbody>
</table>

## 功能模块 🤖

### 1. 数据获取与处理
- **core/fetcher/base.py, futures.py, stock.py**：从东方财富网获取股票或期货历史数据，并计算技术指标（如均线、布林带、MACD等）。

### 2. K线图绘制
- **utils/chart/kline.py**：使用 PyEcharts 库绘制 K 线图，并通过 Pyppeteer 生成静态图片。

### 3. LLM 分析
- **core/llm/base.py, futures.py, stock.py**：利用腾讯元宝大模型对股票或期货数据进行分析，生成通俗易懂的市场解盘文案。
  - [yuanbao-free-api](https://github.com/chenwr727/yuanbao-free-api.git)

### 4. 报告生成
- **utils/report.py**：基于分析结果生成报告图片，用于视频合成。

### 5. TTS 语音生成
- **core/tts/base.py, dashscope.py, hailuo.py**：将分析文案转化为语音解说文件。
  - [dashscope](https://help.aliyun.com/zh/model-studio/developer-reference/cosyvoice-python-api)
  - [hailuo](https://github.com/LLM-Red-Team/minimax-free-api.git)

### 6. 视频生成
- **utils/video.py**：使用 MoviePy 库将图片、语音和字幕合成为高质量视频。

## 安装与运行 ⚙️

### 克隆项目
```bash
git clone https://github.com/chenwr727/FinVizAI.git
cd FinVizAI
```

### 环境准备
确保已安装以下依赖项：
```bash
pip install -r requirements.txt
```

### 配置文件
编辑 `config.toml` 文件，配置相关参数（如 API 密钥、模型名称、输出目录等）：
```bash
cp config-example.toml config.toml
```

### 启动服务
```bash
python main.py
```

## 目录结构 📁
```
.
├── main.py                # 主程序入口
├── assets/v5              # 存放前端资源文件
│   └── echarts.min.js
├── utils                  # 工具类模块
│   ├── config.py          # 配置管理
│   ├── data.py            # 数据处理
│   ├── log.py             # 日志管理
│   ├── report.py          # 报告生成
│   ├── subtitle.py        # 字幕生成
│   ├── video.py           # 视频生成
│   └── chart              # 图表相关工具
│       ├── kline.py       # K线图绘制
│       └── snapshot.py    # 截图工具
├── core                   # 核心逻辑模块
│   ├── fetcher            # 数据获取模块
│   │   ├── base.py        # 基础 Fetcher 类
│   │   ├── futures.py     # 期货数据 Fetcher
│   │   └── stock.py       # 股票数据 Fetcher
│   ├── llm                # LLM 分析模块
│   │   ├── base.py        # 基础 LLMClient 类
│   │   ├── futures.py     # 期货 LLM 分析
│   │   └── stock.py       # 股票 LLM 分析
│   ├── schemas.py         # 数据模型定义
│   ├── stock.py           # 股票视频生成
│   └── tts                # TTS 相关
│       ├── base.py        # 基础 TTS 类
│       ├── dashscope.py   # Dashscope TTS 实现
│       └── hailuo.py      # Hailuo TTS 实现
└── output                 # 输出目录
```

## 注意事项 ⚠️
- 请确保所有第三方 API 密钥正确无误，特别是用于获取期货数据和提供 TTS 服务的 API。
- 运行环境需安装必要的库和工具，如 `ffmpeg` 等。
- 生成的视频文件会保存在 `output` 目录下。

## 贡献 🤝
欢迎提交 Issues 和 Pull Requests！

## 许可证 📜
MIT