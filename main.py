#!/usr/bin/env python3
"""
Trading Money Machine - Main Application Entry Point
"""
import asyncio
import sys
import signal
import threading
from datetime import datetime

from config.settings import Config
from agents.data_collector import DataCollectorAgent
from agents.strategy_agent import StrategyAgent
from agents.execution_agent import ExecutionAgent
from web_app import app, set_agents, set_running_status

class TradingSystem:
    """Main trading system orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.agents = {}
        self.tasks = []
        self.is_running = False
        self.web_thread = None
        
        print("💰 Trading Money Machine v1.0")
        print("=" * 50)
        print(f"Paper Trading: {self.config.PAPER_TRADING}")
        print(f"Symbols: {', '.join(self.config.SYMBOLS_TO_TRACK)}")
        print(f"Update Frequency: {self.config.UPDATE_FREQUENCY_SECONDS}s")
        print("=" * 50)
    
    async def initialize(self):
        """Initialize all trading agents"""
        print("🚀 Initializing Trading System...")
        
        try:
            # Initialize Data Collector Agent
            print("📊 Initializing Data Collector...")
            self.agents['data_collector'] = DataCollectorAgent(self.config)
            
            # Initialize Strategy Agent
            print("🎯 Initializing Strategy Agent...")
            self.agents['strategy'] = StrategyAgent(self.config, self.agents['data_collector'])
            
            # Initialize Execution Agent
            print("💼 Initializing Execution Agent...")
            self.agents['execution'] = ExecutionAgent(self.config, self.agents['strategy'])
            
            # Initialize all agents
            for name, agent in self.agents.items():
                success = await agent.initialize()
                if not success:
                    print(f"❌ Failed to initialize {name} agent")
                    return False
                print(f"✅ {name.title()} agent initialized")
            
            # Set agents for web interface
            set_agents(self.agents)
            
            print("✅ All agents initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            return False
    
    async def start_trading(self):
        """Start the main trading loop"""
        if not await self.initialize():
            print("❌ Initialization failed. Exiting.")
            return
        
        print("🟢 Starting trading system...")
        self.is_running = True
        set_running_status(True)
        
        try:
            # Start all agent tasks
            self.tasks = [
                asyncio.create_task(agent.start()) 
                for agent in self.agents.values()
            ]
            
            print("🔄 Trading system is now running!")
            print(f"🌐 Web interface available at: http://{self.config.FLASK_HOST}:{self.config.FLASK_PORT}")
            print("📊 Check the dashboard to monitor performance")
            print("\n💡 Press Ctrl+C to stop the system")
            
            # Wait for all tasks to complete (or be cancelled)
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except asyncio.CancelledError:
            print("\n🛑 Received stop signal...")
        except Exception as e:
            print(f"❌ Unexpected error in trading loop: {e}")
        finally:
            await self.stop_trading()
    
    async def stop_trading(self):
        """Stop the trading system gracefully"""
        if not self.is_running:
            return
        
        print("🛑 Stopping trading system...")
        self.is_running = False
        set_running_status(False)
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Stop all agents
        for name, agent in self.agents.items():
            try:
                await agent.stop()
                print(f"✅ {name.title()} agent stopped")
            except Exception as e:
                print(f"⚠️ Error stopping {name} agent: {e}")
        
        print("✅ Trading system stopped successfully!")
    
    def start_web_interface(self):
        """Start the web interface in a separate thread"""
        def run_flask():
            app.run(
                host=self.config.FLASK_HOST,
                port=self.config.FLASK_PORT,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        
        self.web_thread = threading.Thread(target=run_flask, daemon=True)
        self.web_thread.start()
        print(f"🌐 Web interface started at http://{self.config.FLASK_HOST}:{self.config.FLASK_PORT}")

async def main():
    """Main entry point"""
    system = TradingSystem()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}")
        if system.is_running:
            # Cancel the main task which will trigger cleanup
            for task in asyncio.all_tasks():
                if not task.done():
                    task.cancel()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start web interface
    system.start_web_interface()
    
    try:
        # Start trading system
        await system.start_trading()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Trading Money Machine shutdown complete")

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import pandas
    except ImportError:
        missing_deps.append('pandas')
    
    try:
        import numpy
    except ImportError:
        missing_deps.append('numpy')
    
    try:
        import flask
    except ImportError:
        missing_deps.append('flask')
    
    try:
        import requests
    except ImportError:
        missing_deps.append('requests')
    
    try:
        import ta
    except ImportError:
        missing_deps.append('ta')
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n💡 Install missing dependencies with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_configuration():
    """Check if configuration is valid"""
    config = Config()
    warnings = []
    
    # Check API keys
    if not any([config.ALPHA_VANTAGE_API_KEY, config.FINNHUB_API_KEY, config.IEX_CLOUD_API_KEY]):
        warnings.append("No financial data API keys configured")
        warnings.append("The system will use free yfinance data (may be limited)")
    
    if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
        warnings.append("No Alpaca API keys configured")
        warnings.append("The system will run in simulation mode only")
    
    if warnings:
        print("⚠️ Configuration warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        print(f"\n💡 Copy .env.example to .env and add your API keys")
        print("   You can still run the system in demo mode!")
        print()
    
    return True

if __name__ == "__main__":
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("🔍 Checking configuration...")
    check_configuration()
    
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
