"""
Model Context Protocol (MCP) integration for enhanced context sharing
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict
from collections import Counter

from models import MCPContext, DebaterResponse, DebateRound

logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol server for sharing context between LLMs"""
    
    def __init__(self):
        self.contexts: Dict[str, MCPContext] = {}
        self.active_context_id: Optional[str] = None
    
    def create_context(self, context_id: str) -> MCPContext:
        """Create a new MCP context"""
        context = MCPContext()
        self.contexts[context_id] = context
        self.active_context_id = context_id
        logger.info(f"Created MCP context: {context_id}")
        return context
    
    def get_context(self, context_id: str) -> Optional[MCPContext]:
        """Get an existing MCP context"""
        return self.contexts.get(context_id)
    
    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update an MCP context with new information"""
        if context_id not in self.contexts:
            return False
        
        context = self.contexts[context_id]
        
        # Update shared knowledge
        if 'shared_knowledge' in updates:
            context.shared_knowledge.update(updates['shared_knowledge'])
        
        # Add to conversation history
        if 'conversation_entry' in updates:
            context.conversation_history.append(updates['conversation_entry'])
        
        # Add key concepts
        if 'key_concepts' in updates:
            for concept in updates['key_concepts']:
                if concept not in context.key_concepts:
                    context.key_concepts.append(concept)
        
        # Add agreed facts
        if 'agreed_facts' in updates:
            for fact in updates['agreed_facts']:
                context.add_agreed_fact(fact)
        
        # Add disputed points
        if 'disputed_points' in updates:
            for point in updates['disputed_points']:
                context.add_disputed_point(point)
        
        logger.debug(f"Updated MCP context: {context_id}")
        return True
    
    def export_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Export context as JSON-serializable dictionary"""
        context = self.get_context(context_id)
        if not context:
            return None
        
        return {
            'context_id': context_id,
            'shared_knowledge': context.shared_knowledge,
            'conversation_history': context.conversation_history,
            'key_concepts': context.key_concepts,
            'agreed_facts': context.agreed_facts,
            'disputed_points': context.disputed_points,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def import_context(self, context_data: Dict[str, Any]) -> str:
        """Import context from dictionary"""
        context_id = context_data.get('context_id', f"imported_{datetime.now().timestamp()}")
        
        context = MCPContext(
            shared_knowledge=context_data.get('shared_knowledge', {}),
            conversation_history=context_data.get('conversation_history', []),
            key_concepts=context_data.get('key_concepts', []),
            agreed_facts=context_data.get('agreed_facts', []),
            disputed_points=context_data.get('disputed_points', [])
        )
        
        self.contexts[context_id] = context
        logger.info(f"Imported MCP context: {context_id}")
        return context_id

class MCPTools:
    """Utility tools for MCP integration"""
    
    @staticmethod
    def extract_entities_from_response(response: DebaterResponse) -> Dict[str, List[str]]:
        """Extract entities from a debater response"""
        text = response.response.lower()
        
        # Simple entity extraction
        entities = {
            'organizations': [],
            'concepts': [],
            'claims': [],
            'statistics': []
        }
        
        # Extract potential organizations (capitalized words)
        import re
        org_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        orgs = re.findall(org_pattern, response.response)
        entities['organizations'] = list(set(orgs))
        
        # Extract claims (sentences with "is", "are", "will", "should")
        claim_patterns = [
            r'[^.!?]*\s(?:is|are|will|should|must|can)\s[^.!?]*[.!?]',
            r'[^.!?]*\s(?:believe|think|argue|claim|suggest)\s[^.!?]*[.!?]'
        ]
        
        for pattern in claim_patterns:
            claims = re.findall(pattern, response.response, re.IGNORECASE)
            entities['claims'].extend([claim.strip() for claim in claims])
        
        # Extract potential statistics (numbers with %)
        stat_pattern = r'\b\d+(?:\.\d+)?%\b|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:billion|million|thousand|percent)\b'
        stats = re.findall(stat_pattern, response.response, re.IGNORECASE)
        entities['statistics'] = list(set(stats))
        
        return entities
    
    @staticmethod
    def identify_consensus_points(responses: List[DebaterResponse]) -> List[str]:
        """Identify points where all debaters seem to agree"""
        if len(responses) < 2:
            return []
        
        consensus_points = []
        
        # Extract key phrases from each response
        all_phrases = []
        for response in responses:
            # Split into sentences and extract key phrases
            sentences = response.response.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20:  # Meaningful sentences
                    all_phrases.append(sentence.lower())
        
        # Find phrases that appear in similar form across responses
        phrase_counter = Counter()
        
        for phrase in all_phrases:
            # Normalize phrase for comparison
            normalized = re.sub(r'[^\w\s]', '', phrase).strip()
            if len(normalized) > 15:
                phrase_counter[normalized] += 1
        
        # Identify consensus points (phrases mentioned by multiple debaters)
        for phrase, count in phrase_counter.items():
            if count >= 2:  # Mentioned by at least 2 debaters
                consensus_points.append(phrase)
        
        return consensus_points[:5]  # Return top 5 consensus points
    
    @staticmethod
    def generate_context_summary(context: MCPContext) -> str:
        """Generate a human-readable summary of the MCP context"""
        summary_parts = []
        
        if context.agreed_facts:
            summary_parts.append(f"Agreed Facts ({len(context.agreed_facts)}):")
            for i, fact in enumerate(context.agreed_facts[:3], 1):
                summary_parts.append(f"  {i}. {fact[:100]}...")
        
        if context.disputed_points:
            summary_parts.append(f"Disputed Points ({len(context.disputed_points)}):")
            for i, point in enumerate(context.disputed_points[:3], 1):
                summary_parts.append(f"  {i}. {point[:100]}...")
        
        if context.key_concepts:
            summary_parts.append(f"Key Concepts: {', '.join(context.key_concepts[:5])}")
        
        if context.shared_knowledge:
            summary_parts.append(f"Shared Knowledge Areas: {len(context.shared_knowledge)}")
        
        return "\n".join(summary_parts) if summary_parts else "No context available"

class DebateContextManager:
    """Manager for debate-specific MCP contexts"""
    
    def __init__(self, mcp_server: MCPServer):
        self.mcp_server = mcp_server
        self.current_debate_id: Optional[str] = None
    
    def start_debate_context(self, question: str) -> str:
        """Start a new debate context"""
        debate_id = f"debate_{datetime.now().timestamp()}"
        context = self.mcp_server.create_context(debate_id)
        
        # Initialize with the question
        context.update_shared_knowledge('original_question', question)
        context.update_shared_knowledge('start_time', datetime.now().isoformat())
        
        self.current_debate_id = debate_id
        return debate_id
    
    def update_with_round(self, round_data: DebateRound):
        """Update context with information from a debate round"""
        if not self.current_debate_id:
            return
        
        # Extract entities from all responses
        all_entities = {}
        for response in round_data.debater_responses:
            entities = MCPTools.extract_entities_from_response(response)
            for entity_type, entity_list in entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = []
                all_entities[entity_type].extend(entity_list)
        
        # Identify consensus points
        consensus_points = MCPTools.identify_consensus_points(round_data.debater_responses)
        
        # Update context
        updates = {
            'shared_knowledge': {
                f'round_{round_data.round_number}_entities': all_entities,
                f'round_{round_data.round_number}_consensus': consensus_points
            },
            'agreed_facts': consensus_points
        }
        
        # Add conversation entries
        for response in round_data.debater_responses:
            updates['conversation_entry'] = f"Round {round_data.round_number} - {response.debater_name}: {response.response[:200]}..."
        
        self.mcp_server.update_context(self.current_debate_id, updates)
    
    def get_context_for_prompt(self) -> str:
        """Get formatted context for inclusion in prompts"""
        if not self.current_debate_id:
            return ""
        
        context = self.mcp_server.get_context(self.current_debate_id)
        if not context:
            return ""
        
        return MCPTools.generate_context_summary(context)
    
    def finalize_debate_context(self, final_summary: str):
        """Finalize the debate context with the final summary"""
        if not self.current_debate_id:
            return
        
        updates = {
            'shared_knowledge': {
                'final_summary': final_summary,
                'end_time': datetime.now().isoformat()
            }
        }
        
        self.mcp_server.update_context(self.current_debate_id, updates)

# Global MCP instances
mcp_server = MCPServer()
debate_context_manager = DebateContextManager(mcp_server)
