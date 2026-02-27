"""
TinkClaw Python SDK Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tinkclaw",
    version="0.3.0",
    author="TinkClaw",
    author_email="dev@tinkclaw.com",
    description="Official Python SDK for TinkClaw quant intelligence API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tinkclaw/tinkclaw-python",
    packages=find_packages(exclude=["tests", "examples", "venv"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
        "brokers": [
            "alpaca-py>=0.10.0",
        ],
    },
    keywords="trading bot api quant finance tinkclaw confluence signals crypto",
    project_urls={
        "Documentation": "https://tinkclaw.com/docs",
        "Source": "https://github.com/tinkclaw/tinkclaw-python",
        "Tracker": "https://github.com/tinkclaw/tinkclaw-python/issues",
    },
)
