# -*- coding: utf-8 -*-
"""
知乎文章/回答下载器 -> PDF（纯 PDF 版，无 Markdown 依赖）

和 zhihu_downloader.py 功能完全一样，只是只输出 PDF 不输出 MD。
双击运行，粘贴链接，自动打开浏览器获取内容。

依赖: playwright, beautifulsoup4
安装: pip install playwright beautifulsoup4 && python -m playwright install chromium
"""

import os
import re
import sys
import asyncio
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_FILE = os.path.join(SCRIPT_DIR, ".zhihu_auth.json")

CONTENT_SELECTORS = [
    ".Post-RichTextContainer",
    ".RichContent-inner",
    ".RichText.RichContent-richtext",
    ".zhuanlan-article-inner",
    ".origin-content",
    ".RichText.ztext",
    ".content",
]

TITLE_SELECTORS = [
    "h1.Post-Title",
    ".PostIndex-header h1",
    "h1.QuestionHeader-title",
    ".QuestionPage-title",
    "h1.ztext-title",
    "title",
]

AUTHOR_SELECTORS = [
    ".AuthorInfo-name",
    ".Post-Author .AuthorInfo-name",
    ".author-info .name",
]

# ── PDF 样式 ──────────────────────────────────────────────────────
PDF_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Noto Serif SC', 'SimSun', 'Songti SC', serif;
    font-size: 14pt;
    line-height: 1.9;
    color: #1a1a1a;
    padding: 60px 72px;
    max-width: 820px;
    margin: 0 auto;
    background: #fff;
}

.article-title {
    font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
    font-size: 26pt;
    font-weight: 700;
    line-height: 1.4;
    margin-bottom: 16px;
    color: #000;
}

.meta-bar {
    font-family: 'Noto Sans SC', sans-serif;
    font-size: 11pt;
    color: #888;
    margin-bottom: 8px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e8e8e8;
}
.meta-bar a { color: #175199; text-decoration: none; }

.article-content { margin-top: 24px; }
.article-content p {
    margin-bottom: 1.2em;
    text-indent: 2em;
    text-align: justify;
}
.article-content img {
    display: block;
    max-width: 90%;
    height: auto;
    margin: 24px auto;
    border-radius: 4px;
    page-break-inside: avoid;
}
.article-content h1, .article-content h2, .article-content h3 {
    font-family: 'Noto Sans SC', sans-serif;
    margin: 1.6em 0 0.6em 0;
    font-weight: 700;
    color: #000;
}
.article-content h1 { font-size: 20pt; }
.article-content h2 { font-size: 17pt; }
.article-content h3 { font-size: 15pt; }

.article-content blockquote {
    margin: 1em 0;
    padding: 12px 20px;
    border-left: 4px solid #175199;
    background: #f7f8fa;
    color: #555;
    font-size: 13pt;
}
.article-content blockquote p { text-indent: 0; }

.article-content code {
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 12pt;
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
}
.article-content pre {
    background: #f5f5f5;
    padding: 16px 20px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 11pt;
    line-height: 1.5;
    margin: 1em 0;
}
.article-content pre code { background: none; padding: 0; }

.article-content ul, .article-content ol { margin: 0.8em 0 0.8em 2em; }
.article-content li { margin-bottom: 0.4em; }

.article-content hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}

