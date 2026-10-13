import codecs
from pathlib import Path

import markdown


def convert_md_to_html(md_file, html_file):
    # 读取Markdown文件
    with codecs.open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 转换Markdown为HTML
    html = markdown.markdown(
        md_text,
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.toc",
        ],
    )

    # HTML模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文件管理系统使用说明</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                color: #333;
            }}
            h1, h2, h3, h4 {{
                color: #2c3e50;
                margin-top: 24px;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 4px;
                font-family: Consolas, Monaco, 'Andale Mono', monospace;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 16px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 16px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
            }}
            blockquote {{
                border-left: 4px solid #42b983;
                margin: 16px 0;
                padding: 0 16px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

    # 写入HTML文件
    with codecs.open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)


if __name__ == "__main__":
    current_dir = Path.cwd()
    md_file = current_dir / "README.md"
    html_file = current_dir / "README.html"

    convert_md_to_html(md_file, html_file)
    print(f"已成功将 {md_file} 转换为 {html_file}")
