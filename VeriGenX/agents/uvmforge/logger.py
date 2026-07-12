"""
UVMForge: Structured Logger
Centralized logging for generation, LLM calls, repair, and validation.
"""
import logging
import os

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"uvmforge.{name}")
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            os.makedirs("output/logs", exist_ok=True)
            # File handler
            fh = logging.FileHandler("output/logs/uvmforge.log", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            
            # Format: timestamp | level | module | message
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s', 
                                          datefmt='%Y-%m-%d %H:%M:%S')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
