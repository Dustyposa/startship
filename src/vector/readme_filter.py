import re

# 需要跳过的章节（中英文）
SKIP_SECTIONS = {
    "installation", "install", "getting started", "quick start",
    "quickstart", "setup", "安装", "快速开始",
    "contributing", "contribute", "贡献",
    "license", "许可证", "许可",
    "changelog", "change log", "changes", "history",
    "更新日志", "变更记录",
    "tests", "testing", "test", "测试",
    "development", "dev", "开发", "developers",
    "faq", "f.a.q", "常见问题",
    "donate", "sponsor", "捐赠", "赞助",
    "authors", "credits", "作者", "致谢",
    "acknowledgements", "acknowledgments", "致谢"
}

# 移除 Badge 徽章
BADGE_PATTERN = r'\[!\[.*?\]\(.*?\)\]\(.*?\)|\!\[.*?\]\(.*?\)'

def extract_readme_summary(readme_content: str, max_length: int = 500) -> str:
    """
    提取 README 摘要，过滤掉无关章节

    Args:
        readme_content: README 原始内容
        max_length: 最大返回字符数

    Returns:
        清理后的 README 摘要
    """
    if not readme_content:
        return ""

    # 移除 Badge 徽章
    cleaned = re.sub(BADGE_PATTERN, '', readme_content)

    lines = cleaned.split('\n')
    summary_lines = []
    skipping = False
    current_length = 0

    for line in lines:
        # 检测章节标题
        section_match = re.match(r'^#{1,6}\s+(.+)$', line)
        if section_match:
            section_title = section_match.group(1).strip().lower()

            # 检查是否在黑名单中（精确匹配）
            if section_title in SKIP_SECTIONS:
                skipping = True
                continue
            else:
                skipping = False

        # 如果不在跳过状态，添加到摘要
        if not skipping and line.strip():
            summary_lines.append(line)
            current_length += len(line) + 1  # +1 for newline

            # 检查长度限制
            if current_length >= max_length:
                return '\n'.join(summary_lines)[:max_length]

    return '\n'.join(summary_lines).strip()
