import os
import re
import datetime
import email.utils

# Map month numbers to Chinese
MONTH_MAP = {
    "01": "一月", "02": "二月", "03": "三月", "04": "四月",
    "05": "五月", "06": "六月", "07": "七月", "08": "八月",
    "09": "九月", "10": "十月", "11": "十一月", "12": "十二月"
}

# Historical overrides to match the exact original names in README.md
HISTORICAL_HEADLINES = {
    "20240107": "AI繁荣第一年",
    "20240112": "OpenAI宣布推出ChatGPT Store",
    "20240119": "比尔·盖茨和萨姆·奥尔特曼对话AI领域",
    "20240126": "用AI生成的货币发展历史视频",
    "20240204": "Neuralink 完成了首个人类大脑植入",
    "20240222": "谷歌发布开源大模型Gemma",
    "20240309": "如何寻找真实的AI需求",
    "20240328": "Suno AI--\"音乐界的ChatGPT\"",
    "20240419": "Meta 发布开源模型 Llama 3",
    "20240519": "Open AI 发布ChatGPT-4o",
    "20240614": "Andrej Karpathy 教你从零复现GPT-2，通宵运行即搞定",
    "20240728": "Meta 发布新一代开源大模型 Llama 3.1",
    "20240825": "LLM Visualization-将 ChatGPT 原理的详细细节可视化的网站",
    "20240914": "OpenAI 发布全新的 o1 系列模型",
    "20241027": "Anthropic 推出了升级版的 Claude 3.5 Sonnet 以及一款新模型 Claude 3.5 Haiku",
    "20241129": "OpenAI上线AI搜索引擎产品——ChatGPT search",
    "20241229": "谷歌推出Gemini 2.0",
    "20250125": "DeepSeek发布并开源 R1 模型",
    "20250325": "DeepSeek发布DeepSeek-V3-0324，编程能力大幅提升",
    "20250430": "Llama 4、Gemini 2.5、通义千问Qwen3先后发布，大模型竞争激烈",
    "20250523": "Google I/O开发者大会",
    "20260522": "Gemini 3.5 Flash发布",
}

EMAIL_SUB_URL = "https://stats.sender.net/forms/e9rM7P/view"

def extract_headline(filepath, date_key):
    if date_key in HISTORICAL_HEADLINES:
        return HISTORICAL_HEADLINES[date_key]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Try to find Headline section (e.g. "## 🌟 本期头条" or "## 本期头条")
        match = re.search(r"##\s*.*?头条.*?\n(.*?)(?=\n##\s|$)", content, re.DOTALL)
        if match:
            section_content = match.group(1)
            # Find first H3 link: ### **[Title](Link)** or ### [Title](Link)
            h3_match = re.search(r"###\s*(?:\*\*)?\[(.*?)(?=\]\()", section_content)
            if h3_match:
                return h3_match.group(1).strip()
            # Find first H3 text
            h3_text_match = re.search(r"###\s*(?:\*\*)?(.*?)(?:\*\*)?\n", section_content)
            if h3_text_match:
                return h3_text_match.group(1).strip()

        # 2. Fallback to first item under ## AI资讯
        match_news = re.search(r"##\s*AI资讯.*?\n(.*?)(?=\n##\s|$)", content, re.DOTALL)
        if match_news:
            news_content = match_news.group(1)
            # Find first H4 link or text
            h4_match = re.search(r"####\s*\d+\.\s*(?:\*\*)?\[(.*?)(?=\]\()", news_content)
            if h4_match:
                return h4_match.group(1).strip()
            h4_text_match = re.search(r"####\s*\d+\.\s*(?:\*\*)?(.*?)(?:\*\*)?\n", news_content)
            if h4_text_match:
                return h4_text_match.group(1).strip().strip("* ")
    except Exception as e:
        print(f"Error extracting headline from {filepath}: {e}")

    return "Weekly News"

