"""
Data Collection Agent - Fetches market data from various APIs
"""
import asyncio
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import ta  # Technical Analysis library

from .base_agent import BaseAgent

class DataCollectorAgent(BaseAgent):
    """Agent responsible for collecting market data from various sources"""
    
    def __init__(self, config: Any):
        super().__init__("DataCollector", config)
        self.api_calls_today = 0
        self.max_api_calls = 500  # Conservative daily limit
        
    async def initialize(self) -> bool:
        """Initialize data collection agent"""
        self.logger.info("Initializing Data Collector Agent...")
        
        # Check if we have at least one API key
        if not any([
            self.config.ALPHA_VANTAGE_API_KEY,
            self.config.FINNHUB_API_KEY,
            self.config.IEX_CLOUD_API_KEY
        ]):
            self.logger.error("No API keys found. Please set at least one in .env file")
            return False
            
        # Initialize data storage structure
        for symbol in self.config.SYMBOLS_TO_TRACK:
            self.data_store[symbol] = {
                'price_data': pd.DataFrame(),
                'technical_indicators': {},
                'last_price': None,
                'last_update': None
            }
        
        self.logger.info(f"Tracking {len(self.config.SYMBOLS_TO_TRACK)} symbols")
        return True
    
    async def process(self) -> Dict[str, Any]:
        """Main processing - fetch and analyze market data"""
        if self.api_calls_today >= self.max_api_calls:
            self.logger.warning("Daily API limit reached, skipping data collection")
            return {}
        
        results = {}
        
        for symbol in self.config.SYMBOLS_TO_TRACK:
            try:
                # Fetch latest price data
                price_data = await self._fetch_price_data(symbol)
                if price_data:
                    # Update stored data
                    self.data_store[symbol]['price_data'] = price_data
                    self.data_store[symbol]['last_price'] = price_data['close'].iloc[-1]
                    self.data_store[symbol]['last_update'] = datetime.now()
                    
                    # Calculate technical indicators
                    indicators = self._calculate_technical_indicators(price_data)
                    self.data_store[symbol]['technical_indicators'] = indicators
                    
                    # Store in results
                    results[symbol] = {
                        'price': self.data_store[symbol]['last_price'],
                        'indicators': indicators,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.logger.info(f"Updated data for {symbol}: ${price_data['close'].iloc[-1]:.2f}")
                
                # Small delay between API calls to be respectful
                await asyncio.sleep(0.2)
                
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        
        return results
    
    async def _fetch_price_data(self, symbol: str) -> pd.DataFrame:
        """Fetch price data for a symbol from available APIs"""
        
        # Try Alpha Vantage first (if key available)
        if self.config.ALPHA_VANTAGE_API_KEY:
            try:
                data = await self._fetch_from_alpha_vantage(symbol)
                if data is not None and not data.empty:
                    return data
            except Exception as e:
                self.logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
        
        # Fallback to yfinance (free but may be rate limited)
        try:
            data = await self._fetch_from_yfinance(symbol)
            if data is not None and not data.empty:
                return data
        except Exception as e:
            self.logger.warning(f"yfinance failed for {symbol}: {e}")
        
        return None
    
    async def _fetch_from_alpha_vantage(self, symbol: str) -> pd.DataFrame:
        """Fetch data from Alpha Vantage API"""
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': '5min',
            'apikey': self.config.ALPHA_VANTAGE_API_KEY,
            'outputsize': 'compact'
        }
        
        response = requests.get(url, params=params)
        self.api_calls_today += 1
        
        if response.status_code == 200:
            data = response.json()
            if 'Time Series (5min)' in data:
                df = pd.DataFrame.from_dict(data['Time Series (5min)'], orient='index')
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df.index = pd.to_datetime(df.index)
                df = df.astype(float)
                df = df.sort_index()
                return df.tail(100)  # Keep last 100 data points
        
        return None
    
    async def _fetch_from_yfinance(self, symbol: str) -> pd.DataFrame:
        """Fetch data using yfinance (fallback option)"""
        import yfinance as yf
        
        # Fetch last 5 days of 5-minute data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d", interval="5m")
        
        if not data.empty:
            # Standardize column names
            data.columns = data.columns.str.lower()
            return data.tail(100)  # Keep last 100 data points
        
        return None
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators from price data"""
        if df.empty or len(df) < 20:
            return {}
        
        try:
            indicators = {}
            
            # RSI (14 period)
            indicators['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
            
            # MACD
            macd_indicator = ta.trend.MACD(df['close'])
            indicators['macd'] = macd_indicator.macd().iloc[-1]
            indicators['macd_signal'] = macd_indicator.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd_indicator.macd_diff().iloc[-1]
            
            # Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(df['close'], window=20)
            indicators['bb_upper'] = bb_indicator.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb_indicator.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb_indicator.bollinger_lband().iloc[-1]
            
            # Simple Moving Averages
            indicators['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator().iloc[-1]
            indicators['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator().iloc[-1] if len(df) >= 50 else None
            
            # Volume indicators
            indicators['volume_sma'] = ta.volume.VolumeSMAIndicator(df['close'], df['volume'], window=20).volume_sma().iloc[-1]
            
            # Price change
            indicators['price_change_pct'] = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info("Data Collector Agent cleanup complete")
        
    def get_latest_price(self, symbol: str) -> float:
        """Get the latest price for a symbol"""
        if symbol in self.data_store:
            return self.data_store[symbol].get('last_price', 0)
        return 0
    
    def get_technical_indicators(self, symbol: str) -> Dict[str, float]:
        """Get technical indicators for a symbol"""
        if symbol in self.data_store:
            return self.data_store[symbol].get('technical_indicators', {})
        return {}
