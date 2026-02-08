"""
Logger Configuration - Loguru + Rich Handler Integration
ADR 161: Unified Logging Infrastructure
"""

import sys
from typing import Optional, Dict, Any
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.traceback import Traceback


class RichLogHandler:
    """Rich-enhanced log handler for beautiful terminal output"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.traceback_handler = Traceback()
    
    def format_message(self, record: Dict[str, Any]) -> str:
        """Format log message with Rich styling"""
        level = record["level"].name
        message = record["message"]
        module = record.get("module", "unknown")
        function = record.get("function", "unknown")
        
        # Color code by level
        level_colors = {
            "DEBUG": "dim blue",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red"
        }
        
        level_style = level_colors.get(level, "white")
        
        # Format message
        if level in ["ERROR", "CRITICAL"]:
            # Show full traceback for errors
            if record.get("exception"):
                exception = record["exception"]
                formatted_exception = self.traceback_handler.traceback(*exception)
                return f"[{level_style}]{level}[/]: {message}\n{formatted_exception}"
        
        # Standard format
        timestamp = record.get("time", "")
        return f"[{level_style}]{level}[/]: [{dim cyan}]{module}[/]:[{dim}]{function}[/] {message}"


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_rich: bool = True,
    console_width: Optional[int] = None
) -> None:
    """
    Configure unified logging with Loguru and Rich integration
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        enable_rich: Whether to enable Rich formatting for console
        console_width: Optional console width for Rich formatting
    """
    
    # Remove default handlers
    logger.remove()
    
    # Console handler with Rich formatting
    if enable_rich:
        console = Console(width=console_width, file=sys.stderr)
        rich_handler = RichLogHandler(console)
        
        logger.add(
            lambda record: print(rich_handler.format_message(record), file=sys.stderr),
            level=log_level,
            format="<level>{level}</>: <green>{module}</>:<cyan>{function}</> {message}",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    else:
        # Standard console handler
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</>:<cyan>{function}</> | {message}",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level="DEBUG",  # Always log everything to file
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: <8}</level> | {module}:{function} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            backtrace=True,
            diagnose=True
        )
    
    logger.info(f"📝 Logging configured: level={log_level}, rich={enable_rich}, file={log_file}")


def get_logger(name: Optional[str] = None) -> Any:
    """
    Get a configured logger instance
    
    Args:
        name: Optional logger name (defaults to module name)
    
    Returns:
        Configured Loguru logger
    """
    if name:
        return logger.bind(name=name)
    return logger


class ViewLogger:
    """Specialized logger for view layer components"""
    
    def __init__(self, component_name: str):
        self.logger = logger.bind(component=component_name)
    
    def debug(self, message: str, **kwargs):
        """Debug message with component context"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info message with component context"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning message with component context"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error message with component context"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical message with component context"""
        self.logger.critical(message, **kwargs)


# Factory functions for specialized loggers
def create_view_logger(component_name: str) -> ViewLogger:
    """Create a view-specific logger"""
    return ViewLogger(component_name)


def create_graphics_logger() -> ViewLogger:
    """Create graphics-specific logger"""
    return ViewLogger("graphics")


def create_cli_logger() -> ViewLogger:
    """Create CLI-specific logger"""
    return ViewLogger("cli")


def create_terminal_logger() -> ViewLogger:
    """Create terminal-specific logger"""
    return ViewLogger("terminal")


# Auto-configure logging on import
configure_logging(
    log_level="INFO",
    log_file="logs/dgt_view.log",
    enable_rich=True
)
