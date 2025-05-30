import logging
import sys
from datetime import datetime
from typing import List, Dict, Any
import threading
import queue

class ScrapingLogger:
    """Enhanced logging system for real-time scraping progress tracking."""
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.log_history = []
        self.lock = threading.Lock()
        
        # Setup console logger
        self.logger = logging.getLogger('scraper')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Custom handler for web interface
        web_handler = WebLogHandler(self)
        web_handler.setLevel(logging.DEBUG)
        web_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        )
        web_handler.setFormatter(web_formatter)
        self.logger.addHandler(web_handler)
    
    def log(self, level: str, message: str, extra_data: Dict[str, Any] = None):
        """Log a message with timestamp and optional extra data."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        log_entry = {
            'timestamp': timestamp,
            'level': level.upper(),
            'message': message,
            'extra_data': extra_data or {}
        }
        
        with self.lock:
            self.log_history.append(log_entry)
            self.log_queue.put(log_entry)
        
        # Also log to standard logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
    
    def info(self, message: str, **kwargs):
        """Log info level message."""
        self.log('INFO', message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        self.log('WARNING', message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message."""
        self.log('ERROR', message, kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message."""
        self.log('DEBUG', message, kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message (custom level)."""
        self.log('SUCCESS', message, kwargs)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all log history."""
        with self.lock:
            return self.log_history.copy()
    
    def get_new_logs(self) -> List[Dict[str, Any]]:
        """Get new logs from queue."""
        logs = []
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                logs.append(log_entry)
        except queue.Empty:
            pass
        return logs
    
    def clear_logs(self):
        """Clear log history."""
        with self.lock:
            self.log_history.clear()
            # Clear queue
            try:
                while True:
                    self.log_queue.get_nowait()
            except queue.Empty:
                pass
    
    def format_log_for_display(self, log_entry: Dict[str, Any]) -> str:
        """Format log entry for display."""
        timestamp = log_entry['timestamp']
        level = log_entry['level']
        message = log_entry['message']
        
        # Add extra data if present
        extra_info = ""
        if log_entry.get('extra_data'):
            extra_parts = []
            for key, value in log_entry['extra_data'].items():
                extra_parts.append(f"{key}={value}")
            if extra_parts:
                extra_info = f" [{', '.join(extra_parts)}]"
        
        return f"{timestamp} [{level}] {message}{extra_info}"
    
    def export_logs_to_text(self) -> str:
        """Export all logs to text format."""
        with self.lock:
            lines = []
            lines.append("=" * 80)
            lines.append("GOOGLE IMAGES SCRAPER - SESSION LOGS")
            lines.append("=" * 80)
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Total Log Entries: {len(self.log_history)}")
            lines.append("=" * 80)
            lines.append("")
            
            for log_entry in self.log_history:
                lines.append(self.format_log_for_display(log_entry))
            
            lines.append("")
            lines.append("=" * 80)
            lines.append("END OF LOGS")
            lines.append("=" * 80)
            
            return "\n".join(lines)

class WebLogHandler(logging.Handler):
    """Custom logging handler for web interface."""
    
    def __init__(self, scraping_logger):
        super().__init__()
        self.scraping_logger = scraping_logger
    
    def emit(self, record):
        """Emit log record to web interface."""
        # This is handled by the ScrapingLogger itself
        pass

# Global logger instance
scraping_logger = ScrapingLogger()
