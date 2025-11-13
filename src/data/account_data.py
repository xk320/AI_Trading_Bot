"""
账户数据管理器
负责获取账户信息
"""
from typing import Dict, Any, Optional
from src.utils.logger import log_warning, log_success, log_error


class AccountDataManager:
    """账户数据管理器"""
    
    def __init__(self, client):
        """
        初始化账户数据管理器
        
        Args:
            client: Binance API客户端
        """
        self.client = client
    
    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """
        获取账户摘要
        
        Returns:
            {
                'total_balance': 10000.0,
                'available_balance': 8000.0,
                'used_margin': 2000.0,
                'total_unrealized_pnl': 100.0,
                'equity': 10100.0,
                'margin_ratio': 0.2,
                ...
            }
        """
        try:
            account = self.client.get_account()
            if not account:
                log_warning("获取账户信息为空")
                return None
            
            # 调试：打印账户信息的键（已禁用）
            
            total_balance = float(account.get('totalWalletBalance', 0) or 0)
            available_balance = float(account.get('availableBalance', 0) or 0)
            
            # 如果totalWalletBalance是0，尝试其他字段
            if total_balance == 0:
                # 尝试其他可能的字段
                for key in ['totalMarginBalance', 'totalCrossWalletBalance', 'availableBalance', 'walletBalance']:
                    val = account.get(key, 0)
                    if val and float(val) > 0:
                        total_balance = float(val)
                        log_success(f"使用备用字段 {key} = {total_balance}")
                        break
            
            return {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'used_margin': float(account.get('totalInitialMargin', 0) or 0),
                'total_unrealized_pnl': float(account.get('totalUnrealizedProfit', 0) or 0),
                'equity': float(account.get('totalMarginBalance', total_balance) or total_balance),
                'margin_ratio': self._calculate_margin_ratio(account),
                'update_time': account.get('updateTime', 0),
                'raw_account': account  # 保存原始数据用于调试
            }
        except Exception as e:
            log_error(f"获取账户摘要失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_margin_ratio(self, account: Dict[str, Any]) -> float:
        """计算保证金率"""
        try:
            total_balance = float(account.get('totalWalletBalance', 0))
            if total_balance == 0:
                return 0.0
            
            used_margin = float(account.get('totalInitialMargin', 0))
            return (used_margin / total_balance) * 100
        except Exception as e:
            log_error(f"计算保证金率失败: {e}")
            return 0.0
    
    def get_available_balance(self) -> float:
        """获取可用余额"""
        summary = self.get_account_summary()
        return summary.get('available_balance', 0.0) if summary else 0.0
    
    def get_total_equity(self) -> float:
        """获取账户总权益"""
        summary = self.get_account_summary()
        return summary.get('equity', 0.0) if summary else 0.0
    
    def get_total_unrealized_pnl(self) -> float:
        """获取总未实现盈亏"""
        summary = self.get_account_summary()
        return summary.get('total_unrealized_pnl', 0.0) if summary else 0.0
