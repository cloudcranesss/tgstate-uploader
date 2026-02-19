# TGState Uploader (TGState 上传助手)

一个现代化的、响应式的 Web 上传工具，专为 [tgState](https://github.com/csznet/tgState) 或 [tgNetDisc](https://github.com/Yohann0617/tgNetDisc) 设计。拥有精美的瀑布流图库和即时预览功能。

![Gallery Preview](http://tgstate.evos.alanmaster.top/d/BQACAgUAAyEGAASMO11uAAIBHmmXLLaow5Y2WV2m4Jr68MQ_8V2pAAIzIQAC9XC5VBuRwgJs5ekQOgQ)

## 功能特性

- **拖拽上传**: 支持拖拽文件直接上传，轻松处理图片和视频。
- **现代化图库**: 
  - 采用瀑布流布局（Pinterest 风格），美观展示图片和视频。
  - **即时悬停预览**: 鼠标悬停在缩略图上即可快速预览媒体内容。
  - **灯箱模式**: 支持全屏查看大图、缩放以及视频播放。
  - **分类筛选**: 可按“全部”、“图片”或“视频”进行快速筛选。
- **历史记录**: 自动记录上传文件的文件名、下载链接和上传时间。
- **响应式设计**: 完美适配桌面、平板和移动设备屏幕。
- **剪贴板集成**: 一键复制文件链接。
- **自定义域名**: 支持配置自定义基础 URL（Base URL），适配自定义域名场景。

## 配置说明

您可以通过环境变量或直接修改 `docker-compose.yml` 来配置应用。

| 环境变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `TGSTATE_PASS` | tgState 实例的访问密码（如果设置了的话）。 | `password` |
| `BASE_URL` | 文件链接的公共基础 URL（例如您的自定义域名）。 | `http://localhost:8088` |

## 快速开始 (Docker)

使用 Docker Compose 是运行 TGState Uploader 最简单的方法。

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/your-username/tgstate-uploader.git
    cd tgstate-uploader
    ```

2.  **编辑配置 (可选)**:
    如果您使用自己的 tgState 服务，请修改 `docker-compose.yml` 中的环境变量。

3.  **启动服务**:
    ```bash
    docker-compose up -d
    ```

4.  **访问应用**:
    在浏览器中打开 [http://localhost:8080](http://localhost:8080)。

## 手动安装

1.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **运行服务器**:
    ```bash
    python main.py
    ```
    或者直接使用 uvicorn:
    ```bash
    uvicorn main:app --reload --port 8080
    ```

## 项目结构

- `main.py`: FastAPI 后端应用程序。
- `templates/`: HTML 模板 (使用 Vue.js + Tailwind CSS 构建)。
  - `index.html`: 上传页面。
  - `gallery.html`: 图库页面。
- `files.db`: SQLite 数据库，用于存储上传历史（在 Docker 中持久化存储于 `./data` 卷）。

## 许可证

MIT License
