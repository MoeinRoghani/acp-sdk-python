"""
ACP Logging Utilities

Provides structured logging with correlation IDs, JSON formatting,
and ACP-specific log formatters for monitoring and debugging.
"""

import json
import logging
import logging.handlers
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

from ..exceptions import ACPException


class CorrelationFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.
    
    The correlation ID can be set per-thread or globally for
    request tracing across the ACP system.
    """
    
    def __init__(self):
        super().__init__()
        self._correlation_id = None
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current context"""
        self._correlation_id = correlation_id
    
    def clear_correlation_id(self):
        """Clear correlation ID"""
        self._correlation_id = None
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return self._correlation_id
    
    def filter(self, record):
        """Add correlation ID to log record"""
        record.correlation_id = self._correlation_id or "no-correlation"
        return True


class JsonFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    
    Formats log records as JSON for easy parsing by log aggregation
    systems like ELK stack, Splunk, or CloudWatch.
    """
    
    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_module: bool = True,
        include_function: bool = True,
        include_line: bool = True,
        include_correlation: bool = True,
        extra_fields: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize JSON formatter.
        
        Args:
            include_timestamp: Include timestamp in output
            include_level: Include log level
            include_logger: Include logger name
            include_module: Include module name
            include_function: Include function name
            include_line: Include line number
            include_correlation: Include correlation ID
            extra_fields: Additional static fields to include
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_module = include_module
        self.include_function = include_function
        self.include_line = include_line
        self.include_correlation = include_correlation
        self.extra_fields = extra_fields or {}
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {}
        
        # Basic fields
        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(record.created).isoformat() + "Z"
        
        if self.include_level:
            log_data["level"] = record.levelname
        
        if self.include_logger:
            log_data["logger"] = record.name
        
        # Location fields
        if self.include_module:
            log_data["module"] = record.module
        
        if self.include_function:
            log_data["function"] = record.funcName
        
        if self.include_line:
            log_data["line"] = record.lineno
        
        # Correlation ID
        if self.include_correlation and hasattr(record, 'correlation_id'):
            log_data["correlationId"] = record.correlation_id
        
        # Message
        log_data["message"] = record.getMessage()
        
        # Exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # ACP specific fields
        if hasattr(record, 'agent_name'):
            log_data["agentName"] = record.agent_name
        
        if hasattr(record, 'task_id'):
            log_data["taskId"] = record.task_id
        
        if hasattr(record, 'stream_id'):
            log_data["streamId"] = record.stream_id
        
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        
        if hasattr(record, 'user_id'):
            log_data["userId"] = record.user_id
        
        # Extra fields from record
        for key, value in record.__dict__.items():
            if (key not in log_data and 
                not key.startswith('_') and 
                key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                           'filename', 'module', 'lineno', 'funcName', 'created', 
                           'msecs', 'relativeCreated', 'thread', 'threadName', 
                           'processName', 'process', 'exc_info', 'exc_text', 'stack_info']):
                try:
                    # Only include JSON-serializable values
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        # Add static extra fields
        log_data.update(self.extra_fields)
        
        return json.dumps(log_data, default=str)


class ACPFormatter(logging.Formatter):
    """
    Human-readable formatter for ACP logs.
    
    Provides colored output and ACP-specific formatting for
    development and debugging.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(
        self,
        use_colors: bool = True,
        include_correlation: bool = True,
        include_location: bool = False
    ):
        """
        Initialize ACP formatter.
        
        Args:
            use_colors: Enable colored output
            include_correlation: Include correlation ID
            include_location: Include file:line information
        """
        self.use_colors = use_colors and sys.stderr.isatty()
        self.include_correlation = include_correlation
        self.include_location = include_location
        
        # Base format
        format_str = "%(asctime)s [%(levelname)s]"
        
        if include_correlation:
            format_str += " [%(correlation_id)s]"
        
        format_str += " %(name)s"
        
        if include_location:
            format_str += " (%(filename)s:%(lineno)d)"
        
        format_str += ": %(message)s"
        
        super().__init__(format_str, datefmt="%Y-%m-%d %H:%M:%S")
    
    def format(self, record):
        """Format log record with colors and ACP context"""
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = "no-correlation"
        
        # Format the record
        formatted = super().format(record)
        
        # Add colors if enabled
        if self.use_colors:
            level_name = record.levelname
            if level_name in self.COLORS:
                color = self.COLORS[level_name]
                reset = self.COLORS['RESET']
                formatted = f"{color}{formatted}{reset}"
        
        return formatted


class ACPLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds ACP-specific context to log records.
    
    Automatically includes agent name, task ID, stream ID, and other
    ACP-specific information in log records.
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        agent_name: Optional[str] = None,
        task_id: Optional[str] = None,
        stream_id: Optional[str] = None,
        user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize logger adapter.
        
        Args:
            logger: Base logger
            agent_name: Agent name
            task_id: Task identifier
            stream_id: Stream identifier
            user_id: User identifier
            extra: Additional context
        """
        context = {}
        
        if agent_name:
            context['agent_name'] = agent_name
        if task_id:
            context['task_id'] = task_id
        if stream_id:
            context['stream_id'] = stream_id
        if user_id:
            context['user_id'] = user_id
        if extra:
            context.update(extra)
        
        super().__init__(logger, context)
    
    def process(self, msg, kwargs):
        """Process log record with ACP context"""
        # Merge extra context
        if 'extra' in kwargs:
            kwargs['extra'].update(self.extra)
        else:
            kwargs['extra'] = self.extra.copy()
        
        return msg, kwargs


def setup_logging(
    level: Union[str, int] = logging.INFO,
    format_type: str = "human",  # "human", "json"
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    include_correlation: bool = True,
    extra_fields: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Setup ACP logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Formatter type ("human" or "json")
        log_file: Optional log file path
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
        include_correlation: Include correlation ID in logs
        extra_fields: Additional static fields for JSON logs
        
    Returns:
        Configured root logger
    """
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set level
    root_logger.setLevel(level)
    
    # Add correlation filter
    correlation_filter = CorrelationFilter()
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.addFilter(correlation_filter)
    
    if format_type == "json":
        console_formatter = JsonFormatter(
            include_correlation=include_correlation,
            extra_fields=extra_fields
        )
    else:
        console_formatter = ACPFormatter(
            include_correlation=include_correlation,
            include_location=level <= logging.DEBUG
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.addFilter(correlation_filter)
        
        # Always use JSON format for file logs
        file_formatter = JsonFormatter(
            include_correlation=include_correlation,
            extra_fields=extra_fields
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set ACP logger level
    acp_logger = logging.getLogger('acp')
    acp_logger.setLevel(level)
    
    return root_logger


def get_logger(
    name: str,
    agent_name: Optional[str] = None,
    task_id: Optional[str] = None,
    stream_id: Optional[str] = None,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> ACPLoggerAdapter:
    """
    Get an ACP logger adapter with context.
    
    Args:
        name: Logger name
        agent_name: Agent name
        task_id: Task identifier
        stream_id: Stream identifier
        user_id: User identifier
        extra: Additional context
        
    Returns:
        Configured ACPLoggerAdapter
    """
    logger = logging.getLogger(name)
    return ACPLoggerAdapter(
        logger=logger,
        agent_name=agent_name,
        task_id=task_id,
        stream_id=stream_id,
        user_id=user_id,
        extra=extra
    )


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for current context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    # Find correlation filter in root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, CorrelationFilter):
                filter_obj.set_correlation_id(correlation_id)


def clear_correlation_id():
    """Clear correlation ID from current context"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, CorrelationFilter):
                filter_obj.clear_correlation_id()


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID.
    
    Returns:
        Current correlation ID or None
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, CorrelationFilter):
                return filter_obj.get_correlation_id()
    return None


class LogContext:
    """
    Context manager for setting correlation ID and other log context.
    
    Example:
        with LogContext(correlation_id="req-123", agent_name="test-agent"):
            logger.info("Processing request")
    """
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        auto_generate: bool = True,
        **extra_context
    ):
        """
        Initialize log context.
        
        Args:
            correlation_id: Correlation ID to set
            auto_generate: Auto-generate correlation ID if not provided
            **extra_context: Additional context to log
        """
        self.correlation_id = correlation_id
        self.auto_generate = auto_generate
        self.extra_context = extra_context
        self.previous_correlation_id = None
    
    def __enter__(self):
        """Enter context - set correlation ID"""
        self.previous_correlation_id = get_correlation_id()
        
        if self.correlation_id:
            set_correlation_id(self.correlation_id)
        elif self.auto_generate:
            set_correlation_id(f"auto-{uuid.uuid4()}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore previous correlation ID"""
        if self.previous_correlation_id:
            set_correlation_id(self.previous_correlation_id)
        else:
            clear_correlation_id()


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "Exception occurred",
    level: int = logging.ERROR,
    include_traceback: bool = True
):
    """
    Log an exception with ACP-specific formatting.
    
    Args:
        logger: Logger to use
        exception: Exception to log
        message: Log message
        level: Log level
        include_traceback: Include full traceback
    """
    extra = {}
    
    # Add ACP exception details
    if isinstance(exception, ACPException):
        extra['error_code'] = exception.code
        extra['error_data'] = exception.data
    
    if include_traceback:
        logger.log(level, message, exc_info=True, extra=extra)
    else:
        extra['exception_type'] = type(exception).__name__
        extra['exception_message'] = str(exception)
        logger.log(level, f"{message}: {exception}", extra=extra)


def configure_library_logging():
    """
    Configure logging for third-party libraries used by ACP.
    
    Reduces verbosity of external libraries while keeping ACP logs visible.
    """
    # Reduce httpx verbosity
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Reduce websockets verbosity  
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    # Reduce uvicorn verbosity
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Reduce fastapi verbosity
    logging.getLogger("fastapi").setLevel(logging.WARNING)


# Performance logging utilities

class PerformanceLogger:
    """Logger for performance metrics and timing"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_timing(
        self,
        operation: str,
        duration: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log operation timing.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            context: Additional context
        """
        extra = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'performance': True
        }
        
        if context:
            extra.update(context)
        
        self.logger.info(f"Operation '{operation}' completed in {duration:.3f}s", extra=extra)


class TimingContext:
    """
    Context manager for timing operations.
    
    Example:
        with TimingContext(logger, "task_processing", task_id="123"):
            # Do work
            pass
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        **context
    ):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
        self.perf_logger = PerformanceLogger(logger)
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.perf_logger.log_timing(self.operation, duration, self.context)
