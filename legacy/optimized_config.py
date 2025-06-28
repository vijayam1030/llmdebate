"""
Optimized configuration for your current local models under 4GB
"""

import asyncio
from dynamic_config import DynamicModelSelector, ModelConfig

async def create_optimized_config():
    """Create an optimized config using your current models"""
    
    print("🎯 Creating Optimized Configuration for Your Models")
    print("=" * 60)
    
    # Best models from your collection under 4GB:
    # llama3.2:3b (2.0 GB) - Best orchestrator
    # gemma2:2b (1.6 GB) - Creative debater
    # phi3:mini (2.2 GB) - Analytical debater 
    # llama3.2:1b (1.3 GB) - Practical debater
    
    orchestrator_config = ModelConfig(
        name="Optimized_Orchestrator",
        model="llama3.2:3b",  # Your best small model for orchestration
        temperature=0.3,
        max_tokens=1500,
        personality="analytical and diplomatic",
        system_prompt="""You are an expert debate orchestrator. Your role is to:
1. Analyze responses from debater LLMs
2. Determine if they have reached consensus
3. Provide feedback to help them converge
4. Synthesize final summaries when consensus is reached
Be objective, thorough, and focus on finding common ground."""
    )
    
    debater_configs = [
        ModelConfig(
            name="Creative_Debater",
            model="gemma2:2b",  # Google's creative model
            temperature=0.7,
            max_tokens=600,
            personality="creative and innovative",
            system_prompt="""You are a creative debater who brings unique perspectives.
Explore different angles, consider alternative viewpoints, and think outside the box.
Challenge assumptions while remaining constructive."""
        ),
        ModelConfig(
            name="Analytical_Debater", 
            model="phi3:mini",  # Microsoft's efficient analytical model
            temperature=0.6,
            max_tokens=600,
            personality="analytical and fact-focused",
            system_prompt="""You are an analytical debater focused on facts and logic.
Provide structured arguments based on evidence and clear reasoning.
Be thorough but concise in your responses."""
        ),
        ModelConfig(
            name="Practical_Debater",
            model="llama3.2:1b",  # Lightweight but functional
            temperature=0.8,
            max_tokens=600,
            personality="practical and solution-oriented",
            system_prompt="""You are a practical debater focused on real-world solutions.
Emphasize actionable insights, practical implications, and concrete examples.
Bridge theory with practice in your arguments."""
        )
    ]
    
    print("✅ Optimized Configuration Created!")
    print(f"\n🧠 Orchestrator: {orchestrator_config.model} (2.0 GB)")
    print(f"👥 Debaters:")
    print(f"   • {debater_configs[0].model} (1.6 GB) - {debater_configs[0].personality}")
    print(f"   • {debater_configs[1].model} (2.2 GB) - {debater_configs[1].personality}")
    print(f"   • {debater_configs[2].model} (1.3 GB) - {debater_configs[2].personality}")
    print(f"\n📊 Total Estimated Memory: ~7.1 GB")
    print(f"💡 This uses your best models under reasonable memory constraints")
    
    return orchestrator_config, debater_configs

if __name__ == "__main__":
    asyncio.run(create_optimized_config())
