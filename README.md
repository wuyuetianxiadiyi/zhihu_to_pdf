# 知乎文章/回答下载器 → PDF

自动抓取知乎文章/回答内容，渲染为 PDF 保存到桌面。

## 用法

```bash
pip install playwright beautifulsoup4
python -m playwright install chromium
python zhihu_to_pdf_pure.py
```

双击运行，粘贴知乎链接，自动打开浏览器获取内容并生成 PDF。

## 功能

- 支持知乎文章（zhuanlan.zhihu.com）
- 支持知乎回答（www.zhihu.com/question/.../answer/...）
- 自动处理登录态（首次需扫码登录，缓存到本地）
- 保留图片、代码块、公式等格式
- 纯 PDF 输出，无 Markdown 依赖

## 依赖

- Python 3.8+
- playwright
- beautifulsoup4
- Chromium 浏览器引擎
