"""
LangChain agents for debater LLMs and orchestrator
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.schema import HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate

from models import DebaterResponse, MCPContext, ModelConfig
from ollama_integration import CustomOllamaLLM, model_factory
from consensus_engine import consensus_engine
from config import Config

logger = logging.getLogger(__name__)

class DebaterAgent:
    """Individual debater agent with specific personality and reasoning style"""
    
    def __init__(self, config: ModelConfig, mcp_context: MCPContext):
        self.config = config
        self.llm = model_factory.create_debater(config)
        self.mcp_context = mcp_context
        self.response_history = []
        
    async def generate_initial_response(self, question: str) -> DebaterResponse:
        """Generate initial response to the debate question"""
        try:
            prompt = self._create_initial_prompt(question)
            response = await self.llm._acall(prompt)
            
            debater_response = DebaterResponse(
                debater_name=self.config.name,
                model=self.config.model,
                response=response,
                round_number=1,
                response_length=len(response)
            )
            
            self.response_history.append(debater_response)
            self._update_mcp_context(response)
            
            return debater_response
            
        except Exception as e:
            logger.error(f"Error generating initial response for {self.config.name}: {e}")
            raise
    
    async def generate_rebuttal(
        self, 
        question: str, 
        other_responses: List[DebaterResponse], 
        orchestrator_feedback: str,
        round_number: int
    ) -> DebaterResponse:
        """Generate rebuttal based on other debaters' responses and orchestrator feedback"""
        try:
            prompt = self._create_rebuttal_prompt(question, other_responses, orchestrator_feedback)
            response = await self.llm._acall(prompt)
            
            debater_response = DebaterResponse(
                debater_name=self.config.name,
                model=self.config.model,
                response=response,
                round_number=round_number,
                response_length=len(response)
            )
            
            self.response_history.append(debater_response)
            self._update_mcp_context(response)
            
            return debater_response
            
        except Exception as e:
            logger.error(f"Error generating rebuttal for {self.config.name}: {e}")
            raise
    
    def _create_initial_prompt(self, question: str) -> str:
        """Create prompt for initial response"""
        context_info = ""
        if self.mcp_context.shared_knowledge:
            context_info = f"\nShared Context: {self.mcp_context.shared_knowledge}\n"
        
        prompt = f"""
{self.config.system_prompt}

{context_info}

Question for debate: {question}

Please provide your perspective on this question. Consider your unique viewpoint as a {self.config.personality} debater.

Be thorough but concise (aim for {Config.MIN_RESPONSE_LENGTH}-{Config.MAX_RESPONSE_LENGTH} characters).
Structure your response clearly with key points and supporting reasoning.

Your response:
"""
        return prompt
    
    def _create_rebuttal_prompt(
        self, 
        question: str, 
        other_responses: List[DebaterResponse], 
        orchestrator_feedback: str
    ) -> str:
        """Create prompt for rebuttal response"""
        
        # Format other responses
        other_responses_text = ""
        for resp in other_responses:
            if resp.debater_name != self.config.name:
                other_responses_text += f"\n{resp.debater_name}: {resp.response}\n"
        
        # Include MCP context
        context_info = ""
        if self.mcp_context.agreed_facts:
            context_info += f"\nAgreed Facts: {'; '.join(self.mcp_context.agreed_facts)}"
        if self.mcp_context.disputed_points:
            context_info += f"\nDisputed Points: {'; '.join(self.mcp_context.disputed_points)}"
        
        prompt = f"""
{self.config.system_prompt}

Original Question: {question}

{context_info}

Other Debaters' Responses:
{other_responses_text}

Orchestrator Feedback: {orchestrator_feedback}

Your Previous Response: {self.response_history[-1].response if self.response_history else "None"}

Based on the other responses and feedback, please refine your position. You should:
1. Address any valid points raised by other debaters
2. Clarify or strengthen your arguments where needed
3. Find common ground where possible
4. Maintain your unique {self.config.personality} perspective

Aim for convergence while preserving the strength of your arguments.

Your refined response:
"""
        return prompt
    
    def _update_mcp_context(self, response: str):
        """Update MCP context with information from this response"""
        # Add to conversation history
        self.mcp_context.conversation_history.append(f"{self.config.name}: {response}")
        
        # Simple keyword extraction for key concepts
        response_lower = response.lower()
        potential_concepts = []
        
        # Look for phrases that indicate key concepts
        concept_patterns = [
            "the main point is", "key factor", "important aspect", "crucial element",
            "significant", "primary reason", "fundamental", "essential"
        ]
        
        for pattern in concept_patterns:
            if pattern in response_lower:
                # Extract the sentence containing the pattern
                sentences = response.split('.')
                for sentence in sentences:
                    if pattern in sentence.lower():
                        potential_concepts.append(sentence.strip())
        
        # Add unique concepts
        for concept in potential_concepts:
            if concept not in self.mcp_context.key_concepts:
                self.mcp_context.key_concepts.append(concept)

