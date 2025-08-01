#!/usr/bin/env python3
"""
ACP Python SDK Setup
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="acp-sdk-python",
    version="1.1.2",
    author="Moein Roghani",
    author_email="moein.roghani@proton.me",
    description="Python implementation of the Agent Communication Protocol (ACP)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/MoeinRoghani/acp-sdk-python",
    project_urls={
        "Bug Tracker": "https://github.com/MoeinRoghani/acp-sdk-python/issues",
        "Documentation": "https://docs.acp-protocol.org",
        "Protocol Specification": "https://acp-protocol.org/spec",
        "Source Code": "https://github.com/MoeinRoghani/acp-sdk-python",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Communications",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Networking",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Typing :: Typed",
    ],
    packages=find_packages(exclude=["tests*", "examples*"]),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "server": ["fastapi>=0.104.0", "uvicorn[standard]>=0.24.0"],
        "client": ["httpx>=0.25.0"],
        "validation": ["pydantic>=2.0.0", "jsonschema>=4.19.0"],
        "all": ["fastapi>=0.104.0", "uvicorn[standard]>=0.24.0", "httpx>=0.25.0", "pydantic>=2.0.0", "jsonschema>=4.19.0"],
        "dev": ["pytest>=7.0.0", "pytest-asyncio>=0.21.0", "black>=23.0.0", "flake8>=6.0.0", "mypy>=1.5.0"],
    },
    entry_points={
        "console_scripts": [
            "acp=acp.cli:main",
            "acp-validate=acp.utils.validation:validate_cli",
            "acp-schema=acp.utils.schema:main",
            "acp-agent-card=acp.utils.agent_card:main",
        ],
    },
    include_package_data=True,
    package_data={
        "acp": [
            "*.yaml", 
            "*.yml", 
            "schemas/*.json",
            "examples/*.json", 
            "templates/*.py"
        ],
    },
    zip_safe=False,
) 