#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows集成模块，提供Windows右键菜单集成功能。
"""

from .command_handler import CommandArgs, CommandProcessor
from .pywin_handler import PyWinHandler

__all__ = ["PyWinHandler", "CommandProcessor", "CommandArgs"]
