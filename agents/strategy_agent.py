"""
Strategy Agent - Makes trading decisions based on technical analysis and ML models
"""
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from .base_agent import BaseAgent

class StrategyAgent(BaseAgent):
    """Agent responsible for making trading decisions"""
    
    def __init__(self, config: Any, data_collector: Any):
        super().__init__("Strategy", config)
        self.data_collector = data_collector
        self.signals = {}  # Store trading signals
        self.ml_model = None
        self.scaler = StandardScaler()
        self.model_trained = False
        
    async def initialize(self) -> bool:
        """Initialize strategy agent"""
        self.logger.info("Initializing Strategy Agent...")
        
        # Initialize signal storage for each symbol
        for symbol in self.config.SYMBOLS_TO_TRACK:
            self.signals[symbol] = {
                'signal': 'HOLD',  # BUY, SELL, HOLD
                'confidence': 0.0,
                'reasoning': [],
                'last_signal_time': None
            }
        
        # Initialize ML model (Random Forest for simplicity)
        self.ml_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.logger.info("Strategy Agent initialized successfully")
        return True
    
    async def process(self) -> Dict[str, Any]:
        """Main processing - analyze data and generate trading signals"""
        results = {}
        
        for symbol in self.config.SYMBOLS_TO_TRACK:
            try:
                # Get latest data from data collector
                price = self.data_collector.get_latest_price(symbol)
                indicators = self.data_collector.get_technical_indicators(symbol)
                
                if not indicators or price == 0:
                    continue
                
                # Generate trading signal
                signal_info = self._generate_signal(symbol, price, indicators)
                
                # Store the signal
                self.signals[symbol].update(signal_info)
                self.signals[symbol]['last_signal_time'] = datetime.now()
                
                # Add to results
                results[symbol] = {
                    'signal': signal_info['signal'],
                    'confidence': signal_info['confidence'],
                    'price': price,
                    'reasoning': signal_info['reasoning'],
                    'timestamp': datetime.now().isoformat()
                }
                
                if signal_info['signal'] != 'HOLD':
                    self.logger.info(f"{symbol}: {signal_info['signal']} signal generated (confidence: {signal_info['confidence']:.2f})")
                
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return results
    
    def _generate_signal(self, symbol: str, price: float, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Generate trading signal based on technical indicators"""
        
        signal = 'HOLD'
        confidence = 0.0
        reasoning = []
        
        try:
            # Technical Analysis Rules (Research-Based)
            buy_signals = 0
            sell_signals = 0
            
            # RSI Strategy (Oversold/Overbought)
            rsi = indicators.get('rsi', 50)
            if rsi < 30:  # Oversold
                buy_signals += 2
                reasoning.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:  # Overbought
                sell_signals += 2
                reasoning.append(f"RSI overbought ({rsi:.1f})")
            
            # MACD Strategy
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            if macd > macd_signal and macd > 0:
                buy_signals += 1
                reasoning.append("MACD bullish crossover")
            elif macd < macd_signal and macd < 0:
                sell_signals += 1
                reasoning.append("MACD bearish crossover")
            
            # Bollinger Bands Strategy
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)
            bb_middle = indicators.get('bb_middle', 0)
            
            if price <= bb_lower:
                buy_signals += 1
                reasoning.append("Price at lower Bollinger Band")
            elif price >= bb_upper:
                sell_signals += 1
                reasoning.append("Price at upper Bollinger Band")
            
            # Moving Average Strategy
            sma_20 = indicators.get('sma_20', 0)
            if price > sma_20 * 1.02:  # 2% above SMA
                buy_signals += 1
                reasoning.append("Price above SMA-20")
            elif price < sma_20 * 0.98:  # 2% below SMA
                sell_signals += 1
                reasoning.append("Price below SMA-20")
            
            # Volume Confirmation
            volume_sma = indicators.get('volume_sma', 1)
            price_change_pct = indicators.get('price_change_pct', 0)
            
            if abs(price_change_pct) > 2:  # Significant price movement
                if price_change_pct > 0:
                    buy_signals += 1
                    reasoning.append(f"Strong upward momentum ({price_change_pct:.1f}%)")
                else:
                    sell_signals += 1
                    reasoning.append(f"Strong downward momentum ({price_change_pct:.1f}%)")
            
            # Generate final signal
            total_signals = buy_signals + sell_signals
            if total_signals > 0:
                if buy_signals > sell_signals:
                    signal = 'BUY'
                    confidence = min(0.95, (buy_signals / max(total_signals, 1)) * 0.8 + 0.2)
                elif sell_signals > buy_signals:
                    signal = 'SELL'
                    confidence = min(0.95, (sell_signals / max(total_signals, 1)) * 0.8 + 0.2)
                else:
                    signal = 'HOLD'
                    confidence = 0.5
            
            # Risk Management - Don't trade if confidence is too low
            if confidence < 0.6:
                signal = 'HOLD'
                reasoning.append("Low confidence - holding position")
            
        except Exception as e:
            self.logger.error(f"Error in signal generation for {symbol}: {e}")
            signal = 'HOLD'
            confidence = 0.0
            reasoning = ["Error in analysis"]
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning
        }
    
    def _should_retrain_model(self) -> bool:
        """Determine if ML model should be retrained"""
        # For now, simple logic - could be enhanced
        return not self.model_trained
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info("Strategy Agent cleanup complete")
    
    def get_signals(self) -> Dict[str, Any]:
        """Get all current trading signals"""
        return self.signals.copy()
    
    def get_signal_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Get trading signal for a specific symbol"""
        return self.signals.get(symbol, {
            'signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': ['No data available'],
            'last_signal_time': None
        })
