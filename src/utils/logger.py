"""
统一日志管理器
提供项目统一的日志配置和输出
"""
import logging
import sys
from typing import Optional


class TradingLogger:
    """交易机器人日志管理器"""
    
    _instance: Optional['TradingLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logger()
            TradingLogger._initialized = True
    
    def _setup_logger(self):
        """设置日志配置"""
        # 创建根日志器
        self.logger = logging.getLogger('trading_bot')
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # 文件处理器
            file_handler = logging.FileHandler('trading_bot.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 格式化器
            console_formatter = logging.Formatter(
                '%(message)s'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            console_handler.setFormatter(console_formatter)
            file_handler.setFormatter(file_formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(f"⚠️ {message}")
    
    def error(self, message: str):
        """错误日志"""
        self.logger.error(f"❌ {message}")
    
    def success(self, message: str):
        """成功日志"""
        self.logger.info(f"✅ {message}")
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(f"🔍 {message}")
    
    def trade_info(self, message: str):
        """交易信息日志"""
        self.logger.info(f"💹 {message}")
    
    def ai_info(self, message: str):
        """AI信息日志"""
        self.logger.info(f"🤖 {message}")
    
    def account_info(self, message: str):
        """账户信息日志"""
        self.logger.info(f"💰 {message}")
    
    def separator(self, title: str = "", length: int = 60):
        """分隔线"""
        if title:
            self.logger.info(f"\n{'='*length}")
            self.logger.info(f"{title}")
            self.logger.info(f"{'='*length}")
        else:
            self.logger.info(f"{'='*length}")


# 全局日志实例
logger = TradingLogger()

# 便捷函数
def log_info(message: str):
    logger.info(message)

def log_warning(message: str):
    logger.warning(message)

def log_error(message: str):
    logger.error(message)

def log_success(message: str):
    logger.success(message)

def log_debug(message: str):
    logger.debug(message)

def log_trade(message: str):
    logger.trade_info(message)

def log_ai(message: str):
    logger.ai_info(message)

def log_account(message: str):
    logger.account_info(message)

def log_separator(title: str = "", length: int = 60):
    logger.separator(title, length)
