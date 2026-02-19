import os
import datetime
import mimetypes
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import aiosqlite
import uvicorn
from urllib.parse import urlparse, urljoin

# 配置
# 基础 URL，用于拼接相对路径
BASE_URL = os.getenv("BASE_URL", "http://tgstate.evos.alanmaster.top")
# 优先使用环境变量中的 TGSTATE_API_URL，如果没有则使用 BASE_URL + /api
TGSTATE_API_URL = os.getenv("TGSTATE_API_URL", f"{BASE_URL}/api")
# 如果设置了密码，请在此处填写
TGSTATE_PASS = os.getenv("TGSTATE_PASS", "35432d8e-6ec9-f4ff-35df-0148a442bb06")

app = FastAPI(title="TgState Uploader")

# 数据库文件路径
DB_PATH = os.getenv("DB_PATH", "files.db")

# 模板配置
templates = Jinja2Templates(directory="templates")

# 初始化数据库
@app.on_event("startup")
async def startup():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# 首页
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 图库页
@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request})

# 上传接口
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # 验证文件类型
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type or not (mime_type.startswith("image/") or mime_type.startswith("video/")):
        # 双重检查 content_type
        if not (file.content_type.startswith("image/") or file.content_type.startswith("video/")):
            raise HTTPException(status_code=400, detail="仅支持上传图片和视频文件")

    # 读取文件内容
    content = await file.read()
    
    # 构造请求参数
    # target_url = TGSTATE_API_URL
    # if TGSTATE_PASS and 'pass=' not in target_url:
    #     # 手动拼接密码参数，避免使用 httpx 的 params
    #     separator = '&' if '?' in target_url else '?'
    #     target_url = f"{target_url}{separator}pass={TGSTATE_PASS}"

    # 发送到 tgState
    async with httpx.AsyncClient() as client:
        try:
            # tgState API 期望字段名为 image
            # 必须指定 content_type，否则可能被视为 octet-stream 导致某些服务器拒绝
            files = {"image": (file.filename, content, file.content_type)}
            print(f"Sending request to: {TGSTATE_API_URL}") # 增加调试日志
            
            # tgNetDisc 要求的密码传递方式：
            # 1. URL 参数: ?pass=xxx
            # 2. Cookie: p=xxx
            # 3. Header: pass: xxx (部分版本支持)
            
            # 这里采用 Cookie 方式，这是 tgNetDisc 文档明确提到的
            cookies = {}
            if TGSTATE_PASS:
                cookies["p"] = TGSTATE_PASS
                # 为了兼容性，同时也尝试放到 header 中
                # headers["pass"] = TGSTATE_PASS 

            # 不设置 User-Agent，也不传递 params，完全依赖手动拼接的 URL
            # 必须跟随重定向，因为 tgState 可能会进行重定向
            response = await client.post(TGSTATE_API_URL, files=files, cookies=cookies, timeout=60.0, follow_redirects=True)
            
            # 增加响应内容调试日志
            print(f"Response Status: {response.status_code}")
            # 如果是文本内容，打印前200字符；如果是二进制，打印前200字节的 repr
            try:
                print(f"Response Content: {response.text[:200]}")
            except:
                print(f"Response Content (binary): {response.content[:200]!r}")

            response.raise_for_status()
            
            # 兼容空响应或非 JSON 响应
            if not response.content:
                 raise HTTPException(status_code=500, detail="API 返回空响应")
            
            try:
                result = response.json()
            except ValueError:
                # 尝试解析非 JSON 的响应，或者直接抛出错误
                # 如果 API 有可能返回纯文本 URL，可以在这里处理
                # 这里假设如果不是 JSON，可能是出错了
                print(f"Non-JSON response received: {response.text}")
                raise HTTPException(status_code=500, detail=f"API 返回无效数据: {response.text[:100]}")

        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            raise HTTPException(status_code=502, detail=f"连接 tgState 失败: {str(e)}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP Status Error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail=f"tgState 返回错误: {e.response.status_code}")
        except Exception as e:
            print(f"Unexpected Error: {e}")
            if 'API 返回空响应' in str(e):
                 # 特殊处理空响应，有时候 tgState 虽然返回空，但可能已经上传成功（非常罕见）
                 # 但更可能是 API 路径不对或者被防火墙拦截
                 raise HTTPException(status_code=500, detail="API 返回空响应，请检查 TGSTATE_API_URL 是否正确，或网络是否通畅")
            
            if 'Expecting value' in str(e):
                 # 可能是 API 返回了非 JSON 格式的响应
                 raise HTTPException(status_code=500, detail="API 响应格式错误，请检查 API 地址是否正确")
            raise HTTPException(status_code=500, detail=f"上传处理失败: {str(e)}")

    # 解析返回结果
    if result.get("code") != 1:
        raise HTTPException(status_code=500, detail=f"tgState 返回错误: {result.get('message', '未知错误')}")

    file_url = result.get("message")

    if not file_url:
        raise HTTPException(status_code=500, detail="无法获取文件链接")

    # 如果是绝对 URL，只保留路径部分
    if file_url.startswith("http://") or file_url.startswith("https://"):
        try:
            parsed = urlparse(file_url)
            # 仅保留 path, query, fragment
            file_url = parsed.path
            if parsed.query:
                file_url += "?" + parsed.query
            if parsed.fragment:
                file_url += "#" + parsed.fragment
        except Exception as e:
            print(f"Error parsing URL {file_url}: {e}")
            # 如果解析失败，保留原样或做其他处理
            pass
    
    # 确保路径以 / 开头
    if not file_url.startswith("/"):
        file_url = "/" + file_url

    # 保存记录到数据库
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO files (filename, url, created_at) VALUES (?, ?, ?)",
            (file.filename, file_url, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.commit()

    # 返回完整 URL
    full_url = urljoin(BASE_URL, file_url)
    return {"filename": file.filename, "url": full_url}

# 历史记录接口
@app.get("/api/history")
async def get_history():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT filename, url, created_at FROM files ORDER BY id DESC") as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                # 拼接完整 URL
                # 如果数据库里存的是相对路径（以/开头），则拼接 BASE_URL
                if item["url"].startswith("/"):
                     item["url"] = urljoin(BASE_URL, item["url"])
                results.append(item)
            return results

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
