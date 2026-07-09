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

## 免责声明

1. **个人学习用途** — 本工具仅用于个人学习、研究、备份自己已授权的知乎内容。
2. **禁止商用** — 严禁将本工具用于商业目的、批量抓取或任何形式的牟利行为。
3. **版权归属** — 下载内容的知识产权归知乎及原作者所有，用户应遵守知乎用户协议和相关法律法规。
4. **责任自负** — 使用者因违反上述条款引发的任何法律纠纷，由使用者自行承担全部责任。

## 许可

Copyright © 2025 wuyuetianxiadiyi. All rights reserved.

本软件仅供个人学习研究，未经许可不得用于商业用途或再分发。
