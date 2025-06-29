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
from system.config import Config, ModelConfig

logger = logging.getLogger(__name__)

class OllamaManager:
    """Manager class for Ollama connections and model operations"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.timeout = Config.OLLAMA_TIMEOUT
        self.models_cache = {}
        self.loaded_models = set()  # Track which models are loaded
        
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
    
    async def load_model(self, model_name: str) -> bool:
        """Load a specific model into memory - with persistence logging"""
        try:
            if model_name in self.loaded_models:
                logger.info(f"Model {model_name} ALREADY LOADED (persistent) - no action needed")
                return True
                
            logger.info(f"Loading model {model_name} for the FIRST TIME...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Make a small request to load the model
                payload = {
                    "model": model_name,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {"num_predict": 1}
                }
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                
                if response.status_code == 200:
                    self.loaded_models.add(model_name)
                    logger.info(f"Successfully loaded model {model_name} - NOW IN MEMORY")
                    return True
                else:
                    logger.error(f"Failed to load model {model_name}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a model from memory (note: Ollama may not support explicit unloading)"""
        try:
            if model_name not in self.loaded_models:
                logger.info(f"Model {model_name} not loaded")
                return True
                
            # For now, we'll just remove it from our tracking
            # Ollama typically manages memory automatically
            logger.info(f"Unloading model {model_name} from tracking...")
            self.loaded_models.discard(model_name)
            logger.info(f"Model {model_name} removed from loaded set")
            return True
                    
        except Exception as e:
            logger.warning(f"Error unloading model {model_name}: {e}")
            # Remove from loaded set anyway since we can't be sure
            self.loaded_models.discard(model_name)
            return True
    
    async def unload_all_models(self) -> bool:
        """Unload all loaded models"""
        logger.info("Clearing loaded models tracking to free memory...")
        
        # Clear the tracking set
        self.loaded_models.clear()
        logger.info("All models removed from tracking")
        
        # Force garbage collection to help free memory
        import gc
        gc.collect()
        
        return True
    
    async def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self.loaded_models)
    
    async def load_required_models(self, required_models: List[str]) -> bool:
        """Load only the required models, keeping already loaded ones for persistence"""
        logger.info(f"Ensuring required models are loaded: {required_models}")
        
        # Get all available models
        available_models = await self.list_available_models()
        
        # Check which required models are available
        missing_models = [model for model in required_models if model not in available_models]
        if missing_models:
            logger.error(f"Required models not available: {missing_models}")
            return False
        
        # Only unload models that are loaded but not required (optional optimization)
        # Comment this out for maximum persistence - keep all loaded models
        # current_loaded = list(self.loaded_models)
        # models_to_unload = [model for model in current_loaded if model not in required_models]
        # 
        # for model in models_to_unload:
        #     await self.unload_model(model)
        
        # Load only models that are NOT already loaded
        success = True
        for model in required_models:
            if model not in self.loaded_models:
                logger.info(f"Model {model} needs loading...")
                if not await self.load_model(model):
                    success = False
            else:
                logger.info(f"Model {model} ALREADY LOADED (persistent) - skipping")
        
        logger.info(f"Currently loaded models: {list(self.loaded_models)} - PERSISTENT IN MEMORY")
        return success

class DirectOllamaLLM:
    """Direct Ollama LLM implementation that bypasses LangChain"""
    
    def __init__(self, model_config: ModelConfig, base_url: str = None, ollama_manager: OllamaManager = None):
        self.model_config = model_config
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.model = model_config.model
        self.system_prompt = model_config.system_prompt
        self.ollama_manager = ollama_manager or ollama_manager
        
    async def ainvoke(self, input_text: str, config: Optional[dict] = None, **kwargs) -> str:
        """Direct async invoke method with TRUE persistence - never unload models"""
        try:
            # PERSISTENCE MODE: Never unload models, they stay loaded for maximum efficiency
            # Lightweight mode is DISABLED for true persistence
            
            # Simply ensure this model is loaded if not already
            if self.ollama_manager:
                # Only load if not already loaded - NEVER unload
                if not await self.ollama_manager.load_model(self.model):
                    logger.warning(f"Model {self.model} might already be loaded, continuing...")
            
            # Format the prompt with system prompt
            full_prompt = ""
            if self.system_prompt:
                full_prompt += f"System: {self.system_prompt}\n\n"
            full_prompt += f"Human: {input_text}\n\nAssistant: "
            
            # Prepare the request
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.model_config.temperature,
                    "num_predict": Config.MAX_RESPONSE_LENGTH
                }
            }
            
            # Make the request
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()
                    
                    # Validate response length
                    if len(response_text) < Config.MIN_RESPONSE_LENGTH:
                        logger.warning(f"Response too short from {self.model_config.name}: {len(response_text)} chars")
                    elif len(response_text) > Config.MAX_RESPONSE_LENGTH:
                        logger.warning(f"Response too long from {self.model_config.name}: {len(response_text)} chars")
                        response_text = response_text[:Config.MAX_RESPONSE_LENGTH] + "..."
                    
                    return response_text
                else:
                    raise Exception(f"Ollama call failed with status code {response.status_code}: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error calling {self.model_config.name}: {e}")
            raise

