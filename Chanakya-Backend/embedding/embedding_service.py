"""
Embedding generation service using sentence-t5-large model
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using sentence-t5-large model"""
    
    def __init__(self, model_name: str = "sentence-transformers/sentence-t5-large"):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
        
        Returns:
            NumPy array of the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            # Return zero vector with model's dimension
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        try:
            # Sentence-T5 models don't require prefixes, encode directly
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of input texts to embed
            batch_size: Number of texts to process in each batch
        
        Returns:
            NumPy array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not texts:
            return np.array([])
        
        # Filter out empty texts
        valid_texts = [text if text and text.strip() else "" for text in texts]
        
        try:
            # Sentence-T5 models don't require prefixes, encode directly
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query
        
        Args:
            query: Query text to embed
        
        Returns:
            NumPy array of the embedding vector
        """
        if not query or not query.strip():
            logger.warning("Empty query provided, returning zero vector")
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        try:
            # Sentence-T5 models don't require prefixes, encode directly
            embedding = self.model.encode(query, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.model.get_sentence_embedding_dimension()
