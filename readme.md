# FinVizAI 🎥  
**一键生成股票与期货分析视频**

FinVizAI 是一个强大的工具，专注于股票和期货数据的获取、分析、可视化以及视频生成。通过本项目，您可以轻松完成从数据采集到高质量分析视频输出的全流程。

## 核心功能 🌟

- **📈 数据获取**：从权威数据源（如东方财富网）获取股票或期货的历史数据和最新资讯。
- **📊 数据分析**：计算技术指标（如均线、布林带、MACD等），结合大模型进行多维度深度解析，提供全面的市场洞察。
- **🖼️ 图表绘制**：使用 PyEcharts 和 Pyppeteer 绘制精美的 K 线图并生成静态图片。
- **🗣️ 语音生成**：通过 TTS 技术（支持 Dashscope 和 Hailuo 引擎）将分析结果转化为语音解说。
- **🎥 视频合成**：使用 MoviePy 将图表图片和语音解说合成为带有字幕的高质量视频。

无论您是投资者、分析师还是内容创作者，FinVizAI 都能为您提供一站式的解决方案！

## 示例展示 📂

以下是一些示例视频，分别展示了不同模式下的分析效果：

<table>
    <thead>
        <tr>
            <th align="center">全局背景模式</th>
            <th align="center">滑动窗口模式</th>
            <th align="center">期货分析示例</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td align="center">
                <video controls width="320" height="180" src="https://github.com/user-attachments/assets/34b47522-56da-41ab-8d89-433908d66f92"></video>
                <br>比亚迪（002594）
            </td>
            <td align="center">
                <video controls width="320" height="180" src="https://github.com/user-attachments/assets/24a50c51-39ec-4e29-b7a9-298e675361d5"></video>
                <br>比亚迪（002594）
            </td>
            <td align="center">
                <video controls width="320" height="180" src="https://github.com/user-attachments/assets/abdbfea1-61b9-47f2-beb0-d716cefa805b"></video>
                <br>塑料主连
            </td>
        </tr>
    </tbody>
</table>

## 功能模块详解 🛠️

### 1. 数据获取与处理  
- **路径**: `core/fetcher/base.py, futures.py, stock.py`  
- **功能**: 从东方财富网获取股票或期货历史数据，并计算技术指标（如均线、布林带、MACD等）。  
  - **futures**: 期货数据获取与处理  
  - **stock**: 股票数据获取与处理  

### 2. K线图绘制  
- **路径**: `core/kline/base.py, bg.py, windows.py`  
- **功能**: 使用 PyEcharts 库绘制 K 线图，并通过 Pyppeteer 生成静态图片。  
  - **bg（全局背景模式）**：以布林带为背景，完整展示所有历史数据，并通过动态添加每日 K 线的方式逐步呈现时间序列变化。  
  - **windows（滑动窗口模式）**：先展示全部数据，随后通过缩短时间范围，使用固定大小的窗口从左至右逐步移动，聚焦局部细节，最后拉长时间范围回归整体视图。  

### 3. LLM 分析  
- **路径**: `core/llm/base.py, futures.py, stock.py`  
- **功能**: 利用腾讯元宝大模型对股票或期货数据进行分析，生成通俗易懂的市场解盘文案。  
  - [yuanbao-free-api](https://github.com/chenwr727/yuanbao-free-api.git)  

### 4. 报告生成  
- **路径**: `utils/report.py`  
- **功能**: 基于分析结果生成报告图片，用于视频合成。  

### 5. TTS 语音生成  
- **路径**: `core/tts/base.py, dashscope.py, hailuo.py`  
- **功能**: 将分析文案转化为语音解说文件。  
  - [dashscope](https://help.aliyun.com/zh/model-studio/developer-reference/cosyvoice-python-api)  
  - [hailuo](https://github.com/LLM-Red-Team/minimax-free-api.git)  

### 6. 视频生成  
- **路径**: `utils/video.py`  
- **功能**: 使用 MoviePy 库将图片、语音和字幕合成为高质量视频。  

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
├── assets                      # 存放资源文件
│   ├── audios                  # 音频
│   │   └── bgm.mp3             # 背景音乐
│   ├── fonts                   # 字体
│   │   └── msyhbd.ttc          # 字幕字体
│   └── v5                      # Echarts
│       └── echarts.min.js      # Echarts 静态资源文件
├── core                        # 核心逻辑模块
│   ├── fetcher                 # 数据获取模块
│   │   ├── __init__.py         # 初始化文件
│   │   ├── base.py             # 基础 Fetcher 类
│   │   ├── futures.py          # 期货数据 Fetcher
│   │   └── stock.py            # 股票数据 Fetcher
│   ├── kline                   # K线图相关
│   │   ├── __init__.py         # 初始化文件
│   │   ├── base.py             # 基础 Kline 类
│   │   ├── bg.py               # 全局背景
│   │   └── windows.py          # 滑动窗口
│   ├── llm                     # LLM 分析模块
│   │   ├── __init__.py         # 初始化文件
│   │   ├── base.py             # 基础 LLMClient 类
│   │   ├── futures.py          # 期货 LLM 分析
│   │   └── stock.py            # 股票 LLM 分析
│   ├── tts                     # TTS 相关
│   │   ├── __init__.py         # 初始化文件
│   │   ├── base.py             # 基础 TTS 类
│   │   ├── dashscope.py        # Dashscope TTS 实现
│   │   └── hailuo.py           # Hailuo TTS 实现
│   ├── __init__.py             # 初始化文件
│   ├── futures.py              # 视频生成
│   └── schemas.py              # 数据模型定义
├── utils                       # 工具类模块
│   ├── chart                   # 图表相关工具
│   │   ├── __init__.py         # 初始化文件
│   │   ├── axis.py             # 坐标轴设定
│   │   └── snapshot.py         # 截图工具
│   ├── __init__.py             # 初始化文件
│   ├── config.py               # 配置管理
│   ├── log.py                  # 日志管理
│   ├── report.py               # 报告生成
│   ├── subtitle.py             # 字幕生成
│   └── video.py                # 视频生成
└── main.py                     # 主程序入口
```

## 注意事项 ⚠️

- 确保所有第三方 API 密钥正确无误，特别是用于获取期货数据和提供 TTS 服务的 API。
- 运行环境需安装必要的库和工具，如 `ffmpeg` 等。
- 生成的视频文件会保存在 `output` 目录下。

## 贡献 🤝

欢迎提交 Issues 和 Pull Requests！我们期待您的参与和反馈。

## 许可证 📜

MIT