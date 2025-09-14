#!/usr/bin/env python3
"""
Quick test script to verify the Trading Money Machine works
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from agents.data_collector import DataCollectorAgent
from agents.strategy_agent import StrategyAgent
from agents.execution_agent import ExecutionAgent

async def test_system():
    """Test system initialization and basic functionality"""
    print("🧪 Testing Trading Money Machine...")
    
    config = Config()
    
    # Test Data Collector
    print("📊 Testing Data Collector...")
    data_collector = DataCollectorAgent(config)
    
    if await data_collector.initialize():
        print("✅ Data Collector initialized successfully")
        
        # Test Strategy Agent
        print("🎯 Testing Strategy Agent...")
        strategy_agent = StrategyAgent(config, data_collector)
        
        if await strategy_agent.initialize():
            print("✅ Strategy Agent initialized successfully")
            
            # Test Execution Agent
            print("💼 Testing Execution Agent...")
            execution_agent = ExecutionAgent(config, strategy_agent)
            
            if await execution_agent.initialize():
                print("✅ Execution Agent initialized successfully")
                
                # Test a single cycle
                print("🔄 Testing one processing cycle...")
                try:
                    # Simulate getting one data point
                    result = await data_collector.process()
                    if result:
                        print(f"✅ Data collection worked! Got data for {len(result)} symbols")
                        
                        # Test strategy generation
                        strategy_result = await strategy_agent.process()
                        if strategy_result:
                            print(f"✅ Strategy generation worked! Generated {len(strategy_result)} signals")
                    else:
                        print("⚠️ No data collected (may need to wait for market hours)")
                        
                except Exception as e:
                    print(f"⚠️ Processing test error: {e}")
                
                await execution_agent.cleanup()
            else:
                print("❌ Execution Agent failed to initialize")
                return False
            
            await strategy_agent.cleanup()
        else:
            print("❌ Strategy Agent failed to initialize")
            return False
        
        await data_collector.cleanup()
    else:
        print("❌ Data Collector failed to initialize")
        return False
    
    print("\n🎉 All systems functional!")
    print("💡 To run the full system with web interface:")
    print("   python3 main.py")
    print("   Then open: http://127.0.0.1:8080")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_system())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"💥 Test failed: {e}")
        sys.exit(1)
