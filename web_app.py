"""
Web Interface for Trading Money Machine
"""
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import asyncio
import threading
from config.settings import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Global variables to store agent references
agents = {}
is_running = False

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    status = {
        'is_running': is_running,
        'timestamp': datetime.now().isoformat(),
        'agents': {}
    }
    
    for name, agent in agents.items():
        if agent:
            status['agents'][name] = agent.get_status()
    
    return jsonify(status)

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio information"""
    execution_agent = agents.get('execution')
    if execution_agent:
        portfolio = execution_agent.get_portfolio_summary()
        return jsonify(portfolio)
    
    return jsonify({'error': 'Execution agent not available'})

@app.route('/api/signals')
def get_signals():
    """Get current trading signals"""
    strategy_agent = agents.get('strategy')
    if strategy_agent:
        signals = strategy_agent.get_signals()
        
        # Convert datetime objects to strings for JSON serialization
        for symbol, signal_info in signals.items():
            if 'last_signal_time' in signal_info and signal_info['last_signal_time']:
                signals[symbol]['last_signal_time'] = signal_info['last_signal_time'].isoformat()
        
        return jsonify(signals)
    
    return jsonify({'error': 'Strategy agent not available'})

@app.route('/api/market_data')
def get_market_data():
    """Get current market data"""
    data_collector = agents.get('data_collector')
    if data_collector:
        market_data = {}
        
        for symbol in Config.SYMBOLS_TO_TRACK:
            price = data_collector.get_latest_price(symbol)
            indicators = data_collector.get_technical_indicators(symbol)
            
            market_data[symbol] = {
                'price': price,
                'indicators': indicators,
                'last_update': data_collector.data_store.get(symbol, {}).get('last_update')
            }
            
            # Convert datetime to string if present
            if market_data[symbol]['last_update']:
                market_data[symbol]['last_update'] = market_data[symbol]['last_update'].isoformat()
        
        return jsonify(market_data)
    
    return jsonify({'error': 'Data collector not available'})

@app.route('/api/trades')
def get_trades():
    """Get recent trade history"""
    execution_agent = agents.get('execution')
    if execution_agent:
        trades = execution_agent.get_trade_history(limit=20)
        
        # Convert datetime objects to strings
        for trade in trades:
            if 'timestamp' in trade and trade['timestamp']:
                trade['timestamp'] = trade['timestamp'].isoformat()
        
        return jsonify(trades)
    
    return jsonify({'error': 'Execution agent not available'})

@app.route('/api/start', methods=['POST'])
def start_system():
    """Start the trading system"""
    global is_running
    # This would be handled by the main application
    # For now, just return success
    return jsonify({'status': 'System start requested'})

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """Stop the trading system"""
    global is_running
    # This would be handled by the main application
    # For now, just return success
    return jsonify({'status': 'System stop requested'})

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    config_data = {
        'symbols_tracked': Config.SYMBOLS_TO_TRACK,
        'paper_trading': Config.PAPER_TRADING,
        'max_daily_trades': Config.MAX_DAILY_TRADES,
        'update_frequency': Config.UPDATE_FREQUENCY_SECONDS,
        'risk_management': {
            'max_portfolio_risk': Config.MAX_PORTFOLIO_RISK,
            'stop_loss_percent': Config.STOP_LOSS_PERCENT,
            'take_profit_percent': Config.TAKE_PROFIT_PERCENT
        }
    }
    return jsonify(config_data)

def set_agents(agent_dict):
    """Set agent references for the web app"""
    global agents
    agents = agent_dict

def set_running_status(status):
    """Set system running status"""
    global is_running
    is_running = status

if __name__ == '__main__':
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)
