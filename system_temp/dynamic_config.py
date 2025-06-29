"""
Dynamic model configuration based on locally available Ollama models
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from backend.ollama_integration import ollama_manager
from config import ModelConfig

logger = logging.getLogger(__name__)

@dataclass
class ModelCapability:
    """Information about a model's capabilities"""
    name: str
    size_category: str  # "small", "medium", "large", "extra_large"
    estimated_params: str
    suitable_for_orchestrator: bool
    suitable_for_debater: bool
    personality_match: Optional[str] = None

class DynamicModelSelector:
    """Dynamically select and configure models based on local availability"""
    
    def __init__(self):
        self.available_models = []
        self.model_capabilities = {}
        self._initialize_model_database()
    
    def _initialize_model_database(self):
        """Initialize database of known model capabilities"""
        self.model_capabilities = {
            # Large models - commented out as they're too big for most systems
            # "llama3.1:70b": ModelCapability(
            #     name="llama3.1:70b",
            #     size_category="extra_large",
            #     estimated_params="70B",
            #     suitable_for_orchestrator=True,
            #     suitable_for_debater=False
            # ),
            # "llama3:70b": ModelCapability(
            #     name="llama3:70b", 
            #     size_category="extra_large",
            #     estimated_params="70B",
            #     suitable_for_orchestrator=True,
            #     suitable_for_debater=False
            # ),
            "mixtral:8x7b": ModelCapability(
                name="mixtral:8x7b",
                size_category="large",
                estimated_params="47B",
                suitable_for_orchestrator=True,
                suitable_for_debater=False
            ),
            "qwen2.5:72b": ModelCapability(
                name="qwen2.5:72b",
                size_category="extra_large", 
                estimated_params="72B",
                suitable_for_orchestrator=True,
                suitable_for_debater=False
            ),
            
            # Medium models - can be orchestrator or debater (usually >4GB)
            "llama3.1:8b": ModelCapability(
                name="llama3.1:8b",
                size_category="medium",
                estimated_params="8B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "llama3:8b": ModelCapability(
                name="llama3:8b",
                size_category="medium", 
                estimated_params="8B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "mistral:7b": ModelCapability(
                name="mistral:7b",
                size_category="medium",
                estimated_params="7B", 
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="creative"
            ),
            "phi3:medium": ModelCapability(
                name="phi3:medium",
                size_category="medium",
                estimated_params="14B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="practical"
            ),
            "gemma2:9b": ModelCapability(
                name="gemma2:9b",
                size_category="medium",
                estimated_params="9B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "qwen2.5:7b": ModelCapability(
                name="qwen2.5:7b",
                size_category="medium",
                estimated_params="7B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "codegemma:7b": ModelCapability(
                name="codegemma:7b",
                size_category="medium",
                estimated_params="7B",
                suitable_for_orchestrator=False,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "neural-chat:7b": ModelCapability(
                name="neural-chat:7b",
                size_category="medium",
                estimated_params="7B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="creative"
            ),
            
            # Small models - under 4GB and efficient
            "llama3.2:3b": ModelCapability(
                name="llama3.2:3b",
                size_category="small",
                estimated_params="3B",
                suitable_for_orchestrator=True,  # Can handle orchestration
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "llama3.1:3b": ModelCapability(
                name="llama3.1:3b",
                size_category="small",
                estimated_params="3B",
                suitable_for_orchestrator=True,  # Updated for better capability
                suitable_for_debater=True,
                personality_match="practical"
            ),
            "phi3:mini": ModelCapability(
                name="phi3:mini",
                size_category="small",
                estimated_params="3.8B",
                suitable_for_orchestrator=True,  # Phi3 mini is quite capable
                suitable_for_debater=True,
                personality_match="practical"
            ),
            "phi3:3.8b": ModelCapability(
                name="phi3:3.8b",
                size_category="small",
                estimated_params="3.8B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="practical"
            ),
            "gemma2:2b": ModelCapability(
                name="gemma2:2b",
                size_category="small",
                estimated_params="2B",
                suitable_for_orchestrator=True,  # Small but capable
                suitable_for_debater=True,
                personality_match="creative"
            ),
            "llama3.2:1b": ModelCapability(
                name="llama3.2:1b",
                size_category="tiny",
                estimated_params="1B",
                suitable_for_orchestrator=False,  # Too small for orchestration
                suitable_for_debater=True,
                personality_match="practical"
            ),
            "tinyllama:1.1b": ModelCapability(
                name="tinyllama:1.1b",
                size_category="tiny",
                estimated_params="1.1B",
                suitable_for_orchestrator=False,
                suitable_for_debater=True,
                personality_match="practical"
            ),
            "gemma:2b": ModelCapability(
                name="gemma:2b",
                size_category="small",
                estimated_params="2B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="creative"
            ),
            "qwen2.5:1.5b": ModelCapability(
                name="qwen2.5:1.5b",
                size_category="tiny",
                estimated_params="1.5B",
                suitable_for_orchestrator=False,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "qwen2.5:3b": ModelCapability(
                name="qwen2.5:3b",
                size_category="small",
                estimated_params="3B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "deepseek-coder:1.3b": ModelCapability(
                name="deepseek-coder:1.3b",
                size_category="tiny",
                estimated_params="1.3B",
                suitable_for_orchestrator=False,
                suitable_for_debater=True,
                personality_match="analytical"
            ),
            "starcoder2:3b": ModelCapability(
                name="starcoder2:3b",
                size_category="small",
                estimated_params="3B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            )
        }
    
    async def scan_available_models(self) -> List[str]:
        """Scan for locally available models"""
        try:
            self.available_models = await ollama_manager.list_available_models()
            logger.info(f"Found {len(self.available_models)} available models")
            return self.available_models
        except Exception as e:
            logger.error(f"Error scanning models: {e}")
            return []
    
    def get_model_info(self, model_name: str) -> Optional[ModelCapability]:
        """Get capability information for a model"""
        # Direct match
        if model_name in self.model_capabilities:
            return self.model_capabilities[model_name]
        
        # Try to match without version tags
        base_name = model_name.split(':')[0]
        for known_model, capability in self.model_capabilities.items():
            if known_model.startswith(base_name):
                # Create a copy with the actual model name
                return ModelCapability(
                    name=model_name,
                    size_category=capability.size_category,
                    estimated_params=capability.estimated_params,
                    suitable_for_orchestrator=capability.suitable_for_orchestrator,
                    suitable_for_debater=capability.suitable_for_debater,
                    personality_match=capability.personality_match
                )
        
        # Unknown model - make educated guess based on name
        # Skip extremely large models (70B+) as they're too big for most systems
        if any(size in model_name.lower() for size in ['70b', '72b']):
            return ModelCapability(
                name=model_name,
                size_category="extra_large",
                estimated_params="70B+",
                suitable_for_orchestrator=False,  # Too large for practical use
                suitable_for_debater=False
            )
        elif any(size in model_name.lower() for size in ['7b', '8b', '9b', '13b', '14b']):
            return ModelCapability(
                name=model_name,
                size_category="medium", 
                estimated_params="7-14B",
                suitable_for_orchestrator=True,
                suitable_for_debater=True,
                personality_match="analytical"
            )
        elif any(size in model_name.lower() for size in ['3b', '2b', '1b']):
            return ModelCapability(
                name=model_name,
                size_category="small",
                estimated_params="1-3B",
                suitable_for_orchestrator=False,
                suitable_for_debater=True,
                personality_match="practical"
            )
        
        return None
    
    def select_orchestrator(self) -> Optional[str]:
        """Select the best available model for orchestrator role"""
        orchestrator_candidates = []
        
        for model in self.available_models:
            info = self.get_model_info(model)
            if info and info.suitable_for_orchestrator:
                orchestrator_candidates.append((model, info))
        
        if not orchestrator_candidates:
            return None
        
        # Sort by preference: extra_large > large > medium
        size_priority = {"extra_large": 3, "large": 2, "medium": 1, "small": 0}
        orchestrator_candidates.sort(
            key=lambda x: size_priority.get(x[1].size_category, 0),
            reverse=True
        )
        
        return orchestrator_candidates[0][0]
    
    def select_debaters(self, count: int = 3) -> List[Tuple[str, str]]:
        """Select models for debater roles, returns list of (model, personality)"""
        debater_candidates = []
        
        for model in self.available_models:
            info = self.get_model_info(model)
            if info and info.suitable_for_debater:
                debater_candidates.append((model, info))
        
        if len(debater_candidates) < count:
            # If we don't have enough models, reuse some
            while len(debater_candidates) < count and debater_candidates:
                debater_candidates.extend(debater_candidates[:count - len(debater_candidates)])
        
        # Try to get diverse personalities
        selected_debaters = []
        used_personalities = set()
        
        # First pass - try to get different personalities
        for model, info in debater_candidates:
            if len(selected_debaters) >= count:
                break
            
            personality = info.personality_match or "analytical"
            if personality not in used_personalities:
                selected_debaters.append((model, personality))
                used_personalities.add(personality)
        
        # Second pass - fill remaining slots
        for model, info in debater_candidates:
            if len(selected_debaters) >= count:
                break
            
            personality = info.personality_match or "analytical"
            if (model, personality) not in selected_debaters:
                selected_debaters.append((model, personality))
        
        return selected_debaters[:count]
    
    def create_dynamic_config(self) -> Tuple[Optional[ModelConfig], List[ModelConfig]]:
        """Create dynamic configuration based on available models"""
        
        # Select orchestrator
        orchestrator_model = self.select_orchestrator()
        if not orchestrator_model:
            logger.error("No suitable orchestrator model found")
            return None, []
        
        orchestrator_config = ModelConfig(
            name="Dynamic_Orchestrator",
            model=orchestrator_model,
            temperature=0.3,
            max_tokens=2000,
            personality="analytical and diplomatic",
            system_prompt="""You are an expert debate orchestrator. Your role is to:
1. Analyze responses from debater LLMs
2. Determine if they have reached consensus
3. Provide feedback to help them converge
4. Synthesize final summaries when consensus is reached
Be objective, thorough, and focus on finding common ground."""
        )
        
        # Select debaters
        debater_selections = self.select_debaters(3)
        if len(debater_selections) < 2:
            logger.error("Not enough models for debaters")
            return orchestrator_config, []
        
        debater_configs = []
        personality_prompts = {
            "analytical": """You are an analytical debater who focuses on facts, data, and logical reasoning. 
Provide well-structured arguments based on evidence and clear reasoning. 
Be thorough but concise in your responses.""",
            "creative": """You are a creative debater who brings unique perspectives and innovative thinking.
Explore different angles, consider alternative viewpoints, and think outside the box.
Challenge assumptions while remaining constructive.""",
            "practical": """You are a practical debater focused on real-world applications and solutions.
Emphasize actionable insights, practical implications, and concrete examples.
Bridge theory with practice in your arguments."""
        }
        
        for i, (model, personality) in enumerate(debater_selections):
            config = ModelConfig(
                name=f"Dynamic_Debater_{i+1}_{personality.title()}",
                model=model,
                temperature=0.6 + (i * 0.1),  # Vary temperature slightly
                max_tokens=800,
                personality=f"{personality} and focused",
                system_prompt=personality_prompts.get(personality, personality_prompts["analytical"])
            )
            debater_configs.append(config)
        
        return orchestrator_config, debater_configs
    
    def print_available_models_summary(self):
        """Print a summary of available models and their capabilities"""
        print("\nAvailable Local Models Analysis")
        print("=" * 50)
        
        if not self.available_models:
            print("No models found. Please install some models with 'ollama pull <model>'")
            return
        
        orchestrator_models = []
        debater_models = []
        unknown_models = []
        
        for model in self.available_models:
            info = self.get_model_info(model)
            if not info:
                unknown_models.append(model)
                continue
            
            if info.suitable_for_orchestrator:
                orchestrator_models.append((model, info))
            if info.suitable_for_debater:
                debater_models.append((model, info))
        
        print(f"\nORCHESTRATOR CANDIDATES ({len(orchestrator_models)}):")
        for model, info in sorted(orchestrator_models, key=lambda x: x[1].size_category, reverse=True):
            print(f"  {model} ({info.estimated_params}) - {info.size_category}")
        
        print(f"\nDEBATER CANDIDATES ({len(debater_models)}):")
        for model, info in sorted(debater_models, key=lambda x: x[1].estimated_params):
            personality = info.personality_match or "general"
            print(f"  {model} ({info.estimated_params}) - {personality}")
        
        if unknown_models:
            print(f"\nUNKNOWN MODELS ({len(unknown_models)}):")
            for model in unknown_models:
                print(f"  {model} - capabilities unknown")
        
        # Show recommended configuration
        orchestrator, debaters = self.create_dynamic_config()
        if orchestrator and debaters:
            print(f"\nRECOMMENDED CONFIGURATION:")
            print(f"  Orchestrator: {orchestrator.model}")
            print(f"  Debaters:")
            for debater in debaters:
                print(f"    - {debater.model} ({debater.personality})")
        else:
            print(f"\nINSUFFICIENT MODELS for debate system")
            print("Need at least 1 orchestrator-capable model and 2 debater-capable models")
    
    def get_models_under_size_limit(self, max_size_gb: float = 4.0) -> List[str]:
        """Get available models that are under the specified size limit"""
        # Accurate model sizes in GB based on your actual ollama list output
        model_sizes = {
            # Tiny models (under 1.5GB)
            "tinyllama:1.1b": 0.637,        # 637 MB
            "llama3.2:1b": 1.3,             # 1.3 GB  
            "deepseek-r1:1.5b": 1.1,        # 1.1 GB
            "qwen3:1.7b": 1.4,              # 1.4 GB
            "gemma3:1b": 0.815,             # 815 MB
            
            # Small models (1.5-3GB)
            "gemma2:2b": 1.6,               # 1.6 GB
            "phi3:mini": 2.2,               # 2.2 GB
            "phi3:3.8b": 2.2,               # 2.2 GB (same as mini)
            "phi3:instruct": 2.2,           # 2.2 GB (same as mini)
            "llama3.2:3b": 2.0,             # 2.0 GB
            
            # Medium models (3-4GB) - near limit
            "llama2-uncensored:7b": 3.8,    # 3.8 GB
            "llama2:chat": 3.8,             # 3.8 GB
            "llama2:latest": 3.8,           # 3.8 GB
            
            # Medium-large models (4GB+) - over 4GB limit
            "mistral:7b": 4.1,              # 4.1 GB
            "llama3.1:8b": 4.9,             # 4.9 GB  
            "dolphin3:8b": 4.9,             # 4.9 GB
            "llava:7b": 4.7,                # 4.7 GB
            "llama3:latest": 4.7,           # 4.7 GB
            
            # Large models (40GB+) - commented out as too big
            # "llama3.1:70b": 42.0,           # 42 GB
        }
        
        suitable_models = []
        for model in self.available_models:
            # Check exact match first
            if model in model_sizes:
                if model_sizes[model] <= max_size_gb:
                    suitable_models.append(model)
                    continue
            
            # Check base model name (without tags)
            base_name = model.split(':')[0]
            for known_model, size in model_sizes.items():
                if known_model.startswith(base_name) and size <= max_size_gb:
                    suitable_models.append(model)
                    break
        
        return suitable_models
    
    def select_orchestrator_small(self, max_size_gb: float = 4.0) -> Optional[str]:
        """Select the best available model for orchestrator role under size limit"""
        small_models = self.get_models_under_size_limit(max_size_gb)
        orchestrator_candidates = []
        
        for model in small_models:
            info = self.get_model_info(model)
            if info and info.suitable_for_orchestrator:
                orchestrator_candidates.append((model, info))
        
        if not orchestrator_candidates:
            return None
        
        # Sort by preference: small > tiny (we want the largest small model for orchestrator)
        size_priority = {"small": 2, "tiny": 1}
        orchestrator_candidates.sort(
            key=lambda x: size_priority.get(x[1].size_category, 0),
            reverse=True
        )
        
        return orchestrator_candidates[0][0]
    
    def select_debaters_small(self, count: int = 3, max_size_gb: float = 4.0) -> List[Tuple[str, str]]:
        """Select models for debater roles under size limit"""
        small_models = self.get_models_under_size_limit(max_size_gb)
        debater_candidates = []
        
        for model in small_models:
            info = self.get_model_info(model)
            if info and info.suitable_for_debater:
                debater_candidates.append((model, info))
        
        if len(debater_candidates) < count:
            # If we don't have enough small models, reuse some
            while len(debater_candidates) < count and debater_candidates:
                debater_candidates.extend(debater_candidates[:count - len(debater_candidates)])
        
        # Try to get diverse personalities and sizes
        selected_debaters = []
        used_personalities = set()
        
        # First pass - try to get different personalities
        for model, info in debater_candidates:
            if len(selected_debaters) >= count:
                break
            
            personality = info.personality_match or "analytical"
            if personality not in used_personalities:
                selected_debaters.append((model, personality))
                used_personalities.add(personality)
        
        # Second pass - fill remaining slots
        for model, info in debater_candidates:
            if len(selected_debaters) >= count:
                break
            
            personality = info.personality_match or "analytical"
            if (model, personality) not in selected_debaters:
                selected_debaters.append((model, personality))
        
        return selected_debaters[:count]
    
    def create_small_model_config(self, max_size_gb: float = 4.0) -> Tuple[Optional[ModelConfig], List[ModelConfig]]:
        """Create configuration optimized for models under size limit"""
        
        # Select orchestrator from small models
        orchestrator_model = self.select_orchestrator_small(max_size_gb)
        if not orchestrator_model:
            print(f"No suitable orchestrator model found under {max_size_gb}GB")
            return None, []
        
        orchestrator_config = ModelConfig(
            name="Small_Orchestrator",
            model=orchestrator_model,
            temperature=0.4,  # Slightly higher temp for smaller models
            max_tokens=1500,  # Reduced for smaller models
            personality="analytical and diplomatic",
            system_prompt="""You are a debate orchestrator. Your role is to:
1. Analyze responses from debater LLMs
2. Determine if they have reached consensus
3. Provide feedback to help them converge
4. Synthesize final summaries when consensus is reached
Be concise, objective, and focus on finding common ground."""
        )
        
        # Select debaters from small models
        debater_selections = self.select_debaters_small(3, max_size_gb)
        if len(debater_selections) < 2:
            print(f"Not enough debater models under {max_size_gb}GB (found {len(debater_selections)}, need at least 2)")
            return orchestrator_config, []
        
        debater_configs = []
        personality_prompts = {
            "analytical": """You are an analytical debater focused on facts and logic. 
Provide structured arguments based on evidence. Be concise and clear.""",
            "creative": """You are a creative debater who brings unique perspectives.
Explore different angles and think outside the box. Be constructive.""",
            "practical": """You are a practical debater focused on real-world solutions.
Emphasize actionable insights and concrete examples. Be direct."""
        }
        
        for i, (model, personality) in enumerate(debater_selections):
            config = ModelConfig(
                name=f"Small_Debater_{i+1}_{personality.title()}",
                model=model,
                temperature=0.7 + (i * 0.1),  # Vary temperature
                max_tokens=600,  # Reduced for smaller models
                personality=f"{personality} and focused",
                system_prompt=personality_prompts.get(personality, personality_prompts["analytical"])
            )
            debater_configs.append(config)
        
        return orchestrator_config, debater_configs

async def create_dynamic_debate_config(prefer_small_models: bool = False, max_size_gb: float = 4.0):
    """Create dynamic configuration and return it"""
    selector = DynamicModelSelector()
    
    print("Scanning for available local models...")
    available = await selector.scan_available_models()
    
    if not available:
        print("No models found locally")
        return None, []
    
    if prefer_small_models:
        print(f"\nFiltering for models under {max_size_gb}GB...")
        small_models = selector.get_models_under_size_limit(max_size_gb)
        print(f"Found {len(small_models)} models under {max_size_gb}GB:")
        for model in small_models:
            print(f"  - {model}")
        
        if not small_models:
            print(f"No models found under {max_size_gb}GB")
            print("Consider installing smaller models:")
            print("  ollama pull llama3.2:3b      # 3B model (~1.9GB)")
            print("  ollama pull phi3:mini        # 3.8B model (~2.2GB)")
            print("  ollama pull gemma2:2b        # 2B model (~1.4GB)")
            print("  ollama pull tinyllama:1.1b   # 1.1B model (~0.6GB)")
            return None, []
        
        orchestrator, debaters = selector.create_small_model_config(max_size_gb)
        
        if orchestrator and len(debaters) >= 2:
            print(f"\nSmall model configuration created successfully!")
            print(f"Using {orchestrator.model} as orchestrator (optimized for <{max_size_gb}GB)")
            print(f"Using {len(debaters)} debaters (all under {max_size_gb}GB)")
            
            # Show estimated total memory usage
            total_estimated_gb = 0
            model_sizes = {
                "tinyllama:1.1b": 0.6, "llama3.2:1b": 0.6, "qwen2.5:1.5b": 0.9,
                "gemma2:2b": 1.4, "gemma:2b": 1.4, "qwen2.5:3b": 1.9,
                "llama3.2:3b": 1.9, "llama3.1:3b": 1.9, "phi3:mini": 2.2, "phi3:3.8b": 2.2
            }
            
            if orchestrator.model in model_sizes:
                total_estimated_gb += model_sizes[orchestrator.model]
            for debater in debaters:
                if debater.model in model_sizes:
                    total_estimated_gb += model_sizes[debater.model]
            
            if total_estimated_gb > 0:
                print(f"Estimated total memory usage: ~{total_estimated_gb:.1f}GB")
            
            return orchestrator, debaters
        else:
            print(f"\nCould not create valid small model configuration")
            return None, []
    else:
        # Regular configuration (existing logic)
        selector.print_available_models_summary()
        
        orchestrator, debaters = selector.create_dynamic_config()
        
        if orchestrator and len(debaters) >= 2:
            print(f"\nDynamic configuration created successfully!")
            print(f"Using {orchestrator.model} as orchestrator")
            print(f"Using {len(debaters)} debaters")
            return orchestrator, debaters
        else:
            print(f"\nCould not create valid configuration")
            print("Please install more models or check your Ollama installation")
            return None, []

async def create_small_model_config_only(max_size_gb: float = 4.0):
    """Create configuration using only models under the size limit"""
    return await create_dynamic_debate_config(prefer_small_models=True, max_size_gb=max_size_gb)

if __name__ == "__main__":
    async def main():
        orchestrator, debaters = await create_dynamic_debate_config()
        
        if orchestrator and debaters:
            print("\nGenerated Configuration:")
            print(f"ORCHESTRATOR_MODEL = {orchestrator}")
            print(f"DEBATER_MODELS = {debaters}")
    
    asyncio.run(main())
