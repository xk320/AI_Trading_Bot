"""
AI交易机器人主程序
整合所有模块，实现完整的交易流程
"""
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.binance_client import BinanceClient
from src.config.config_loader import ConfigLoader
from src.config.env_manager import EnvManager
from src.data.market_data import MarketDataManager
from src.data.position_data import PositionDataManager
from src.data.account_data import AccountDataManager
from src.trading.trade_executor import TradeExecutor
from src.trading.position_manager import PositionManager
from src.trading.risk_manager import RiskManager
from src.ai.deepseek_client import DeepSeekClient
from src.ai.prompt_builder import PromptBuilder
from src.ai.decision_parser import DecisionParser
from src.utils.logger import (
    log_info, log_success, log_error, log_warning, 
    log_ai, log_separator
)
from src.utils.confidence_converter import convert_confidence_to_float


class TradingBot:
    """交易机器人主类"""
    
    def __init__(self, config_path: str = 'config/trading_config.json'):
        """初始化交易机器人"""
        log_separator("🚀 AI交易机器人启动中...")
        
        # 加载配置
        self.config = ConfigLoader.load_trading_config(config_path)
        log_success("配置加载完成")
        
        # 加载环境变量
        EnvManager.load_env_file('.env')
        log_success("环境变量加载完成")
        
        # 初始化客户端
        self.client = self._init_binance_client()
        self.ai_client = self._init_ai_client()
        log_success("API客户端初始化完成")
        
        # 初始化管理器
        self.market_data = MarketDataManager(self.client)
        self.position_data = PositionDataManager(self.client)
        self.account_data = AccountDataManager(self.client)
        log_success("数据管理器初始化完成")
        
        # 初始化交易执行器和风险管理器
        self.trade_executor = TradeExecutor(self.client, self.config)
        self.position_manager = PositionManager(self.client)
        self.risk_manager = RiskManager(self.config)
        log_success("交易执行器初始化完成")
        
        # AI组件
        self.prompt_builder = PromptBuilder(self.config)
        self.decision_parser = DecisionParser()
        log_success("AI组件初始化完成")
        
        # 状态追踪
        self.decision_history = []
        self.trade_count = 0
        
        log_separator("🎉 AI交易机器人启动成功！")
        log_info("")
    
    def _init_binance_client(self) -> BinanceClient:
        """初始化Binance客户端（正式网）"""
        api_key, api_secret = EnvManager.get_api_credentials()
        if not api_key or not api_secret:
            raise ValueError("API凭证未配置")
        
        return BinanceClient(api_key=api_key, api_secret=api_secret)
    
    def _init_ai_client(self) -> DeepSeekClient:
        """初始化DeepSeek客户端"""
        api_key = EnvManager.get_deepseek_key()
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 未配置")
        
        model = self.config.get('ai', {}).get('model', 'deepseek-reasoner')
        return DeepSeekClient(api_key=api_key, model=model)
    
    def get_market_data_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """获取单个币种的市场数据"""
        # 多周期K线
        intervals = ['5m', '15m', '1h', '4h', '1d']
        multi_timeframe = self.market_data.get_multi_timeframe_data(symbol, intervals)
        
        # 实时行情
        realtime = self.market_data.get_realtime_market_data(symbol)
        
        return {
            'symbol': symbol,
            'realtime': realtime or {},
            'multi_timeframe': multi_timeframe
        }
    
    def analyze_all_symbols_with_ai(self, all_symbols_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """使用AI一次性分析所有币种"""
        try:
            # 收集所有币种的持仓
            all_positions = {}
            for symbol in all_symbols_data.keys():
                position = self.position_data.get_current_position(symbol)
                if position:
                    all_positions[symbol] = position
            
            # 获取账户摘要
            account_summary = self.account_data.get_account_summary()
            
            # 获取历史决策
            history = self.decision_history[-3:] if self.decision_history else []
            
            # 构建多币种提示词
            prompt = self.prompt_builder.build_multi_symbol_analysis_prompt(
                all_symbols_data=all_symbols_data,
                all_positions=all_positions,
                account_summary=account_summary,
                history=history
            )
            
            # 调用AI
            log_ai("\n调用AI一次性分析所有币种...")
            log_separator("📤 发送给AI的完整提示词")
            log_info(prompt)
            log_separator()
            
            response = self.ai_client.analyze_and_decide(prompt)
            
            # 显示AI推理过程
            reasoning = self.ai_client.get_reasoning(response)
            
            if reasoning:
                log_separator("🧠 AI思维链（详细分析）")
                log_info(reasoning)
                log_separator()
            
            # 显示AI原始回复
            log_separator("🤖 AI原始回复")
            log_info(response['content'])
            log_separator()
            
            # 解析决策
            decisions = self.decision_parser.parse_multi_symbol_response(response['content'])
            
            # 显示所有决策
            log_separator("📊 AI多币种决策总结")
            for symbol, decision in decisions.items():
                log_info(f"   {symbol}: {decision['action']} - {decision['reason']}")
            log_separator()
            
            return decisions
            
        except Exception as e:
            log_error(f"AI分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def analyze_with_ai(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI分析并获取决策"""
        try:
            # 获取持仓
            position = self.position_data.get_current_position(symbol)
            
            # 获取历史决策（最近3条）
            history = [d for d in self.decision_history if d.get('symbol') == symbol][-3:]
            
            # 构建提示词
            prompt = self.prompt_builder.build_analysis_prompt(
                symbol=symbol,
                market_data=market_data,
                position=position,
                history=history
            )
            
            # 调用AI
            log_ai(f"调用AI分析 {symbol}...")
            response = self.ai_client.analyze_and_decide(prompt)
            
            # 解析决策
            decision = self.decision_parser.parse_ai_response(response['content'])
            
            # 显示AI推理过程
            reasoning = self.ai_client.get_reasoning(response)
            if reasoning:
                log_ai(f"{symbol} AI推理:")
                log_info(reasoning)
            
            # 显示决策
            log_ai(f"{symbol} AI决策:")
            log_info(f"   动作: {decision['action']}")
            log_info(f"   信心: {decision['confidence']:.2f}")
            log_info(f"   杠杆: {decision['leverage']}x")
            log_info(f"   仓位: {decision['position_percent']}%")
            log_info(f"   理由: {decision['reason']}")
            
            return decision
            
        except Exception as e:
            log_error(f"AI分析失败 {symbol}: {e}")
            return self.decision_parser._get_default_decision()
    
    def execute_decision(self, symbol: str, decision: Dict[str, Any], market_data: Dict[str, Any]):
        """执行AI决策"""
        action = decision.get('action', 'HOLD')
        confidence = decision.get('confidence', 0.5)
        
        # 确保 confidence 是数字
        confidence = convert_confidence_to_float(confidence)
        
        # 如果信心度太低，不执行
        if confidence < 0.5 and action != 'CLOSE':
            log_warning(f"{symbol} 信心度太低({confidence:.2f})，跳过执行")
            return
        
        try:
            # 获取账户信息
            account_summary = self.account_data.get_account_summary()
            if not account_summary:
                log_warning(f"{symbol} 无法获取账户信息")
                return
            
            total_equity = account_summary['equity']
            
            # 获取当前价格
            current_price = market_data['realtime'].get('price', 0)
            if current_price == 0:
                log_warning(f"{symbol} 无法获取当前价格")
                return
            
            if action == 'BUY_OPEN':
                # 开多仓
                self._open_long(symbol, decision, total_equity, current_price)
                
            elif action == 'SELL_OPEN':
                # 开空仓
                self._open_short(symbol, decision, total_equity, current_price)
                
            elif action == 'CLOSE':
                # 平仓
                self._close_position(symbol, decision)
                
            elif action == 'HOLD':
                # 持有
                log_info(f"💤 {symbol} 保持现状")
                
        except Exception as e:
            log_error(f"执行决策失败 {symbol}: {e}")
    
    def _open_long(self, symbol: str, decision: Dict[str, Any], total_equity: float, current_price: float):
        """开多仓"""
        # 检查账户余额
        if total_equity <= 0:
            log_warning(f"{symbol} 账户余额为0，无法开仓")
            log_warning("   请确保账户有足够的 USDT 余额")
            return
        
        # 检查是否已有持仓
        position = self.position_data.get_current_position(symbol)
        if position:
            log_warning(f"{symbol} 已有持仓，无法开多仓")
            return
        
        # 计算仓位数量
        position_percent = decision['position_percent'] / 100
        position_value = total_equity * position_percent
        quantity = position_value / current_price
        
        # 检查数量是否有效
        if quantity <= 0:
            log_error(f"{symbol} 计算出的数量无效: {quantity} (账户余额: {total_equity})")
            return
        
        # 风险检查
        leverage = decision['leverage']
        ok, errors = self.risk_manager.check_all_risk_limits(
            symbol, quantity, current_price, total_equity, total_equity
        )
        if not ok:
            log_error(f"{symbol} 风控检查失败:")
            for err in errors:
                log_error(f"   - {err}")
            return
        
        # 计算止盈止损价格
        take_profit_percent = decision.get('take_profit_percent', 5.0)
        stop_loss_percent = decision.get('stop_loss_percent', -2.0)
        take_profit = current_price * (1 + take_profit_percent / 100)
        stop_loss = current_price * (1 + stop_loss_percent / 100)
        
        # 执行开仓
        try:
            self.trade_executor.open_long(
                symbol=symbol,
                quantity=quantity,
                leverage=leverage,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            log_success(f"{symbol} 开多仓成功")
            self.trade_count += 1
        except Exception as e:
            log_error(f"{symbol} 开多仓失败: {e}")
    
    def _open_short(self, symbol: str, decision: Dict[str, Any], total_equity: float, current_price: float):
        """开空仓"""
        # 检查账户余额
        if total_equity <= 0:
            log_warning(f"{symbol} 账户余额为0，无法开仓")
            log_warning("   请确保账户有足够的 USDT 余额")
            return
        
        # 检查是否已有持仓
        position = self.position_data.get_current_position(symbol)
        if position:
            log_warning(f"{symbol} 已有持仓，无法开空仓")
            return
        
        # 计算仓位数量
        position_percent = decision['position_percent'] / 100
        position_value = total_equity * position_percent
        quantity = position_value / current_price
        
        # 检查数量是否有效
        if quantity <= 0:
            log_error(f"{symbol} 计算出的数量无效: {quantity} (账户余额: {total_equity})")
            return
        
        # 风险检查
        leverage = decision['leverage']
        ok, errors = self.risk_manager.check_all_risk_limits(
            symbol, quantity, current_price, total_equity, total_equity
        )
        if not ok:
            log_error(f"{symbol} 风控检查失败:")
            for err in errors:
                log_error(f"   - {err}")
            return
        
        # 计算止盈止损价格
        take_profit_percent = decision.get('take_profit_percent', 5.0)
        stop_loss_percent = decision.get('stop_loss_percent', -2.0)
        take_profit = current_price * (1 - take_profit_percent / 100)  # 做空止盈价降低
        stop_loss = current_price * (1 + abs(stop_loss_percent) / 100)  # 做空止损价提高
        
        # 执行开仓
        try:
            self.trade_executor.open_short(
                symbol=symbol,
                quantity=quantity,
                leverage=leverage,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            log_success(f"{symbol} 开空仓成功")
            self.trade_count += 1
        except Exception as e:
            log_error(f"{symbol} 开空仓失败: {e}")
    
    def _close_position(self, symbol: str, decision: Dict[str, Any]):
        """平仓"""
        try:
            self.trade_executor.close_position(symbol)
            log_success(f"{symbol} 平仓成功")
            self.trade_count += 1
        except Exception as e:
            log_error(f"{symbol} 平仓失败: {e}")
    
    def save_decision(self, symbol: str, decision: Dict[str, Any], market_data: Dict[str, Any]):
        """保存决策历史"""
        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': decision['action'],
            'confidence': decision['confidence'],
            'leverage': decision['leverage'],
            'position_percent': decision['position_percent'],
            'reason': decision['reason'],
            'price': market_data['realtime'].get('price', 0)
        }
        self.decision_history.append(decision_record)
        
        # 只保留最近100条
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def run_cycle(self):
        """执行一个交易周期"""
        log_separator(f"📅 交易周期 #{self.trade_count + 1} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取交易币种列表
        symbols = ConfigLoader.get_trading_symbols(self.config)
        
        # 显示账户摘要
        account_summary = self.account_data.get_account_summary()
        if account_summary:
            log_info("\n💰 账户信息:")
            log_info(f"   总权益: {account_summary['equity']:.2f} USDT")
            log_info(f"   未实现盈亏: {account_summary['total_unrealized_pnl']:.2f} USDT")
            log_info(f"   保证金率: {account_summary['margin_ratio']:.2f}%")
        
        # 方式1：多币种一次性分析（优化）
        if len(symbols) > 1:
            # 收集所有币种的数据
            all_symbols_data = {}
            for symbol in symbols:
                market_data = self.get_market_data_for_symbol(symbol)
                position = self.position_data.get_current_position(symbol)
                
                all_symbols_data[symbol] = {
                    'market_data': market_data,
                    'position': position
                }
            
            # 一次性AI分析所有币种
            all_decisions = self.analyze_all_symbols_with_ai(all_symbols_data)
            
            # 执行每个币种的决策
            for symbol, decision in all_decisions.items():
                log_info(f"\n--- {symbol} ---")
                market_data = all_symbols_data[symbol]['market_data']
                self.execute_decision(symbol, decision, market_data)
                
        else:
            # 方式2：单个币种分析（保持兼容）
            for symbol in symbols:
                log_info(f"\n--- {symbol} ---")
                
                # 获取市场数据
                market_data = self.get_market_data_for_symbol(symbol)
                
                # AI分析
                decision = self.analyze_with_ai(symbol, market_data)
                
                # 保存决策
                self.save_decision(symbol, decision, market_data)
                
                # 执行决策
                self.execute_decision(symbol, decision, market_data)
    
    def run(self):
        """启动主循环"""
        schedule_config = ConfigLoader.get_schedule_config(self.config)
        interval_seconds = schedule_config['interval_seconds']
        
        log_info(f"\n⏱️  交易周期: 每{interval_seconds}秒")
        log_info(f"📊 交易币种: {', '.join(ConfigLoader.get_trading_symbols(self.config))}")
        log_info(f"\n按 Ctrl+C 停止运行\n")
        
        try:
            while True:
                start_time = time.time()
                
                # 执行交易周期
                self.run_cycle()
                
                # 等待下一个周期
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    log_info(f"\n💤 等待 {sleep_time:.0f}秒...")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            log_warning("\n\n收到中断信号，正在安全退出...")
            self.shutdown()
    
    def shutdown(self):
        """优雅关闭"""
        log_separator("🛑 交易机器人正在关闭...")
        log_success(f"本次运行交易次数: {self.trade_count}")
        log_success(f"决策记录数量: {len(self.decision_history)}")
        log_success("🎉 交易机器人已安全退出")
        log_separator()


def main():
    """主函数"""
    bot = TradingBot()
    bot.run()


if __name__ == '__main__':
    main()