class OrchestratorAgent:
    """Orchestrator agent that manages the debate flow and consensus detection"""
    
    def __init__(self, mcp_context: MCPContext):
        self.llm = model_factory.create_orchestrator()
        self.mcp_context = mcp_context
        
    async def analyze_responses_and_provide_feedback(
        self, 
        question: str, 
        responses: List[DebaterResponse],
        round_number: int
    ) -> tuple[str, bool]:
        """Analyze responses and provide feedback. Returns (feedback, should_continue)"""
        
        try:
            # First, check consensus using the consensus engine
            consensus_analysis = consensus_engine.analyze_consensus(responses)
            
            # Update MCP context with consensus information
            if consensus_analysis.consensus_reached:
                # Extract agreed points
                for resp in responses:
                    key_points = consensus_engine.extract_key_points(resp.response)
                    for point in key_points:
                        self.mcp_context.add_agreed_fact(point)
            else:
                # Identify disagreement areas
                disagreements = consensus_engine.identify_disagreement_areas(responses)
                for disagreement in disagreements:
                    self.mcp_context.add_disputed_point(disagreement)
            
            # Generate orchestrator feedback
            feedback = await self._generate_feedback(question, responses, consensus_analysis, round_number)
            
            return feedback, not consensus_analysis.consensus_reached
            
        except Exception as e:
            logger.error(f"Error in orchestrator analysis: {e}")
            return "Error in analysis. Please continue with your best reasoning.", True
    
    async def generate_final_summary(
        self, 
        question: str, 
        all_responses: List[DebaterResponse]
    ) -> str:
        """Generate final summary when consensus is reached"""
        
        try:
            prompt = self._create_summary_prompt(question, all_responses)
            summary = await self.llm._acall(prompt)
            return summary
            
        except Exception as e:
            logger.error(f"Error generating final summary: {e}")
            return "Unable to generate summary due to technical error."
    
    def _create_summary_prompt(self, question: str, all_responses: List[DebaterResponse]) -> str:
        """Create prompt for final summary generation"""
        
        # Group responses by round
        rounds_text = ""
        current_round = 1
        round_responses = []
        
        for resp in all_responses:
            if resp.round_number != current_round:
                if round_responses:
                    rounds_text += f"\nRound {current_round}:\n"
                    for r in round_responses:
                        rounds_text += f"- {r.debater_name}: {r.response[:200]}...\n"
                current_round = resp.round_number
                round_responses = []
            round_responses.append(resp)
        
        # Add the last round
        if round_responses:
            rounds_text += f"\nRound {current_round}:\n"
            for r in round_responses:
                rounds_text += f"- {r.debater_name}: {r.response[:200]}...\n"
        
        # Include MCP context
        context_summary = ""
        if self.mcp_context.agreed_facts:
            context_summary += f"\nKey Agreed Points: {'; '.join(self.mcp_context.agreed_facts[:5])}"
        
        prompt = f"""
{Config.ORCHESTRATOR_MODEL.system_prompt}

Original Question: {question}

Debate Evolution:
{rounds_text}

{context_summary}

The debaters have reached consensus. Please provide a comprehensive summary that:

1. Clearly answers the original question
2. Integrates the key insights from all debaters
3. Highlights the main points of agreement
4. Provides a balanced and nuanced perspective
5. Acknowledges any remaining complexities or nuances

Keep the summary focused and well-structured (aim for 300-800 words).

Final Summary:
"""
        return prompt
    
    async def _generate_feedback(
        self, 
        question: str, 
        responses: List[DebaterResponse], 
        consensus_analysis, 
        round_number: int
    ) -> str:
        """Generate feedback for debaters"""
        
        responses_text = ""
        for resp in responses:
            responses_text += f"\n{resp.debater_name} ({resp.model}): {resp.response}\n"
        
        convergence_strategies = consensus_engine.suggest_convergence_strategies(consensus_analysis)
        strategies_text = "\n".join(f"- {strategy}" for strategy in convergence_strategies)
        
        prompt = f"""
{Config.ORCHESTRATOR_MODEL.system_prompt}

Round {round_number} Analysis:

Original Question: {question}

Debater Responses:
{responses_text}

Consensus Analysis:
- Average Similarity: {consensus_analysis.average_similarity:.3f}
- Consensus Reached: {consensus_analysis.consensus_reached}
- Method: {consensus_analysis.analysis_method}
- Details: {consensus_analysis.details}

Suggested Convergence Strategies:
{strategies_text}

Please provide constructive feedback to help the debaters converge on a consensus. Focus on:

1. Identifying common ground and shared principles
2. Highlighting areas where perspectives can be reconciled
3. Suggesting specific ways to address remaining disagreements
4. Encouraging integration of different viewpoints

Keep your feedback concise but actionable (200-400 words).

Feedback:
"""
        
        try:
            feedback = await self.llm._acall(prompt)
            return feedback
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return f"Continue refining your responses. Current similarity: {consensus_analysis.average_similarity:.3f}. Target: {Config.CONSENSUS_THRESHOLD}"
