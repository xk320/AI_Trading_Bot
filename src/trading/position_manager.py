"""
仓位管理器
负责管理杠杆、止盈止损等
"""
from typing import Dict, Any, Optional
from src.api.binance_client import BinanceClient
from src.utils.logger import log_success, log_error


class PositionManager:
    """仓位管理器"""
    
    def __init__(self, client: BinanceClient):
        """
        初始化仓位管理器
        
        Args:
            client: Binance API客户端
        """
        self.client = client
    
    def modify_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        修改杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数（1-100）
        """
        try:
            result = self.client.change_leverage(symbol, leverage)
            log_success(f"修改杠杆: {symbol} {leverage}x")
            return result
        except Exception as e:
            log_error(f"修改杠杆失败 {symbol} {leverage}x: {e}")
            raise
    
    def set_position_mode(self, hedge_mode: bool = True):
        """
        设置持仓模式
        
        Args:
            hedge_mode: True=双向持仓, False=单向持仓
        """
        try:
            result = self.client.set_hedge_mode(hedge_mode)
            log_success(f"设置持仓模式: {'双向持仓' if hedge_mode else '单向持仓'}")
            return result
        except Exception as e:
            log_error(f"设置持仓模式失败: {e}")
            raise
    
    def set_margin_type(self, symbol: str, margin_type: str = 'ISOLATED'):
        """
        设置保证金类型
        
        Args:
            symbol: 交易对
            margin_type: 'ISOLATED'(逐仓) 或 'CROSSED'(全仓)
        """
        try:
            result = self.client.change_margin_type(symbol, margin_type)
            log_success(f"设置保证金类型: {symbol} {margin_type}")
            return result
        except Exception as e:
            log_error(f"设置保证金类型失败 {symbol}: {e}")
            raise
    
    def get_position_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓信息"""
        return self.client.get_position(symbol)
    
    def calculate_position_value(self, symbol: str, quantity: float, price: float) -> float:
        """计算持仓价值"""
        return quantity * price
    
    def calculate_required_margin(self, quantity: float, price: float, leverage: int) -> float:
        """
        计算所需保证金
        
        Args:
            quantity: 数量
            price: 价格
            leverage: 杠杆倍数
            
        Returns:
            所需保证金
            
        Raises:
            ValueError: 当杠杆倍数无效时
        """
        if leverage <= 0:
            raise ValueError(f"杠杆倍数必须大于0，当前值: {leverage}")
        
        if leverage > 100:
            raise ValueError(f"杠杆倍数不能超过100，当前值: {leverage}")
        
        position_value = quantity * price
        return position_value / leverage
