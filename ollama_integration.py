"""
Ollama integration for LangChain with local models
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from langchain_community.llms import Ollama
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from config import Config
from models import ModelConfig

logger = logging.getLogger(__name__)

class OllamaManager:
    """Manager class for Ollama connections and model operations"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.timeout = Config.OLLAMA_TIMEOUT
        self.models_cache = {}
        
    async def check_ollama_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def list_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model if it's not available locally"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def ensure_models_available(self, required_models: List[str]) -> Dict[str, bool]:
        """Ensure all required models are available, pull if necessary"""
        available_models = await self.list_available_models()
        model_status = {}
        
        for model in required_models:
            if model in available_models:
                model_status[model] = True
                logger.info(f"Model {model} is available")
            else:
                logger.info(f"Model {model} not found, attempting to pull...")
                success = await self.pull_model(model)
                model_status[model] = success
                if success:
                    logger.info(f"Successfully pulled model {model}")
                else:
                    logger.error(f"Failed to pull model {model}")
        
        return model_status

class CustomOllamaLLM(Ollama):
    """Custom Ollama LLM with enhanced features"""
    
    def __init__(self, model_config: ModelConfig, **kwargs):
        super().__init__(
            model=model_config.model,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=model_config.temperature,
            **kwargs
        )
        self.model_config = model_config
        self.system_prompt = model_config.system_prompt
        
    def format_messages(self, messages: List[BaseMessage]) -> str:
        """Format messages for Ollama"""
        formatted = ""
        
        # Add system prompt
        if self.system_prompt:
            formatted += f"System: {self.system_prompt}\n\n"
        
        # Add conversation messages
        for message in messages:
            if isinstance(message, HumanMessage):
                formatted += f"Human: {message.content}\n\n"
            elif isinstance(message, SystemMessage):
                formatted += f"System: {message.content}\n\n"
            else:
                formatted += f"{message.content}\n\n"
        
        formatted += "Assistant: "
        return formatted
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Async call to Ollama model"""
        try:
            # Use the parent class's async implementation
            response = await super()._acall(prompt, stop, run_manager, **kwargs)
            
            # Validate response length
            if len(response) < Config.MIN_RESPONSE_LENGTH:
                logger.warning(f"Response too short from {self.model_config.name}: {len(response)} chars")
            elif len(response) > Config.MAX_RESPONSE_LENGTH:
                logger.warning(f"Response too long from {self.model_config.name}: {len(response)} chars")
                response = response[:Config.MAX_RESPONSE_LENGTH] + "..."
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error calling {self.model_config.name}: {e}")
            raise

class ModelFactory:
    """Factory for creating configured LLM instances"""
    
    def __init__(self, ollama_manager: OllamaManager):
        self.ollama_manager = ollama_manager
        self._models = {}
    
    def create_orchestrator(self) -> CustomOllamaLLM:
        """Create the orchestrator LLM"""
        if "orchestrator" not in self._models:
            self._models["orchestrator"] = CustomOllamaLLM(Config.ORCHESTRATOR_MODEL)
        return self._models["orchestrator"]
    
    def create_debater(self, debater_config: ModelConfig) -> CustomOllamaLLM:
        """Create a debater LLM"""
        if debater_config.name not in self._models:
            self._models[debater_config.name] = CustomOllamaLLM(debater_config)
        return self._models[debater_config.name]
    
    def create_all_debaters(self) -> List[CustomOllamaLLM]:
        """Create all debater LLMs"""
        return [self.create_debater(config) for config in Config.DEBATER_MODELS]
    
    async def initialize_all_models(self) -> bool:
        """Initialize and verify all models are available"""
        required_models = Config.get_available_models()
        model_status = await self.ollama_manager.ensure_models_available(required_models)
        
        all_available = all(model_status.values())
        if all_available:
            logger.info("All required models are available")
        else:
            missing_models = [model for model, available in model_status.items() if not available]
            logger.error(f"Missing models: {missing_models}")
        
        return all_available

# Singleton instances
ollama_manager = OllamaManager()
model_factory = ModelFactory(ollama_manager)
