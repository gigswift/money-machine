# Trading Money Machine - Proprietary Trading Application

A multi-agent trading system designed to collect market data, analyze trends, and execute trades automatically.

## Architecture

The system consists of several specialized agents:
- **Data Collection Agent**: Fetches market data from various APIs
- **Analysis Agent**: Processes data using ML models and technical indicators
- **Strategy Agent**: Makes trading decisions based on research-backed strategies
- **Execution Agent**: Handles trade placement and portfolio management
- **Risk Management Agent**: Monitors positions and implements risk controls
- **Web Interface**: Real-time monitoring and manual override capabilities

## APIs Integrated
- Alpha Vantage (market data)
- Alpaca (trading execution)
- Finnhub (global market data)
- IEX Cloud (fundamentals)

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Access the web interface at http://localhost:8080

## Research Foundation

Based on recent PhD research in:
- Machine Learning in Asset Pricing
- Behavioral Finance patterns
- Risk management during market crises
- ESG factor integration
