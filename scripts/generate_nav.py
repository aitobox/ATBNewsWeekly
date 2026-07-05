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

EMAIL_SUB_URL = "https://stats.sender.net/forms/b68J77/view"

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

def extract_description(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        output_parts = []
        in_headline = False
        
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## "):
                in_headline = False
                if "头条" in line_str:
                    in_headline = True
                    output_parts.append(line_str)
                else:
                    output_parts.append(line_str)
            elif in_headline:
                output_parts.append(line)
            else:
                if line_str.startswith("### ") or line_str.startswith("#### "):
                    output_parts.append(line_str)
                    
        return "\n".join(output_parts)
    except Exception as e:
        print(f"Error extracting description from {filepath}: {e}")
        return "AIToBox WeeklyNews"

def markdown_to_html(md_text, page_url=None):
    lines = md_text.split("\n")
    in_quote = False
    html_lines = []
    
    # Wrap in a styled div with a spacious line-height (1.85) and standard font family
    html_lines.append("<div style=\"line-height: 1.85; font-size: 16px; color: #2d3748; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\">")
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            quote_text = stripped[1:].strip()
            if quote_text.startswith("**EN**:") or quote_text.startswith("**ZH**:"):
                quote_text = quote_text.replace("**EN**:", "<strong>EN</strong>:")
                quote_text = quote_text.replace("**ZH**:", "<strong>ZH</strong>:")
            
            if not in_quote:
                html_lines.append("  <blockquote style=\"border-left: 4px solid #e2e8f0; padding-left: 16px; margin: 16px 0; color: #718096; font-style: italic;\">")
                in_quote = True
            html_lines.append(f"    <p style=\"margin-bottom: 8px; line-height: 1.85;\">{quote_text}</p>")
        else:
            if in_quote:
                html_lines.append("  </blockquote>")
                in_quote = False
            
            # Evaluate longer prefix first to avoid "###" matching "####"
            if stripped.startswith("####"):
                heading_text = stripped[4:].strip()
                if page_url:
                    # Link secondary headings directly to the post page
                    html_lines.append(f"  <h4 style=\"margin-top: 20px; margin-bottom: 10px; font-size: 1.1em; line-height: 1.4;\"><a href=\"{page_url}\" style=\"color: #3182ce; text-decoration: none;\">{heading_text}</a></h4>")
                else:
                    html_lines.append(f"  <h4 style=\"margin-top: 20px; margin-bottom: 10px; font-size: 1.1em; line-height: 1.4;\">{heading_text}</h4>")
            elif stripped.startswith("###"):
                html_lines.append(f"  <h3 style=\"margin-top: 24px; margin-bottom: 12px; font-size: 1.3em; line-height: 1.4;\">{stripped[3:].strip()}</h3>")
            elif stripped.startswith("##"):
                html_lines.append(f"  <h2 style=\"margin-top: 32px; margin-bottom: 16px; border-bottom: 1px solid #edf2f7; padding-bottom: 8px; font-size: 1.6em; line-height: 1.3;\">{stripped[2:].strip()}</h2>")
            elif stripped:
                html_lines.append(f"  <p style=\"margin-bottom: 16px; line-height: 1.85;\">{stripped}</p>")
            else:
                html_lines.append("")

    if in_quote:
        html_lines.append("  </blockquote>")
        
    html_lines.append("</div>")

    html_content = "\n".join(html_lines)
    html_content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"\[(.*?)(?=\]\()\]\((.*?)\)", r'<a href="\2" style="color: #3182ce; text-decoration: none;">\1</a>', html_content)
    return html_content

def get_rfc822_date(date_str):
    try:
        dt = datetime.datetime.strptime(date_str, "%Y%m%d")
        # Assume publish time is 10:00:00 UTC+8
        dt = dt.replace(hour=10, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
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

def generate_rss_feed(issues_list, output_path):
    rss_items = []
    
    for filename, headline, full_date, filepath in issues_list:
        pub_date = get_rfc822_date(full_date)
        md_desc = extract_description(filepath)
        page_url = f"https://newsweekly.aitobox.com/{filename[:-3]}/"
        
        # In RSS output, replace the first headline title hyperlink with the issue page_url
        h3_match = re.search(r"###\s*(?:\*\*)?\[(.*?)(?=\]\()\]\((.*?)\)", md_desc)
        if h3_match:
            original_url = h3_match.group(2)
            md_desc = md_desc.replace(f"]({original_url})", f"]({page_url})", 1)
            
        html_desc = markdown_to_html(md_desc, page_url)
        
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
    
    # Prepend Welcome page, Email Subscription, and RSS Subscription to top navigation bar
    nav.append({"欢迎": "welcome.md"})
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
            lines = f.readlines()
        
        # Update lines 2 and 3 of README to put RSS link in the subtitle header
        if len(lines) >= 3:
            lines[1] = "每周AI资讯、工具推荐\n"
            lines[2] = f"\n📢 **订阅周刊**：[📧 邮件订阅]({EMAIL_SUB_URL}) ｜ [🧡 RSS 订阅](https://newsweekly.aitobox.com/rss.xml)\n\n"
            
        readme_content = "".join(lines)
        
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
