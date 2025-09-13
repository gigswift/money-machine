"""
Base Agent Class - Foundation for all trading agents
"""
import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """Base class for all trading system agents"""
    
    def __init__(self, name: str, config: Any):
        self.name = name
        self.config = config
        self.is_running = False
        self.logger = self._setup_logger()
        self.data_store = {}  # Simple in-memory store
        self.last_update = None
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for this agent"""
        logger = logging.getLogger(f"TradingAgent.{self.name}")
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config.LOG_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent - override in subclasses"""
        pass
    
    @abstractmethod
    async def process(self) -> Dict[str, Any]:
        """Main processing logic - override in subclasses"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources - override in subclasses"""
        pass
    
    async def start(self) -> None:
        """Start the agent's main loop"""
        self.logger.info(f"Starting {self.name} agent...")
        
        if not await self.initialize():
            self.logger.error(f"Failed to initialize {self.name} agent")
            return
        
        self.is_running = True
        
        try:
            while self.is_running:
                start_time = datetime.now()
                
                try:
                    result = await self.process()
                    if result:
                        self.data_store.update(result)
                        self.last_update = datetime.now()
                        
                except Exception as e:
                    self.logger.error(f"Error in {self.name} process: {e}")
                
                # Wait for next cycle
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, self.config.UPDATE_FREQUENCY_SECONDS - elapsed)
                await asyncio.sleep(sleep_time)
                
        except Exception as e:
            self.logger.error(f"Unexpected error in {self.name}: {e}")
        finally:
            await self.cleanup()
    
    async def stop(self) -> None:
        """Stop the agent"""
        self.logger.info(f"Stopping {self.name} agent...")
        self.is_running = False
        await self.cleanup()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'name': self.name,
            'is_running': self.is_running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'data_count': len(self.data_store)
        }
    
    def get_data(self, key: Optional[str] = None) -> Any:
        """Get data from the agent's store"""
        if key:
            return self.data_store.get(key)
        return self.data_store.copy()
