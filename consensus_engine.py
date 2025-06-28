"""
Consensus engine for analyzing agreement between debater responses
"""

import logging
import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re
from models import DebaterResponse, ConsensusAnalysis
from config import Config

logger = logging.getLogger(__name__)

class ConsensusEngine:
    """Engine for detecting consensus between multiple LLM responses"""
    
    def __init__(self):
        self.embedding_model = None
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load the sentence transformer model for semantic similarity"""
        try:
            self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {Config.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep punctuation for meaning
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        return text.lower()
    
    def calculate_semantic_similarity(self, responses: List[str]) -> Dict[str, float]:
        """Calculate semantic similarity using sentence transformers"""
        if not self.embedding_model or len(responses) < 2:
            return {}
        
        try:
            # Preprocess responses
            processed_responses = [self.preprocess_text(resp) for resp in responses]
            
            # Get embeddings
            embeddings = self.embedding_model.encode(processed_responses)
            
            # Calculate pairwise similarities
            similarities = {}
            for i in range(len(responses)):
                for j in range(i + 1, len(responses)):
                    sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                    similarities[f"response_{i}_vs_{j}"] = float(sim)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return {}
    
    def calculate_keyword_similarity(self, responses: List[str]) -> Dict[str, float]:
        """Calculate similarity based on TF-IDF vectors"""
        if len(responses) < 2:
            return {}
        
        try:
            # Preprocess responses
            processed_responses = [self.preprocess_text(resp) for resp in responses]
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(processed_responses)
            
            # Calculate pairwise similarities
            similarities = {}
            for i in range(len(responses)):
                for j in range(i + 1, len(responses)):
                    sim = cosine_similarity(tfidf_matrix[i], tfidf_matrix[j])[0][0]
                    similarities[f"response_{i}_vs_{j}"] = float(sim)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating keyword similarity: {e}")
            return {}
    
    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from a response"""
        # Simple extraction based on sentences and bullet points
        sentences = re.split(r'[.!?]', text)
        bullet_points = re.findall(r'[-•*]\s*([^.!?]*)', text)
        
        key_points = []
        
        # Add significant sentences (longer than 20 chars)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                key_points.append(sentence)
        
        # Add bullet points
        for point in bullet_points:
            point = point.strip()
            if len(point) > 10:
                key_points.append(point)
        
        return key_points[:5]  # Limit to top 5 key points
    
    def analyze_consensus(self, debater_responses: List[DebaterResponse]) -> ConsensusAnalysis:
        """Analyze consensus between debater responses"""
        if len(debater_responses) < 2:
            return ConsensusAnalysis(
                similarity_scores={},
                average_similarity=0.0,
                consensus_reached=False,
                threshold_used=Config.CONSENSUS_THRESHOLD,
                analysis_method="insufficient_data"
            )
        
        # Extract response texts
        response_texts = [resp.response for resp in debater_responses]
        
        # Calculate similarities based on configured method
        if Config.SIMILARITY_METHOD == "semantic" and self.embedding_model:
            similarities = self.calculate_semantic_similarity(response_texts)
            method = "semantic_embeddings"
        else:
            similarities = self.calculate_keyword_similarity(response_texts)
            method = "tfidf_keywords"
        
        # Calculate average similarity
        if similarities:
            avg_similarity = np.mean(list(similarities.values()))
        else:
            avg_similarity = 0.0
        
        # Check if consensus is reached
        consensus_reached = avg_similarity >= Config.CONSENSUS_THRESHOLD
        
        # Generate detailed analysis
        details = self._generate_consensus_details(debater_responses, similarities, avg_similarity)
        
        return ConsensusAnalysis(
            similarity_scores=similarities,
            average_similarity=float(avg_similarity),
            consensus_reached=consensus_reached,
            threshold_used=Config.CONSENSUS_THRESHOLD,
            analysis_method=method,
            details=details
        )
    
    def _generate_consensus_details(
        self, 
        responses: List[DebaterResponse], 
        similarities: Dict[str, float], 
        avg_similarity: float
    ) -> str:
        """Generate detailed analysis of consensus"""
        details = []
        
        details.append(f"Average similarity: {avg_similarity:.3f}")
        details.append(f"Consensus threshold: {Config.CONSENSUS_THRESHOLD}")
        
        if similarities:
            max_sim = max(similarities.values())
            min_sim = min(similarities.values())
            details.append(f"Similarity range: {min_sim:.3f} - {max_sim:.3f}")
            
            # Identify most and least similar pairs
            max_pair = max(similarities.items(), key=lambda x: x[1])
            min_pair = min(similarities.items(), key=lambda x: x[1])
            details.append(f"Most similar: {max_pair[0]} ({max_pair[1]:.3f})")
            details.append(f"Least similar: {min_pair[0]} ({min_pair[1]:.3f})")
        
        # Analyze response lengths
        lengths = [len(resp.response) for resp in responses]
        details.append(f"Response lengths: {lengths}")
        
        # Extract key points for comparison
        all_key_points = []
        for i, resp in enumerate(responses):
            key_points = self.extract_key_points(resp.response)
            details.append(f"{resp.debater_name} key points: {len(key_points)}")
            all_key_points.extend(key_points)
        
        return " | ".join(details)
    
    def identify_disagreement_areas(self, responses: List[DebaterResponse]) -> List[str]:
        """Identify specific areas where debaters disagree"""
        disagreements = []
        
        # Extract key points from each response
        response_points = {}
        for resp in responses:
            response_points[resp.debater_name] = self.extract_key_points(resp.response)
        
        # Simple disagreement detection based on contradictory keywords
        contradiction_patterns = [
            (["agree", "support", "favor"], ["disagree", "oppose", "against"]),
            (["yes", "correct", "true"], ["no", "incorrect", "false"]),
            (["beneficial", "positive", "good"], ["harmful", "negative", "bad"]),
            (["increase", "more", "higher"], ["decrease", "less", "lower"])
        ]
        
        for positive_words, negative_words in contradiction_patterns:
            pos_responses = []
            neg_responses = []
            
            for name, points in response_points.items():
                text = " ".join(points).lower()
                if any(word in text for word in positive_words):
                    pos_responses.append(name)
                if any(word in text for word in negative_words):
                    neg_responses.append(name)
            
            if pos_responses and neg_responses:
                disagreements.append(f"Contradiction on {positive_words[0]}: {pos_responses} vs {neg_responses}")
        
        return disagreements
    
    def suggest_convergence_strategies(self, consensus_analysis: ConsensusAnalysis) -> List[str]:
        """Suggest strategies to help debaters converge"""
        strategies = []
        
        if consensus_analysis.average_similarity < 0.3:
            strategies.append("Focus on finding common ground and shared principles")
            strategies.append("Define key terms to ensure everyone is discussing the same concepts")
        elif consensus_analysis.average_similarity < 0.6:
            strategies.append("Identify specific points of disagreement and address them systematically")
            strategies.append("Look for compromise positions that incorporate elements from different perspectives")
        else:
            strategies.append("Refine the details and nuances of your shared understanding")
            strategies.append("Work on integrating your similar viewpoints into a cohesive conclusion")
        
        return strategies

# Singleton instance
consensus_engine = ConsensusEngine()
