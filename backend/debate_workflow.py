"""
LangGraph workflow for the LLM Debate System
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .models import (
    DebateState, DebateStatus, DebaterResponse, DebateRound, 
    DebateResult, MCPContext
)
from .agents import DebaterAgent, OrchestratorAgent
from .consensus_engine import consensus_engine
from .ollama_integration import model_factory
from system.config import Config

logger = logging.getLogger(__name__)

class DebateWorkflow:
    """LangGraph workflow for managing the debate process"""
    
    def __init__(self):
        self.checkpointer = MemorySaver()
        self.mcp_context = MCPContext()
        self.debater_agents = []
        self.orchestrator_agent = None
        self.graph = None
        self._initialize_agents()
        self._create_graph()
    
    def _initialize_agents(self):
        """Initialize all agents"""
        # Create debater agents
        for debater_config in Config.DEBATER_MODELS:
            agent = DebaterAgent(debater_config, self.mcp_context)
            self.debater_agents.append(agent)
        
        # Create orchestrator agent
        self.orchestrator_agent = OrchestratorAgent(self.mcp_context)
        
        logger.info(f"Initialized {len(self.debater_agents)} debater agents and 1 orchestrator")
    
    def _create_graph(self):
        """Create the LangGraph state machine"""
        
        # Define the workflow graph - use dict type instead of DebateState
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("initialize_debate", self._initialize_debate)
        workflow.add_node("collect_initial_responses", self._collect_initial_responses)
        workflow.add_node("analyze_consensus", self._analyze_consensus)
        workflow.add_node("generate_feedback", self._generate_feedback)
        workflow.add_node("collect_rebuttals", self._collect_rebuttals)
        workflow.add_node("finalize_debate", self._finalize_debate)
        workflow.add_node("handle_max_rounds", self._handle_max_rounds)
        
        # Define the flow
        workflow.set_entry_point("initialize_debate")
        
        workflow.add_edge("initialize_debate", "collect_initial_responses")
        workflow.add_edge("collect_initial_responses", "analyze_consensus")
        
        # Conditional routing from analyze_consensus
        workflow.add_conditional_edges(
            "analyze_consensus",
            self._should_continue_debate,
            {
                "continue": "generate_feedback",
                "consensus": "finalize_debate",
                "max_rounds": "handle_max_rounds"
            }
        )
        
        workflow.add_edge("generate_feedback", "collect_rebuttals")
        workflow.add_edge("collect_rebuttals", "analyze_consensus")
        workflow.add_edge("finalize_debate", END)
        workflow.add_edge("handle_max_rounds", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        logger.info("LangGraph workflow compiled successfully")
    
    async def _initialize_debate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the debate process"""
        # Convert dict to DebateState if needed
        if isinstance(state, dict):
            debate_state = DebateState(**state)
        else:
            debate_state = state
            
        logger.info(f"Initializing debate for question: {debate_state.question}")
        
        debate_state.status = DebateStatus.IN_PROGRESS
        debate_state.current_round = 1
        
        # Reset MCP context for new debate
        self.mcp_context = MCPContext()
        for agent in self.debater_agents:
            agent.mcp_context = self.mcp_context
        self.orchestrator_agent.mcp_context = self.mcp_context
        
        return debate_state.dict()
    
    async def _collect_initial_responses(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect initial responses from all debaters"""
        logger.info("Collecting initial responses from debaters")
        
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        try:
            # Collect responses from all debaters concurrently
            tasks = []
            for agent in self.debater_agents:
                task = agent.generate_initial_response(debate_state.question)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            debate_state.debater_responses = responses
            
            # Create round record
            round_record = DebateRound(
                round_number=debate_state.current_round,
                question=debate_state.question,
                debater_responses=responses
            )
            debate_state.rounds_history.append(round_record)
            
            logger.info(f"Collected {len(responses)} initial responses")
            return debate_state.dict()
            
        except Exception as e:
            logger.error(f"Error collecting initial responses: {e}")
            debate_state.status = DebateStatus.ERROR
            return debate_state.dict()
    
    async def _analyze_consensus(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus between current responses"""
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        logger.info(f"Analyzing consensus for round {debate_state.current_round}")
        
        try:
            if not debate_state.debater_responses:
                logger.warning("No debater responses to analyze")
                return debate_state.dict()
            
            # Analyze consensus
            consensus_analysis = consensus_engine.analyze_consensus(debate_state.debater_responses)
            
            # Update the current round with consensus analysis
            if debate_state.rounds_history:
                debate_state.rounds_history[-1].consensus_analysis = consensus_analysis
            
            # Track consensus evolution
            debate_state.consensus_scores.append(consensus_analysis.average_similarity)
            
            logger.info(f"Consensus analysis: similarity={consensus_analysis.average_similarity:.3f}, "
                       f"reached={consensus_analysis.consensus_reached}")
            
            return debate_state.dict()
            
        except Exception as e:
            logger.error(f"Error analyzing consensus: {e}")
            debate_state.status = DebateStatus.ERROR
            return debate_state.dict()
    
    def _should_continue_debate(self, state: Dict[str, Any]) -> str:
        """Determine if debate should continue based on consensus and round limits"""
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        # Check if we've reached maximum rounds
        if debate_state.current_round >= debate_state.max_rounds:
            return "max_rounds"
        
        # Check if consensus is reached
        if (debate_state.rounds_history and 
            debate_state.rounds_history[-1].consensus_analysis and 
            debate_state.rounds_history[-1].consensus_analysis.consensus_reached):
            return "consensus"
        
        return "continue"
    
    async def _generate_feedback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate orchestrator feedback for the current round"""
        logger.info("Generating orchestrator feedback")
        
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        try:
            feedback, should_continue = await self.orchestrator_agent.analyze_responses_and_provide_feedback(
                debate_state.question,
                debate_state.debater_responses,
                debate_state.current_round
            )
            
            debate_state.orchestrator_feedback = feedback
            
            # Update the current round with feedback
            if debate_state.rounds_history:
                debate_state.rounds_history[-1].orchestrator_feedback = feedback
            
            logger.info("Orchestrator feedback generated successfully")
            return debate_state.dict()
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            debate_state.status = DebateStatus.ERROR
            return debate_state.dict()
    
    async def _collect_rebuttals(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect rebuttal responses from all debaters"""
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        logger.info(f"Collecting rebuttals for round {debate_state.current_round + 1}")
        
        try:
            # Increment round
            debate_state.current_round += 1
            
            # Collect rebuttals from all debaters concurrently
            tasks = []
            for agent in self.debater_agents:
                task = agent.generate_rebuttal(
                    debate_state.question,
                    debate_state.debater_responses,
                    debate_state.orchestrator_feedback,
                    debate_state.current_round
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            debate_state.debater_responses = responses
            
            # Create new round record
            round_record = DebateRound(
                round_number=debate_state.current_round,
                question=debate_state.question,
                debater_responses=responses
            )
            debate_state.rounds_history.append(round_record)
            
            logger.info(f"Collected {len(responses)} rebuttal responses for round {debate_state.current_round}")
            return debate_state.dict()
            
        except Exception as e:
            logger.error(f"Error collecting rebuttals: {e}")
            debate_state.status = DebateStatus.ERROR
            return debate_state.dict()
    
    async def _finalize_debate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize debate when consensus is reached"""
        logger.info("Finalizing debate - consensus reached")
        
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        try:
            # Generate final summary
            all_responses = []
            for round_record in debate_state.rounds_history:
                all_responses.extend(round_record.debater_responses)
            
            final_summary = await self.orchestrator_agent.generate_final_summary(
                debate_state.question,
                all_responses
            )
            
            debate_state.final_summary = final_summary
            debate_state.status = DebateStatus.CONSENSUS_REACHED
            
            logger.info("Debate finalized successfully")
            return debate_state.dict()
            
        except Exception as e:
            logger.error(f"Error finalizing debate: {e}")
            debate_state.status = DebateStatus.ERROR
            return debate_state.dict()
    
    async def _handle_max_rounds(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle case when maximum rounds are reached without consensus"""
        logger.info("Handling max rounds reached")
        
        # Convert dict to DebateState
        debate_state = DebateState(**state)
        
        try:
            # Generate summary based on best available consensus
            all_responses = []
            for round_record in debate_state.rounds_history:
                all_responses.extend(round_record.debater_responses)
            
            final_summary = await self.orchestrator_agent.generate_final_summary(
                debate_state.question,
                all_responses
            )
            
            # Add note about incomplete consensus
            final_summary += f"\n\nNote: Consensus was not fully reached after {debate_state.max_rounds} rounds. " \
                           f"Final similarity score: {debate_state.consensus_scores[-1] if debate_state.consensus_scores else 0:.3f}"
            
            debate_state.final_summary = final_summary
            debate_state.status = DebateStatus.MAX_ROUNDS_EXCEEDED
            
            logger.info("Max rounds handling completed")
            return debate_state.dict()
            
        except Exception as e:
            logger.error(f"Error handling max rounds: {e}")
            debate_state.status = DebateStatus.ERROR
            return debate_state.dict()
    
    async def conduct_debate(self, question: str, max_rounds: int = None) -> DebateResult:
        """Conduct a complete debate and return results"""
        logger.info(f"Starting debate: {question}")
        
        start_time = datetime.now()
        
        # Create initial state
        initial_state = DebateState(
            question=question,
            max_rounds=max_rounds or Config.MAX_ROUNDS,
            consensus_threshold=Config.CONSENSUS_THRESHOLD
        )
        
        try:
            # Run the workflow
            config = {"configurable": {"thread_id": f"debate_{start_time.timestamp()}"}}
            final_state_dict = await self.graph.ainvoke(initial_state.dict(), config)
            
            # Convert dict back to DebateState if needed
            if isinstance(final_state_dict, dict):
                # Create DebateState from dict
                final_state = DebateState(**final_state_dict)
            else:
                final_state = final_state_dict
            
            # Create result
            result = DebateResult(
                original_question=question,
                total_rounds=final_state.current_round,
                final_status=final_state.status,
                rounds=final_state.rounds_history,
                final_summary=final_state.final_summary,
                consensus_evolution=final_state.consensus_scores,
                start_time=start_time
            )
            result.finalize()
            
            logger.info(f"Debate completed: {result.final_status} in {result.total_rounds} rounds")
            return result
            
        except Exception as e:
            logger.error(f"Error in debate workflow: {e}")
            
            # Create error result
            result = DebateResult(
                original_question=question,
                total_rounds=0,
                final_status=DebateStatus.ERROR,
                rounds=[],
                final_summary=f"Debate failed due to error: {str(e)}",
                start_time=start_time
            )
            result.finalize()
            return result

# Global workflow instance
debate_workflow = DebateWorkflow()
