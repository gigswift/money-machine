"""
Trading Money Machine Configuration Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys (to be set in .env file)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
    IEX_CLOUD_API_KEY = os.getenv('IEX_CLOUD_API_KEY', '')
    
    # Trading Configuration
    PAPER_TRADING = True  # Set to False for live trading
    BASE_URL = 'https://paper-api.alpaca.markets' if PAPER_TRADING else 'https://api.alpaca.markets'
    
    # Risk Management
    MAX_PORTFOLIO_RISK = 0.02  # 2% max risk per trade
    MAX_DAILY_TRADES = 10
    STOP_LOSS_PERCENT = 0.05  # 5% stop loss
    TAKE_PROFIT_PERCENT = 0.10  # 10% take profit
    
    # Data Collection
    UPDATE_FREQUENCY_SECONDS = 60  # How often to fetch new data
    SYMBOLS_TO_TRACK = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 
        'NVDA', 'META', 'NFLX', 'AMD', 'CRM'
    ]
    
    # Machine Learning
    LOOKBACK_DAYS = 30
    FEATURE_COLUMNS = [
        'open', 'high', 'low', 'close', 'volume',
        'rsi', 'macd', 'bb_upper', 'bb_lower', 'sma_20'
    ]
    
    # Flask App
    FLASK_HOST = '127.0.0.1'
    FLASK_PORT = 8080
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    DATABASE_PATH = 'data/trading_data.db'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
