"""XNOW-Harness — Claude Code 辅助工具箱"""
from setuptools import setup, find_packages

setup(
    name="xnow-harness",
    version="0.2.0",
    description="XNOW-Harness — Claude Code 辅助工具箱",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.0.0",
        "httpx>=0.27.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "xnow = xnow_harness.main:main",
        ],
    },
)
