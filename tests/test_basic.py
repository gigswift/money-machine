"""
Basic tests for Trading Money Machine
"""
import pytest
import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from agents.data_collector import DataCollectorAgent
from agents.strategy_agent import StrategyAgent
from agents.execution_agent import ExecutionAgent

class TestConfiguration:
    """Test configuration settings"""
    
    def test_config_initialization(self):
        """Test that configuration initializes properly"""
        config = Config()
        
        assert hasattr(config, 'SYMBOLS_TO_TRACK')
        assert hasattr(config, 'PAPER_TRADING')
        assert hasattr(config, 'MAX_DAILY_TRADES')
        assert len(config.SYMBOLS_TO_TRACK) > 0
        assert config.PAPER_TRADING is True  # Default should be True
        assert config.MAX_DAILY_TRADES > 0

class TestAgents:
    """Test agent initialization and basic functionality"""
    
    @pytest.fixture
    def config(self):
        """Fixture providing configuration"""
        return Config()
    
    def test_data_collector_creation(self, config):
        """Test that DataCollectorAgent can be created"""
        agent = DataCollectorAgent(config)
        assert agent.name == "DataCollector"
        assert agent.config == config
        assert agent.is_running is False
    
    def test_strategy_agent_creation(self, config):
        """Test that StrategyAgent can be created"""
        data_collector = DataCollectorAgent(config)
        agent = StrategyAgent(config, data_collector)
        assert agent.name == "Strategy"
        assert agent.config == config
        assert agent.data_collector == data_collector
    
    def test_execution_agent_creation(self, config):
        """Test that ExecutionAgent can be created"""
        data_collector = DataCollectorAgent(config)
        strategy_agent = StrategyAgent(config, data_collector)
        agent = ExecutionAgent(config, strategy_agent)
        assert agent.name == "Execution"
        assert agent.config == config
        assert agent.strategy_agent == strategy_agent

class TestAsyncFunctionality:
    """Test asynchronous functionality"""
    
    @pytest.fixture
    def config(self):
        return Config()
    
    @pytest.mark.asyncio
    async def test_data_collector_initialization(self, config):
        """Test data collector async initialization"""
        agent = DataCollectorAgent(config)
        
        # This should work even without API keys (will use yfinance)
        result = await agent.initialize()
        # Should return True even in demo mode
        assert isinstance(result, bool)
        
        await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_strategy_agent_initialization(self, config):
        """Test strategy agent async initialization"""
        data_collector = DataCollectorAgent(config)
        await data_collector.initialize()
        
        agent = StrategyAgent(config, data_collector)
        result = await agent.initialize()
        assert result is True
        
        await agent.cleanup()
        await data_collector.cleanup()
    
    @pytest.mark.asyncio
    async def test_execution_agent_initialization(self, config):
        """Test execution agent async initialization"""
        data_collector = DataCollectorAgent(config)
        await data_collector.initialize()
        
        strategy_agent = StrategyAgent(config, data_collector)
        await strategy_agent.initialize()
        
        agent = ExecutionAgent(config, strategy_agent)
        result = await agent.initialize()
        assert result is True
        
        await agent.cleanup()
        await strategy_agent.cleanup()
        await data_collector.cleanup()

class TestTradingLogic:
    """Test core trading logic"""
    
    def test_signal_generation_logic(self):
        """Test basic signal generation without external APIs"""
        config = Config()
        data_collector = DataCollectorAgent(config)
        strategy_agent = StrategyAgent(config, data_collector)
        
        # Test signal generation with mock indicators
        mock_indicators = {
            'rsi': 25.0,  # Oversold
            'macd': 0.5,
            'macd_signal': 0.3,
            'bb_upper': 150.0,
            'bb_lower': 140.0,
            'bb_middle': 145.0,
            'sma_20': 142.0,
            'volume_sma': 1000000,
            'price_change_pct': 2.5
        }
        
        signal_info = strategy_agent._generate_signal('TEST', 144.0, mock_indicators)
        
        assert 'signal' in signal_info
        assert 'confidence' in signal_info
        assert 'reasoning' in signal_info
        assert signal_info['signal'] in ['BUY', 'SELL', 'HOLD']
        assert 0.0 <= signal_info['confidence'] <= 1.0
        assert isinstance(signal_info['reasoning'], list)
    
    def test_portfolio_tracking(self):
        """Test basic portfolio tracking functionality"""
        config = Config()
        data_collector = DataCollectorAgent(config)
        strategy_agent = StrategyAgent(config, data_collector)
        execution_agent = ExecutionAgent(config, strategy_agent)
        
        # Test portfolio initialization
        assert 'AAPL' in execution_agent.portfolio
        assert execution_agent.portfolio['AAPL']['shares'] == 0
        assert execution_agent.portfolio['AAPL']['avg_cost'] == 0.0
        
        # Test position update
        execution_agent._update_position('AAPL', 'BUY', 10, 150.0)
        assert execution_agent.portfolio['AAPL']['shares'] == 10
        assert execution_agent.portfolio['AAPL']['avg_cost'] == 150.0
        assert execution_agent.portfolio['AAPL']['total_cost'] == 1500.0

if __name__ == "__main__":
    pytest.main([__file__])
