"""
Main apfrom .config import Configlication for the LLM Debate System
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from config import Config
from backend.models import DebateResult, DebateStatus
from backend.debate_workflow import debate_workflow
from backend.ollama_integration import ollama_manager, model_factory

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class LLMDebateSystem:
    """Main class for the LLM Debate System"""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the system and check all dependencies"""
        if self.initialized:
            logger.info("System already initialized - skipping reinitalization for model persistence")
            return True
            
        logger.info("Initializing LLM Debate System...")
        
        try:
            # Check Ollama connection
            if not await ollama_manager.check_ollama_connection():
                logger.error(f"Cannot connect to Ollama. Please ensure Ollama is running on {Config.OLLAMA_BASE_URL}")
                return False
            
            # Initialize all models
            if not await model_factory.initialize_all_models():
                logger.error("Failed to initialize all required models")
                return False
            
            logger.info("System initialized successfully")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    async def conduct_debate(self, question: str, max_rounds: Optional[int] = None) -> DebateResult:
        """Conduct a debate on the given question"""
        if not self.initialized:
            if not await self.initialize():
                raise RuntimeError("System initialization failed")
        
        logger.info(f"Starting debate: {question}")
        result = await debate_workflow.conduct_debate(question, max_rounds)
        logger.info(f"Debate completed with status: {result.final_status}")
        
        return result
    
    async def cleanup(self):
        """
        Cleanup resources
        
        Note: This should only be called when the application exits,
        not after each debate. Models should stay loaded for efficiency
        across multiple debates.
        """
        try:
            await model_factory.cleanup_models()
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
        logger.info("System cleanup completed")
    
    def print_debate_summary(self, result: DebateResult):
        """Print a formatted summary of the debate"""
        print("\n" + "="*80)
        print("DEBATE SUMMARY")
        print("="*80)
        print(f"Question: {result.original_question}")
        print(f"Status: {result.final_status.value}")
        print(f"Total Rounds: {result.total_rounds}")
        print(f"Duration: {result.total_duration:.2f} seconds" if result.total_duration else "Duration: N/A")
        
        if result.consensus_evolution:
            print(f"Consensus Evolution: {' → '.join([f'{score:.3f}' for score in result.consensus_evolution])}")
        
        print("\nFINAL SUMMARY:")
        print("-" * 50)
        if result.final_summary:
            print(result.final_summary)
        else:
            print("No summary available")
        
        print("\nDEBATE ROUNDS:")
        print("-" * 50)
        for i, round_data in enumerate(result.rounds, 1):
            print(f"\nRound {i}:")
            for response in round_data.debater_responses:
                print(f"  • {response.debater_name}: {response.response[:100]}...")
            
            if round_data.consensus_analysis:
                print(f"  Consensus: {round_data.consensus_analysis.average_similarity:.3f}")
            
            if round_data.orchestrator_feedback:
                print(f"  Feedback: {round_data.orchestrator_feedback[:100]}...")
        
        print("\n" + "="*80)

async def interactive_mode():
    """Run the system in interactive mode"""
    system = LLMDebateSystem()
    
    print("LLM Debate System - Interactive Mode")
    print("=====================================")
    
    # Initialize system
    print("Initializing system...")
    if not await system.initialize():
        print("System initialization failed. Please check your Ollama installation.")
        return
    
    print("System initialized successfully!")
    print("\nAvailable models:")
    available_models = await ollama_manager.list_available_models()
    for model in available_models:
        print(f"  • {model}")
    
    print("\nEnter your debate questions (type 'quit' to exit):")
    
    while True:
        try:
            question = input("\n🤔 Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            # Optional: Ask for max rounds
            max_rounds_input = input(f"Max rounds (default {Config.MAX_ROUNDS}): ").strip()
            max_rounds = None
            if max_rounds_input.isdigit():
                max_rounds = int(max_rounds_input)
            
            print(f"\nStarting debate with {len(Config.DEBATER_MODELS)} debaters...")
            
            # Conduct debate
            result = await system.conduct_debate(question, max_rounds)
            
            # Print results
            system.print_debate_summary(result)
            
            # Ask if user wants to save results
            save_input = input("\nSave results to file? (y/n): ").strip().lower()
            if save_input in ['y', 'yes']:
                filename = f"debate_result_{int(result.start_time.timestamp())}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Question: {result.original_question}\n")
                    f.write(f"Status: {result.final_status}\n")
                    f.write(f"Rounds: {result.total_rounds}\n")
                    f.write(f"Duration: {result.total_duration:.2f}s\n\n")
                    f.write("Final Summary:\n")
                    f.write(result.final_summary or "No summary available")
                    f.write("\n\nDetailed Rounds:\n")
                    for i, round_data in enumerate(result.rounds, 1):
                        f.write(f"\nRound {i}:\n")
                        for response in round_data.debater_responses:
                            f.write(f"{response.debater_name}: {response.response}\n\n")
                print(f"Results saved to {filename}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"Error: {e}")

def print_help():
    """Print help information"""
    print("""
LLM Debate System - Help
==========================

Usage:
  python main.py                           # Interactive mode
  python main.py "Your question here"      # Single question mode
  python main.py --help                    # Show this help

Examples:
  python main.py "What are the benefits of renewable energy?"
  python main.py "Should AI development be regulated?"

Features:
  • Uses local Ollama models (no internet required)
  • 3 debater LLMs with different personalities
  • 1 orchestrator LLM for consensus detection
  • Iterative refinement until consensus
  • Detailed logging and analytics

Requirements:
  • Ollama installed and running ({Config.OLLAMA_BASE_URL})
  • Required models downloaded (see config.py)
  
Models used:
  • Orchestrator: {Config.ORCHESTRATOR_MODEL.model}
  • Debaters: {', '.join([d.model for d in Config.DEBATER_MODELS])}
""")

async def single_question_mode(question: str):
    """Run a single debate question"""
    system = LLMDebateSystem()
    
    print(f"Conducting debate: {question}")
    print("=" * 60)
    
    # Initialize system
    if not await system.initialize():
        print("System initialization failed.")
        return
    
    # Conduct debate
    result = await system.conduct_debate(question)
    
    # Print results
    system.print_debate_summary(result)

async def main():
    """Main entry point"""
    load_dotenv()  # Load environment variables
    
    args = sys.argv[1:]
    
    if not args:
        # Interactive mode
        await interactive_mode()
    elif args[0] in ['--help', '-h', 'help']:
        # Help mode
        print_help()
    else:
        # Single question mode
        question = ' '.join(args)
        await single_question_mode(question)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)
