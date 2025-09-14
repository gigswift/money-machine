# Quick Start Guide - Trading Money Machine

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
cd /Users/rashadbartholomew/Documents/trading-money-machine
pip install -r requirements.txt
```

### Step 2: Configure API Keys (Optional)
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your API keys:
# - Alpha Vantage (free: https://www.alphavantage.co/support/#api-key)
# - Alpaca (paper trading: https://alpaca.markets/)
# - Finnhub (free tier: https://finnhub.io/)
```

**Note**: The system works in demo mode without API keys using free yfinance data!

### Step 3: Run the System
```bash
python3 main.py
```

Then open your browser to: **http://127.0.0.1:8080**

## 🎯 What You'll See

1. **Real-time Dashboard** - Beautiful web interface showing:
   - Live market data for 10 major stocks (AAPL, GOOGL, MSFT, etc.)
   - Trading signals with confidence levels
   - Portfolio performance tracking
   - Recent trade history

2. **Multi-Agent System** running:
   - **Data Collector**: Fetches market data every 60 seconds
   - **Strategy Agent**: Analyzes data using technical indicators (RSI, MACD, Bollinger Bands)
   - **Execution Agent**: Simulates trades based on signals

3. **Research-Based Trading Logic**:
   - RSI oversold/overbought detection
   - MACD crossover strategies
   - Bollinger Band mean reversion
   - Volume confirmation
   - Risk management (stop loss, position sizing)

## 💡 Features

- ✅ **Paper Trading Mode** - Safe simulation environment
- ✅ **Real-time Web Interface** - Monitor everything live
- ✅ **Multiple Data Sources** - Alpha Vantage, yfinance, Finnhub
- ✅ **Technical Analysis** - 10+ indicators implemented
- ✅ **Risk Management** - Built-in safety controls
- ✅ **Extensible Architecture** - Easy to add new strategies

## 🔧 Troubleshooting

**Missing dependencies?**
```bash
pip install flask pandas numpy scikit-learn requests yfinance ta
```

**Want to add API keys later?**
- Edit the `.env` file anytime
- Restart the system to use new keys

**Need help?**
- Check the logs in the terminal
- All trades are simulated by default (safe!)
