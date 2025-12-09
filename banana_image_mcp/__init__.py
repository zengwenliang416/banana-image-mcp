"""
Banana Image MCP Server - AI-powered image generation and editing via Gemini.

A production-ready Model Context Protocol server built with FastMCP.
"""

__version__ = "0.1.2"
__author__ = "Wenliang Zeng"
__email__ = "wenliang_zeng416@163.com"
__description__ = "A production-ready MCP server for AI-powered image generation using Gemini"

from .server import create_app, create_wrapper_app, main

__all__ = ["create_app", "create_wrapper_app", "main"]
