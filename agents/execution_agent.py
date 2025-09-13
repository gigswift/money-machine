"""
Execution Agent - Handles trade placement and portfolio management
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent

class ExecutionAgent(BaseAgent):
    """Agent responsible for executing trades and managing portfolio"""
    
    def __init__(self, config: Any, strategy_agent: Any):
        super().__init__("Execution", config)
        self.strategy_agent = strategy_agent
        self.portfolio = {}
        self.positions = {}
        self.trade_history = []
        self.daily_trades = 0
        self.alpaca_api = None
        
    async def initialize(self) -> bool:
        """Initialize execution agent"""
        self.logger.info("Initializing Execution Agent...")
        
        # Initialize portfolio tracking
        for symbol in self.config.SYMBOLS_TO_TRACK:
            self.portfolio[symbol] = {
                'shares': 0,
                'avg_cost': 0.0,
                'total_cost': 0.0,
                'current_value': 0.0,
                'unrealized_pnl': 0.0
            }
        
        # Initialize Alpaca API if keys are available
        if self.config.ALPACA_API_KEY and self.config.ALPACA_SECRET_KEY:
            try:
                import alpaca_trade_api as tradeapi
                self.alpaca_api = tradeapi.REST(
                    key_id=self.config.ALPACA_API_KEY,
                    secret_key=self.config.ALPACA_SECRET_KEY,
                    base_url=self.config.BASE_URL,
                    api_version='v2'
                )
                
                # Test connection
                account = self.alpaca_api.get_account()
                self.logger.info(f"Connected to Alpaca API - Account: {account.status}")
                
            except Exception as e:
                self.logger.warning(f"Alpaca API initialization failed: {e}")
                self.logger.info("Running in simulation mode only")
                self.alpaca_api = None
        else:
            self.logger.info("No Alpaca API keys found - running in simulation mode")
        
        self.logger.info("Execution Agent initialized successfully")
        return True
    
    async def process(self) -> Dict[str, Any]:
        """Main processing - execute trades based on strategy signals"""
        if self.daily_trades >= self.config.MAX_DAILY_TRADES:
            self.logger.warning("Daily trade limit reached")
            return {}
        
        results = {}
        executed_trades = []
        
        # Get signals from strategy agent
        signals = self.strategy_agent.get_signals()
        
        for symbol, signal_info in signals.items():
            try:
                signal = signal_info.get('signal', 'HOLD')
                confidence = signal_info.get('confidence', 0.0)
                
                if signal == 'HOLD' or confidence < 0.7:
                    continue
                
                # Check if we should execute this trade
                should_execute = self._should_execute_trade(symbol, signal, confidence)
                
                if should_execute:
                    trade_result = await self._execute_trade(symbol, signal, confidence)
                    if trade_result:
                        executed_trades.append(trade_result)
                        self.daily_trades += 1
                        self.logger.info(f"Executed {signal} trade for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Error processing trade for {symbol}: {e}")
                continue
        
        # Update portfolio values
        self._update_portfolio_values()
        
        results = {
            'executed_trades': executed_trades,
            'portfolio_value': sum(pos['current_value'] for pos in self.portfolio.values()),
            'daily_trades': self.daily_trades,
            'positions': len([p for p in self.portfolio.values() if p['shares'] != 0])
        }
        
        return results
    
    def _should_execute_trade(self, symbol: str, signal: str, confidence: float) -> bool:
        """Determine if a trade should be executed"""
        
        # Risk management checks
        if confidence < 0.7:
            return False
        
        # Check if we already have a position
        current_position = self.portfolio[symbol]['shares']
        
        if signal == 'BUY' and current_position > 0:
            # Already long, don't add more
            return False
        elif signal == 'SELL' and current_position <= 0:
            # No position to sell or already short
            return False
        
        # Check daily trade limit
        if self.daily_trades >= self.config.MAX_DAILY_TRADES:
            return False
        
        return True
    
    async def _execute_trade(self, symbol: str, signal: str, confidence: float) -> Optional[Dict[str, Any]]:
        """Execute a trade (either real or simulated)"""
        
        # Get current price from data collector
        current_price = self.strategy_agent.data_collector.get_latest_price(symbol)
        if current_price == 0:
            self.logger.warning(f"No price data for {symbol}")
            return None
        
        # Calculate position size (simple strategy: fixed dollar amount)
        position_value = 1000  # $1000 per trade
        shares = int(position_value / current_price)
        
        if shares == 0:
            self.logger.warning(f"Share count is 0 for {symbol} at price ${current_price}")
            return None
        
        # Execute trade
        if self.alpaca_api:
            # Real trading
            trade_result = await self._execute_real_trade(symbol, signal, shares)
        else:
            # Simulated trading
            trade_result = self._execute_simulated_trade(symbol, signal, shares, current_price)
        
        if trade_result:
            # Update portfolio
            self._update_position(symbol, signal, shares, current_price)
            
            # Record trade
            self.trade_history.append({
                'symbol': symbol,
                'signal': signal,
                'shares': shares,
                'price': current_price,
                'value': shares * current_price,
                'timestamp': datetime.now(),
                'confidence': confidence,
                'real_trade': self.alpaca_api is not None
            })
        
        return trade_result
    
    async def _execute_real_trade(self, symbol: str, signal: str, shares: int) -> Optional[Dict[str, Any]]:
        """Execute a real trade via Alpaca API"""
        try:
            side = 'buy' if signal == 'BUY' else 'sell'
            
            # Place market order
            order = self.alpaca_api.submit_order(
                symbol=symbol,
                qty=shares,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            self.logger.info(f"Submitted {side} order for {shares} shares of {symbol}")
            
            return {
                'symbol': symbol,
                'action': signal,
                'shares': shares,
                'order_id': order.id,
                'status': 'submitted',
                'type': 'real'
            }
            
        except Exception as e:
            self.logger.error(f"Real trade execution failed for {symbol}: {e}")
            return None
    
    def _execute_simulated_trade(self, symbol: str, signal: str, shares: int, price: float) -> Dict[str, Any]:
        """Execute a simulated trade"""
        return {
            'symbol': symbol,
            'action': signal,
            'shares': shares,
            'price': price,
            'value': shares * price,
            'status': 'filled',
            'type': 'simulated'
        }
    
    def _update_position(self, symbol: str, signal: str, shares: int, price: float) -> None:
        """Update portfolio position"""
        position = self.portfolio[symbol]
        
        if signal == 'BUY':
            # Add to position
            total_shares = position['shares'] + shares
            total_cost = position['total_cost'] + (shares * price)
            position['avg_cost'] = total_cost / total_shares if total_shares > 0 else 0
            position['shares'] = total_shares
            position['total_cost'] = total_cost
            
        elif signal == 'SELL':
            # Reduce position
            if position['shares'] >= shares:
                position['shares'] -= shares
                # Realize some P&L
                realized_pnl = shares * (price - position['avg_cost'])
                position['total_cost'] = position['shares'] * position['avg_cost']
                self.logger.info(f"Realized P&L for {symbol}: ${realized_pnl:.2f}")
    
    def _update_portfolio_values(self) -> None:
        """Update current values and unrealized P&L"""
        for symbol in self.portfolio:
            position = self.portfolio[symbol]
            if position['shares'] > 0:
                current_price = self.strategy_agent.data_collector.get_latest_price(symbol)
                if current_price > 0:
                    position['current_value'] = position['shares'] * current_price
                    position['unrealized_pnl'] = position['current_value'] - position['total_cost']
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info("Execution Agent cleanup complete")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        total_value = sum(pos['current_value'] for pos in self.portfolio.values())
        total_cost = sum(pos['total_cost'] for pos in self.portfolio.values())
        total_pnl = total_value - total_cost
        
        active_positions = {k: v for k, v in self.portfolio.items() if v['shares'] != 0}
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / total_cost * 100) if total_cost > 0 else 0,
            'active_positions': len(active_positions),
            'positions': active_positions,
            'daily_trades': self.daily_trades,
            'total_trades': len(self.trade_history)
        }
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history"""
        return self.trade_history[-limit:]