.article-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 12pt;
}
.article-content th, .article-content td {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}
.article-content th { background: #f5f5f5; font-weight: 600; }

.footer {
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid #e8e8e8;
    font-family: 'Noto Sans SC', sans-serif;
    font-size: 10pt;
    color: #aaa;
    text-align: center;
}
"""


def safe_filename(text: str, max_len: int = 50) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\n\r\t（）()\[\]]', "", text).strip()
    return cleaned[:max_len]


def process_images(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        src = (
            img.get("data-actualsrc")
            or img.get("data-original")
            or img.get("src")
            or ""
        )
        if not src or "data:image" in src:
            img.decompose()
            continue
        if src.startswith("//"):
            src = "https:" + src
        if not src.startswith("http"):
            img.decompose()
            continue
        img["src"] = src
        for attr in list(img.attrs):
            if attr not in ("src", "alt", "width", "height", "class"):
                del img[attr]
    return str(soup)


def is_login_page(url: str) -> bool:
    return "signin" in url or "login" in url


def build_pdf_html(title: str, author: str, url: str, content_html: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    author_line = f"作者：{author} &nbsp;|&nbsp; " if author else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{PDF_CSS}</style>
</head>
<body>
<div class="article-title">{title}</div>
<div class="meta-bar">
    {author_line}下载时间：{now} &nbsp;|&nbsp;
    <a href="{url}">原链接</a>
</div>
<div class="article-content">{content_html}</div>
<div class="footer">由 zhihu-downloader 生成 &middot; {now}</div>
</body>
</html>"""


async def extract_title(page) -> str:
    for sel in TITLE_SELECTORS:
        try:
            el = await page.query_selector(sel)
            if el:
                text = (await el.inner_text()).strip()
                if text:
                    return text
        except Exception:
            continue
    return "知乎文章"


async def extract_author(page) -> str:
    for sel in AUTHOR_SELECTORS:
        try:
            el = await page.query_selector(sel)
            if el:
                text = (await el.inner_text()).strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


async def extract_content_html(page) -> str:
    for sel in CONTENT_SELECTORS:
        try:
            el = await page.query_selector(sel)
            if el:
                html = (await el.inner_html()).strip()
                if html and len(html) > 50:
                    return html
        except Exception:
            continue
    return ""


async def download_zhihu_pdf(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            storage_state=STORAGE_FILE if os.path.exists(STORAGE_FILE) else None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        if os.path.exists(STORAGE_FILE):
            print("[*] 检测到上次登录态，尝试复用...")
        page = await context.new_page()

        print("[*] 正在访问知乎页面...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"[!] 页面加载超时，继续尝试... ({e})")
        await asyncio.sleep(3)

        # ── 登录检测 ──────────────────────────────────────────
        while True:
            if is_login_page(page.url):
                need_login = True
            else:
                try:
                    need_login = await page.query_selector(".SignContainer-content") is not None
                except Exception:
                    need_login = False
            if not need_login:
                break

            print("=" * 50)
            print("[!] 知乎要求登录！请在浏览器窗口中手动登录")
            print("    登录后我会自动继续...")
            print("=" * 50)
            logged_in = False
            for _ in range(180):
                await asyncio.sleep(1)
                try:
                    se = await page.query_selector(".SignContainer-content")
                    if not se and not is_login_page(page.url):
                        logged_in = True
                        break
                except Exception:
                    pass
            if not logged_in:
                print("[!] 登录超时，请重试")
                await context.close()
                await browser.close()
                return None
            print("[*] 检测到已登录，保存登录态...")
            await context.storage_state(path=STORAGE_FILE)
            print("[*] 登录态已保存，下次无需重复登录")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            await asyncio.sleep(3)

        # ── 等待正文 ──────────────────────────────────────────
        try:
            await page.wait_for_selector(
                ".Post-RichTextContainer, .RichContent-inner, .RichText.ztext",
                timeout=15000,
            )
        except Exception:
            pass
        await asyncio.sleep(2)

        # ── 提取 ──────────────────────────────────────────────
        current_url = page.url
        title = await extract_title(page)
        author = await extract_author(page)
        print(f"[*] 正在提取: {title}")
        if author:
            print(f"[*] 作 者: {author}")

        content_html = await extract_content_html(page)
        if not content_html:
            print("[*] 等待内容加载...")
            await asyncio.sleep(3)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            content_html = await extract_content_html(page)

        if not content_html:
            print("[!] 未能提取到文章内容")
            with open(os.path.join(DESKTOP, "_zhihu_debug.html"), "w", encoding="utf-8") as f:
                f.write(await page.content())
            print("[*] 已保存调试页面到桌面")
            await context.close()
            await browser.close()
            return None

        # ── 生成 PDF ──────────────────────────────────────────
        content_html = process_images(content_html)
        full_html = build_pdf_html(title, author, current_url or url, content_html)

        print("[*] 正在生成 PDF...")
        pdf_page = await context.new_page()
        await pdf_page.set_content(full_html, wait_until="networkidle")
        await asyncio.sleep(3)

        save_name = safe_filename(title) + ".pdf"
        full_path = os.path.join(DESKTOP, save_name)
        # 清理旧文件（防文件锁）
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except PermissionError:
                print(f"[!] 旧文件被占用: {save_name}，请关闭已打开的 PDF 后重试")
        await pdf_page.pdf(
            path=full_path,
            format="A4",
            margin={"top": "40px", "bottom": "40px", "left": "40px", "right": "40px"},
            print_background=True,
        )
        await pdf_page.close()

        # 保存刷新后的登录态
        await context.storage_state(path=STORAGE_FILE)
        await context.close()
        await browser.close()

        print(f"[OK] PDF 已生成 ({os.path.getsize(full_path)/1024:.0f} KB)")
        return full_path


def main():
    print("=" * 50)
    print("  知乎文章下载器 -> PDF（纯 PDF 版）")
    print("=" * 50)
    print()
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("粘贴知乎文章/回答链接：\n> ").strip()
    if not url:
        print("[!] 链接不能为空")
        return
    if not url.startswith("http"):
        url = "https://" + url
    print()
    result = asyncio.run(download_zhihu_pdf(url))
    print()
    if result:
        print(f"[OK] 导出完成！桌面 -> {os.path.basename(result)}")
    else:
        print("[!] 下载失败")
    input("\n按回车退出...")


if __name__ == "__main__":
    main()
