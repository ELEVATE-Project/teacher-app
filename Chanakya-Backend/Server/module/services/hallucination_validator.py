"""
Hallucination Validator
=======================

Validates generated content against source textbook content to prevent hallucinations.
Uses semantic similarity with sentence-transformers for embedding comparison.
"""

import logging
import re
from typing import List, Tuple, Optional
import numpy as np

from ..models.schemas import (
    Lesson,
    Slide,
    TextbookContent,
    ValidationReport,
)

logger = logging.getLogger(__name__)


# Lazy loading for sentence-transformers to avoid import overhead
_model = None
_model_name = "all-MiniLM-L6-v2"


def _get_embedding_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(_model_name)
            logger.info(f"Loaded sentence transformer model: {_model_name}")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise
    return _model


class HallucinationValidator:
    """
    Validates generated content against source textbook content.
    
    Uses semantic similarity to ensure generated content is grounded
    in the source material and doesn't introduce hallucinated facts.
    """
    
    # Minimum grounding score threshold
    MIN_GROUNDING_SCORE = 0.7
    
    # Minimum score before content is flagged
    FLAG_THRESHOLD = 0.6
    
    def __init__(self, use_embeddings: bool = True):
        """
        Initialize the hallucination validator.
        
        Args:
            use_embeddings: Whether to use sentence embeddings for validation.
                           If False, falls back to keyword-based validation.
        """
        self.use_embeddings = use_embeddings
        self._embeddings_available = None

    def _check_embeddings_available(self) -> bool:
        """Check if sentence-transformers is available."""
        if self._embeddings_available is None:
            try:
                _get_embedding_model()
                self._embeddings_available = True
            except (ImportError, Exception) as e:
                logger.warning(f"Embeddings not available: {e}")
                self._embeddings_available = False
        return self._embeddings_available
    
    async def validate_lesson(
        self,
        lesson: Lesson,
        source_content: List[TextbookContent]
    ) -> ValidationReport:
        """
        Validates entire lesson against source content.
        
        Checks:
        - All facts are traceable to source
        - No invented concepts or definitions
        - Examples are appropriate for content
        
        Args:
            lesson: The generated lesson to validate
            source_content: List of source textbook content
            
        Returns:
            ValidationReport with validation results
        """
        if not source_content:
            return ValidationReport(
                is_valid=False,
                overall_score=0.0,
                issues=["No source content provided for validation"],
                flagged_content=[],
                recommendations=["Ensure textbook content is retrieved before validation"]
            )
        
        # Combine source content for comparison
        combined_source = self._combine_source_content(source_content)
        
        # Validate each slide
        slide_scores = []
        all_issues = []
        all_flagged = []
        all_recommendations = []
        
        for slide in lesson.slides:
            slide_report = await self._validate_slide(slide, combined_source, source_content)
            slide_scores.append(slide_report.overall_score)
            all_issues.extend(slide_report.issues)
            all_flagged.extend(slide_report.flagged_content)
            all_recommendations.extend(slide_report.recommendations)
        
        # Calculate overall score (average of slide scores)
        overall_score = sum(slide_scores) / len(slide_scores) if slide_scores else 0.0
        
        # Determine if valid
        is_valid = overall_score >= self.MIN_GROUNDING_SCORE
        
        # Add overall recommendations if score is low
        if not is_valid:
            all_recommendations.append(
                f"Overall grounding score ({overall_score:.2f}) is below threshold "
                f"({self.MIN_GROUNDING_SCORE}). Consider regenerating low-scoring slides."
            )
        
        return ValidationReport(
            is_valid=is_valid,
            overall_score=overall_score,
            issues=list(set(all_issues)),  # Remove duplicates
            flagged_content=all_flagged,
            recommendations=list(set(all_recommendations))
        )
    
    async def _validate_slide(
        self,
        slide: Slide,
        combined_source: str,
        source_content: List[TextbookContent]
    ) -> ValidationReport:
        """
        Validate a single slide against source content.
        
        Args:
            slide: The slide to validate
            combined_source: Combined source text
            source_content: List of source content objects
            
        Returns:
            ValidationReport for this slide
        """
        issues = []
        flagged_content = []
        recommendations = []
        
        # Combine slide content for validation
        slide_text = self._get_slide_text(slide)
        
        # Calculate grounding score
        grounding_score = self._calculate_grounding_score(slide_text, combined_source)
        
        # Extract and validate facts
        facts = self._extract_facts(slide_text)
        ungrounded_facts = []
        
        for fact in facts:
            fact_score = self._calculate_grounding_score(fact, combined_source)
            if fact_score < self.FLAG_THRESHOLD:
                ungrounded_facts.append(fact)
        
        # Report issues
        if grounding_score < self.MIN_GROUNDING_SCORE:
            issues.append(
                f"Slide {slide.slide_number} has low grounding score: {grounding_score:.2f}"
            )
        
        if ungrounded_facts:
            flagged_content.extend(ungrounded_facts)
            issues.append(
                f"Slide {slide.slide_number} contains {len(ungrounded_facts)} "
                f"potentially ungrounded facts"
            )
            recommendations.append(
                f"Review flagged content in slide {slide.slide_number} for accuracy"
            )
        
        # Check source references
        if not slide.source_references:
            issues.append(f"Slide {slide.slide_number} has no source references")
            recommendations.append(
                f"Add source references to slide {slide.slide_number}"
            )
        
        return ValidationReport(
            is_valid=grounding_score >= self.MIN_GROUNDING_SCORE,
            overall_score=grounding_score,
            issues=issues,
            flagged_content=flagged_content,
            recommendations=recommendations
        )

    def _calculate_grounding_score(
        self,
        generated_text: str,
        source_text: str
    ) -> float:
        """
        Calculates how well generated text is grounded in source.
        
        Uses semantic similarity via sentence embeddings when available,
        falls back to keyword-based scoring otherwise.
        
        Args:
            generated_text: The generated text to validate
            source_text: The source textbook content
            
        Returns:
            Float score between 0.0 and 1.0
        """
        if not generated_text or not source_text:
            return 0.0
        
        # Try embedding-based similarity first
        if self.use_embeddings and self._check_embeddings_available():
            return self._calculate_embedding_similarity(generated_text, source_text)
        
        # Fallback to keyword-based scoring
        return self._calculate_keyword_similarity(generated_text, source_text)
    
    def _calculate_embedding_similarity(
        self,
        generated_text: str,
        source_text: str
    ) -> float:
        """
        Calculate semantic similarity using sentence embeddings.
        
        Args:
            generated_text: The generated text
            source_text: The source text
            
        Returns:
            Cosine similarity score between 0.0 and 1.0
        """
        try:
            model = _get_embedding_model()
            
            # Split texts into sentences for better comparison
            gen_sentences = self._split_into_sentences(generated_text)
            source_sentences = self._split_into_sentences(source_text)
            
            if not gen_sentences or not source_sentences:
                return 0.5  # Neutral score if can't split
            
            # Get embeddings
            gen_embeddings = model.encode(gen_sentences)
            source_embeddings = model.encode(source_sentences)
            
            # Calculate max similarity for each generated sentence
            similarities = []
            for gen_emb in gen_embeddings:
                max_sim = 0.0
                for src_emb in source_embeddings:
                    sim = self._cosine_similarity(gen_emb, src_emb)
                    max_sim = max(max_sim, sim)
                similarities.append(max_sim)
            
            # Return average of max similarities
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            
            # Normalize to 0-1 range (cosine similarity can be negative)
            return max(0.0, min(1.0, (avg_similarity + 1) / 2))
            
        except Exception as e:
            logger.warning(f"Embedding similarity failed: {e}, falling back to keywords")
            return self._calculate_keyword_similarity(generated_text, source_text)
    
    def _calculate_keyword_similarity(
        self,
        generated_text: str,
        source_text: str
    ) -> float:
        """
        Calculate similarity based on keyword overlap.
        
        Args:
            generated_text: The generated text
            source_text: The source text
            
        Returns:
            Jaccard-like similarity score between 0.0 and 1.0
        """
        # Tokenize and normalize
        gen_words = self._tokenize(generated_text)
        source_words = self._tokenize(source_text)
        
        if not gen_words:
            return 0.0
        
        # Calculate overlap
        overlap = len(gen_words & source_words)
        
        # Use Jaccard-like coefficient with bias toward generated text
        # This measures what fraction of generated words appear in source
        coverage = overlap / len(gen_words) if gen_words else 0.0
        
        # Add a base score to account for paraphrasing
        # (generated text may use different words for same concepts)
        base_score = 0.3
        
        return min(1.0, base_score + (coverage * 0.7))
    
    def _extract_facts(self, text: str) -> List[str]:
        """
        Extract factual claims from text.
        
        Identifies sentences that contain factual statements
        (definitions, numerical claims, cause-effect relationships).
        
        Args:
            text: Text to extract facts from
            
        Returns:
            List of factual claim strings
        """
        facts = []
        sentences = self._split_into_sentences(text)
        
        # Patterns that indicate factual claims
        fact_patterns = [
            r'\b(is|are|was|were)\s+(a|an|the)\b',  # Definitions
            r'\b(means|refers to|defined as)\b',     # Definitions
            r'\b\d+(\.\d+)?\s*(percent|%|kg|m|cm|km|years?|days?)\b',  # Numerical
            r'\b(because|therefore|thus|hence|causes?|results? in)\b',  # Cause-effect
            r'\b(always|never|must|cannot)\b',       # Absolute claims
            r'\b(discovered|invented|founded|created)\s+by\b',  # Attribution
            r'\b(formula|equation|law|theorem|principle)\b',  # Scientific terms
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence matches any fact pattern
            for pattern in fact_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    facts.append(sentence)
                    break
        
        return facts

    def _combine_source_content(self, source_content: List[TextbookContent]) -> str:
        """Combine multiple source content items into a single string."""
        return "\n\n".join(tc.content for tc in source_content)
    
    def _get_slide_text(self, slide: Slide) -> str:
        """Extract all text content from a slide."""
        parts = [
            slide.title,
            slide.explanation,
            " ".join(slide.bullet_points),
            " ".join(slide.key_terms),
            " ".join(slide.examples),
        ]
        return " ".join(parts)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on common delimiters
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _tokenize(self, text: str) -> set:
        """Tokenize text into a set of normalized words."""
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
            'if', 'or', 'because', 'until', 'while', 'this', 'that', 'these',
            'those', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who'
        }
        
        return {w for w in words if w not in stop_words and len(w) > 2}
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    async def validate_content_grounding(
        self,
        generated_text: str,
        source_content: List[TextbookContent]
    ) -> Tuple[float, List[str]]:
        """
        Validate that generated text is grounded in source content.
        
        Args:
            generated_text: The generated text to validate
            source_content: List of source textbook content
            
        Returns:
            Tuple of (grounding_score, list of ungrounded facts)
        """
        if not source_content:
            return 0.0, []
        
        combined_source = self._combine_source_content(source_content)
        score = self._calculate_grounding_score(generated_text, combined_source)
        
        # Find ungrounded facts
        ungrounded = []
        facts = self._extract_facts(generated_text)
        for fact in facts:
            fact_score = self._calculate_grounding_score(fact, combined_source)
            if fact_score < self.FLAG_THRESHOLD:
                ungrounded.append(fact)
        
        return score, ungrounded
    
    def get_source_references_for_slide(
        self,
        slide: Slide,
        source_content: List[TextbookContent]
    ) -> List[str]:
        """
        Find the most relevant source references for a slide.
        
        Args:
            slide: The slide to find references for
            source_content: List of source textbook content
            
        Returns:
            List of source reference strings
        """
        if not source_content:
            return []
        
        slide_text = self._get_slide_text(slide)
        
        # Score each source content by relevance
        scored_sources = []
        for tc in source_content:
            score = self._calculate_grounding_score(slide_text, tc.content)
            scored_sources.append((tc.source, score))
        
        # Sort by score and return top 3
        scored_sources.sort(key=lambda x: x[1], reverse=True)
        return [source for source, score in scored_sources[:3] if score > 0.3]
