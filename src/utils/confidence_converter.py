"""
信心度转换工具
统一处理字符串信心度到数值的转换
"""
from typing import Union


def convert_confidence_to_float(confidence: Union[str, float, int]) -> float:
    """
    将信心度转换为浮点数
    
    Args:
        confidence: 信心度，可以是字符串('HIGH', 'MEDIUM', 'LOW')或数字
        
    Returns:
        float: 转换后的数值信心度
            - HIGH -> 0.8
            - MEDIUM -> 0.6  
            - LOW -> 0.4
            - 其他字符串 -> 0.5
            - 数字直接返回
    """
    if isinstance(confidence, str):
        conf_str = confidence.upper().strip()
        confidence_map = {
            'HIGH': 0.8,
            'MEDIUM': 0.6,
            'LOW': 0.4
        }
        return confidence_map.get(conf_str, 0.5)
    
    # 如果已经是数字，直接返回
    try:
        return float(confidence)
    except (ValueError, TypeError):
        return 0.5


def convert_confidence_to_string(confidence: Union[str, float, int]) -> str:
    """
    将信心度转换为字符串
    
    Args:
        confidence: 信心度，可以是数字或字符串
        
    Returns:
        str: 转换后的字符串信心度
    """
    if isinstance(confidence, str):
        return confidence.upper().strip()
    
    # 数字转字符串
    try:
        conf_float = float(confidence)
        if conf_float >= 0.75:
            return 'HIGH'
        elif conf_float >= 0.55:
            return 'MEDIUM'
        else:
            return 'LOW'
    except (ValueError, TypeError):
        return 'MEDIUM'
