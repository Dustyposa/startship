import pytest
from src.vector.readme_filter import extract_readme_summary

def test_extract_summary_removes_installation_section():
    """测试过滤 Installation 章节"""
    readme = """
# Project Name

This is a great project.

## Installation

npm install project

## Usage

Run the project with npm start.
"""
    result = extract_readme_summary(readme, max_length=500)
    assert "Installation" not in result
    assert "npm install" not in result
    assert "Usage" in result
    assert "npm start" in result

def test_extract_summary_handles_empty_readme():
    """测试空 README 处理"""
    result = extract_readme_summary("", max_length=500)
    assert result == ""

def test_extract_summary_truncates_badges():
    """测试移除 Badge 徽章"""
    readme = """
![Build Status](badge.png)
![License](MIT)

# Project

A great project.
"""
    result = extract_readme_summary(readme, max_length=500)
    assert "[![" not in result
    assert "A great project" in result

def test_extract_summary_limits_length():
    """测试长度限制"""
    readme = "A" * 1000
    result = extract_readme_summary(readme, max_length=100)
    assert len(result) <= 100