def extract_full_content(filepath):
    """Read the full markdown content of an issue file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading full content from {filepath}: {e}")
        return "AIToBox WeeklyNews"

def inline_md(text):
    """Convert inline markdown to HTML: bold, italic, code, links."""
    # Escape XML special chars first (but not < > inside already-converted HTML)
    # We'll process in order: code (to protect content), bold, italic, links
    # Inline code: `code`
    text = re.sub(r"`([^`]+)`", r'<code style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:3px;padding:1px 5px;font-size:0.9em;font-family:monospace;">\1</code>', text)
    # Bold+italic: ***text***
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold: **text**
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text* (not preceded/followed by *)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    # Convert markdown links first to avoid matching URLs inside markdown link syntax
    links = []
    def save_link(m):
        links.append(f'<a href="{m.group(2)}" style="color:#3182ce;text-decoration:none;">{m.group(1)}</a>')
        return f"___LINK_{len(links)-1}___"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", save_link, text)
    # Convert standalone URLs
    text = re.sub(r"(https?://[^\s<\"]+)", r'<a href="\1" style="color:#3182ce;text-decoration:none;">\1</a>', text)
    # Restore markdown links
    for i, link in enumerate(links):
        text = text.replace(f"___LINK_{i}___", link)
    return text

def markdown_to_html(md_text, page_url=None):
    """Convert full markdown document to styled HTML for RSS readers."""
    lines = md_text.split("\n")
    html_parts = []
    in_blockquote = False
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("  </ul>")
            in_ul = False
        if in_ol:
            html_parts.append("  </ol>")
            in_ol = False

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html_parts.append("  </blockquote>")
            in_blockquote = False

    html_parts.append(
        "<div style=\"max-width:720px;margin:0 auto;line-height:1.85;font-size:16px;"
        "color:#2d3748;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Roboto,Helvetica,Arial,sans-serif;padding:0 8px;\">"
    )

    for line in lines:
        stripped = line.strip()

        # Horizontal rule
        if re.match(r"^(---+|===+|\*\*\*+)$", stripped):
            close_blockquote()
            close_lists()
            html_parts.append("  <hr style=\"border:none;border-top:1px solid #edf2f7;margin:24px 0;\">")
            continue

        # Blockquote
        if stripped.startswith(">"):
            close_lists()
            quote_text = stripped[1:].strip()
            quote_text = inline_md(quote_text)
            if not in_blockquote:
                html_parts.append(
                    "  <blockquote style=\"border-left:4px solid #4299e1;background:#ebf8ff;"
                    "padding:12px 16px;margin:16px 0;border-radius:0 6px 6px 0;\">")
                in_blockquote = True
            html_parts.append(f"    <p style=\"margin:4px 0;color:#2c5282;font-style:normal;line-height:1.8;\">{quote_text}</p>")
            continue
        else:
            close_blockquote()

        # Headings (check longer prefixes first)
        if stripped.startswith("######"):
            close_lists()
            html_parts.append(f"  <h6 style=\"margin-top:16px;margin-bottom:8px;font-size:0.9em;color:#4a5568;\">{inline_md(stripped[6:].strip())}</h6>")
            continue
        if stripped.startswith("#####"):
            close_lists()
            html_parts.append(f"  <h5 style=\"margin-top:18px;margin-bottom:8px;font-size:1em;color:#4a5568;\">{inline_md(stripped[5:].strip())}</h5>")
            continue
        if stripped.startswith("####"):
            close_lists()
            heading_text = inline_md(stripped[4:].strip())
            if page_url:
                html_parts.append(
                    f"  <h4 style=\"margin-top:20px;margin-bottom:8px;font-size:1.1em;"
                    f"color:#2d3748;line-height:1.4;\"><a href=\"{page_url}\" "
                    f"style=\"color:#3182ce;text-decoration:none;\">{heading_text}</a></h4>")
            else:
                html_parts.append(f"  <h4 style=\"margin-top:20px;margin-bottom:8px;font-size:1.1em;color:#2d3748;line-height:1.4;\">{heading_text}</h4>")
            continue
        if stripped.startswith("###"):
            close_lists()
            html_parts.append(
                f"  <h3 style=\"margin-top:28px;margin-bottom:10px;font-size:1.25em;"
                f"color:#1a202c;line-height:1.4;border-left:3px solid #4299e1;"
                f"padding-left:10px;\">{inline_md(stripped[3:].strip())}</h3>")
            continue
        if stripped.startswith("##"):
            close_lists()
            html_parts.append(
                f"  <h2 style=\"margin-top:36px;margin-bottom:14px;font-size:1.5em;"
                f"color:#1a202c;line-height:1.3;border-bottom:2px solid #4299e1;"
                f"padding-bottom:6px;\">{inline_md(stripped[2:].strip())}</h2>")
            continue
        if stripped.startswith("#"):
            close_lists()
            html_parts.append(
                f"  <h1 style=\"margin-top:0;margin-bottom:16px;font-size:1.8em;"
                f"color:#1a202c;line-height:1.2;\">{inline_md(stripped[1:].strip())}</h1>")
            continue

        # Unordered list item: - or * or +
        ul_match = re.match(r"^[-*+] (.+)$", stripped)
        if ul_match:
            close_ol = in_ol
            if close_ol:
                html_parts.append("  </ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("  <ul style=\"margin:8px 0 16px 0;padding-left:24px;\">")
                in_ul = True
            html_parts.append(f"    <li style=\"margin-bottom:6px;line-height:1.7;\">{inline_md(ul_match.group(1))}</li>")
            continue

        # Ordered list item: 1. 2. etc.
        ol_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ol_match:
            if in_ul:
                html_parts.append("  </ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("  <ol style=\"margin:8px 0 16px 0;padding-left:24px;\">")
                in_ol = True
            html_parts.append(f"    <li style=\"margin-bottom:6px;line-height:1.7;\">{inline_md(ol_match.group(1))}</li>")
            continue

        # Empty line
        if not stripped:
            close_lists()
            html_parts.append("")
            continue

        # Regular paragraph
        close_lists()
        html_parts.append(f"  <p style=\"margin-bottom:14px;line-height:1.85;\">{inline_md(stripped)}</p>")

    # Close any open structures
    close_blockquote()
    close_lists()
    html_parts.append("</div>")

    return "\n".join(html_parts)

def get_rfc822_date(date_str):
    try:
        dt = datetime.datetime.strptime(date_str, "%Y%m%d")
        # Assume publish time is 18:00:00 UTC+8
        dt = dt.replace(hour=18, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
        return email.utils.format_datetime(dt)
    except Exception:
        return email.utils.format_datetime(datetime.datetime.now())

def to_toml_val(val):
    if isinstance(val, str):
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(val, list):
        items = [to_toml_val(x) for x in val]
        return "[" + ", ".join(items) + "]"
    elif isinstance(val, dict):
        parts = []
        for k, v in val.items():
            parts.append(f'"{k}" = {to_toml_val(v)}')
        return "{ " + ", ".join(parts) + " }"
    return str(val)

RSS_MAX_ITEMS = 10

def generate_rss_feed(issues_list, output_path):
    rss_items = []

    # Only include the most recent RSS_MAX_ITEMS issues
    for filename, headline, full_date, filepath in issues_list[:RSS_MAX_ITEMS]:
        pub_date = get_rfc822_date(full_date)
        # Read the full markdown content of the issue
        md_content = extract_full_content(filepath)
        page_url = f"https://newsweekly.aitobox.com/{filename[:-3]}/"

        html_desc = markdown_to_html(md_content, page_url)

        item_xml = f"""    <item>
      <title><![CDATA[ {full_date}期：{headline} ]]></title>
      <link>{page_url}</link>
      <guid>{page_url}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{html_desc}]]></description>
    </item>"""
        rss_items.append(item_xml)

    now_rfc = email.utils.format_datetime(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))))
    rss_items_xml = "\n".join(rss_items)

    rss_template = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AIToBox WeeklyNews</title>
    <link>https://newsweekly.aitobox.com/</link>
    <description>记录每周值得分享的AI资讯、好用的工具和服务，周六发布。</description>
    <language>zh-cn</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="https://newsweekly.aitobox.com/rss.xml" rel="self" type="application/rss+xml" />
{rss_items_xml}
  </channel>
</rss>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rss_template)
    print(f"RSS feed generated successfully at {output_path}")

def main():
    docs_dir = "docs"
    pattern = re.compile(r"^AIToBoxWeeklyNews_(\d{4})(\d{2})(\d{2})\.md$")

    # Grouping structure: {year: {month: [(filename, headline, full_date)]}}
    data = {}
    all_issues = []

    for filename in os.listdir(docs_dir):
        m = pattern.match(filename)
        if m:
            year = m.group(1)
            month_num = m.group(2)
            day_num = m.group(3)
            full_date = f"{year}{month_num}{day_num}"
            month_name = MONTH_MAP.get(month_num, f"{month_num}月")

            filepath = os.path.join(docs_dir, filename)
            headline = extract_headline(filepath, full_date)

            if year not in data:
                data[year] = {}
            if month_name not in data[year]:
                data[year][month_name] = []

            data[year][month_name].append((filename, headline, full_date))
            all_issues.append((filename, headline, full_date, filepath))

    # Generate RSS (sorted descending by date)
    all_issues_sorted = sorted(all_issues, key=lambda x: x[2], reverse=True)
    generate_rss_feed(all_issues_sorted, os.path.join(docs_dir, "rss.xml"))

    # Sort logic: newest first
    nav = []

    # Prepend Welcome page, ATBInsight, Subscription Guide, Email Subscription, and RSS Subscription to top navigation bar
    nav.append({"欢迎": "welcome.md"})
    nav.append({"ATBInsight": "https://insight.aitobox.com/"})
    #nav.append({"订阅指引": "subscribe-success.md"})
    nav.append({"邮件订阅": EMAIL_SUB_URL})
    nav.append({"RSS 订阅": "https://newsweekly.aitobox.com/rss.xml"})

    markdown_list_lines = []

    # Sort years descending
    for year in sorted(data.keys(), reverse=True):
        year_nav = []
        months_in_year = data[year]

        markdown_list_lines.append(f"\n## {year}\n")

        # Sort months descending
        sorted_months = sorted(
            months_in_year.keys(),
            key=lambda m: [k for k, v in MONTH_MAP.items() if v == m][0] if m in MONTH_MAP.values() else m,
            reverse=True
        )

        for month in sorted_months:
            month_nav = []
            markdown_list_lines.append(f"**{month}**\n")

            issues = sorted(months_in_year[month], key=lambda x: x[2], reverse=True)
            for filename, headline, full_date in issues:
                display_title = f"{full_date}期"
                month_nav.append({display_title: filename})
                markdown_list_lines.append(f"- {full_date}期：[{headline}](docs/{filename})")

            markdown_list_lines.append("")
            year_nav.append({month: month_nav})

        nav.append({year: year_nav})

    # Generate TOML manually
    toml_lines = [
        "[project]",
        f'site_name = "AIToBox WeeklyNews"',
        f'site_description = "记录每周值得分享的AI资讯、好用的工具和服务，周六发布。"',
        f'site_author = "AIToBox"',
        f'site_url = "https://newsweekly.aitobox.com/"',
        f'nav = {to_toml_val(nav)}',
        "",
        "[project.theme]",
        f'variant = "modern"',
        f'custom_dir = "overrides"',
        f'features = ["navigation.sections", "navigation.top"]'
    ]

    with open("zensical.toml", "w", encoding="utf-8") as f:
        f.write("\n".join(toml_lines) + "\n")
    print("zensical.toml generated successfully.")

    # Reconstruct README.md by preserving the header and replacing the list
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()

        # Make the header replacement idempotent
        readme_content = re.sub(r"📢 \*\*订阅周刊\*\*：.*?\n", "", readme_content)
        readme_content = re.sub(r"<div[^>]*class=\"sender-form-field\"[^>]*></div>\n*", "", readme_content)
        readme_content = re.sub(r"每周AI资讯、工具推荐.*?\n", "每周AI资讯、工具推荐\n", readme_content)
        readme_content = re.sub(r"\n{3,}", "\n\n", readme_content)

        # Insert subscription banner
        readme_content = readme_content.replace(
            "每周AI资讯、工具推荐",
            f"每周AI资讯、工具推荐\n\n📢 **订阅周刊**：[📧 邮件订阅]({EMAIL_SUB_URL}) ｜ [🧡 RSS 订阅](https://newsweekly.aitobox.com/rss.xml)\n\n<div style=\"text-align: left\" class=\"sender-form-field\" data-sender-form-id=\"e9rM7P\"></div>"
        )

        split_marker = "[AIToBox NewsWeekly](https://newsweekly.aitobox.com)"
        parts = readme_content.split(split_marker)
        if len(parts) >= 2:
            header_part = parts[0] + split_marker + "\n\n"
            new_readme_content = header_part + "\n".join(markdown_list_lines).strip() + "\n"
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(new_readme_content)
            print("README.md updated with sorted issue list.")
        else:
            print("Warning: Could not find split marker in README.md. Skipping README.md update.")

    # Copy root README.md to docs/index.md, adjusting internal links
    index_path = os.path.join(docs_dir, "index.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
        adjusted_content = readme_content.replace("docs/AIToBoxWeeklyNews_", "AIToBoxWeeklyNews_")
        # Replace the local relative path for RSS in index.md
        adjusted_content = adjusted_content.replace("https://newsweekly.aitobox.com/rss.xml", "rss.xml")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(adjusted_content)
        print("Generated docs/index.md from README.md with adjusted paths.")

if __name__ == "__main__":
    main()