class CustomOllamaLLM(Ollama):
    """Custom Ollama LLM with enhanced features"""
    
    def __init__(self, model_config: ModelConfig = None, model: str = None, **kwargs):
        # Handle both ModelConfig and direct model string
        if model_config:
            super().__init__(
                model=model_config.model,
                base_url=Config.OLLAMA_BASE_URL,
                temperature=model_config.temperature,
                **kwargs
            )
            # Use object.__setattr__ to bypass Pydantic validation
            object.__setattr__(self, '_model_config', model_config)
            object.__setattr__(self, 'system_prompt', model_config.system_prompt)
            object.__setattr__(self, 'model_name', model_config.name)
        else:
            # Direct model string (for simple testing)
            super().__init__(
                model=model,
                base_url=Config.OLLAMA_BASE_URL,
                temperature=0.7,
                **kwargs
            )
            object.__setattr__(self, '_model_config', None)
            object.__setattr__(self, 'system_prompt', "")
            object.__setattr__(self, 'model_name', model or "unknown")
        
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
    
    async def ainvoke(
        self,
        input: str,
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        """Async invoke method for LangChain compatibility"""
        try:
            # Use direct HTTP call to Ollama API
            import httpx
            
            # Create the full prompt
            if self.system_prompt:
                full_prompt = f"{self.system_prompt}\n\nHuman: {input}\n\nAssistant: "
            else:
                full_prompt = f"Human: {input}\n\nAssistant: "
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": 500  # Limit response length
                }
            }
            
            # Use a shorter timeout and create fresh client
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama call failed with status code {response.status_code}: {response.text}")
                
                result = response.json()
                generated_text = result.get("response", "")
                
                if not generated_text:
                    raise Exception("Empty response from Ollama")
            
            # Basic validation
            generated_text = generated_text.strip()
            if len(generated_text) < 5:
                logger.warning(f"Very short response from {self.model_name}: '{generated_text}'")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error calling {self.model_name}: {e}")
            # Return a meaningful error response instead of raising
            return f"Error: Failed to get response from {self.model_name} - {str(e)}"

class ModelFactory:
    """Factory for creating configured LLM instances"""
    
    def __init__(self, ollama_manager: OllamaManager):
        self.ollama_manager = ollama_manager
        self._models = {}
        self.use_lightweight_mode = False  # Load models on demand
        self.current_loaded_model = None  # Track single loaded model in lightweight mode
    
    def create_orchestrator(self) -> DirectOllamaLLM:
        """Create the orchestrator LLM"""
        if "orchestrator" not in self._models:
            self._models["orchestrator"] = DirectOllamaLLM(Config.ORCHESTRATOR_MODEL, ollama_manager=self.ollama_manager)
        return self._models["orchestrator"]
    
    def create_debater(self, debater_config: ModelConfig) -> DirectOllamaLLM:
        """Create a debater LLM"""
        if debater_config.name not in self._models:
            self._models[debater_config.name] = DirectOllamaLLM(debater_config, ollama_manager=self.ollama_manager)
        return self._models[debater_config.name]
    
    def create_all_debaters(self) -> List[DirectOllamaLLM]:
        """Create all debater LLMs"""
        return [self.create_debater(config) for config in Config.DEBATER_MODELS]
    
    async def initialize_all_models(self) -> bool:
        """Initialize and verify all models are available, loading only required ones"""
        required_models = Config.get_available_models()
        
        # Use the new load_required_models method to manage memory efficiently
        if not await self.ollama_manager.load_required_models(required_models):
            logger.error("Failed to load required models")
            return False
        
        logger.info("All required models loaded successfully")
        return True
    
    async def cleanup_models(self):
        """
        Cleanup and unload all models
        
        Note: This should only be called when the application exits,
        not after each debate. Models should stay loaded for efficiency
        across multiple debates.
        """
        await self.ollama_manager.unload_all_models()
        logger.info("All models unloaded")

# Singleton instances with persistence tracking
import uuid
_instance_id = str(uuid.uuid4())[:8]
ollama_manager = OllamaManager()
model_factory = ModelFactory(ollama_manager)

# Log instance creation for debugging
logger.info(f"🆔 Ollama instance created: {_instance_id} - this should only appear once per session")
