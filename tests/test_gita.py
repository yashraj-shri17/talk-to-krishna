"""
Basic tests for Talk to Krishna application.

Run with: pytest test_gita.py
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config import Settings
from exceptions import (
    DataFileNotFoundError,
    ModelNotFoundError,
    InvalidInputError,
    SearchError
)


class TestConfig:
    """Test configuration management."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized."""
        settings = Settings()
        assert settings.SENTENCE_TRANSFORMER_MODEL == "all-MiniLM-L6-v2"
        assert settings.DEFAULT_TOP_K == 5
        assert settings.MIN_SIMILARITY_THRESHOLD == 0.1
    
    def test_file_path_generation(self):
        """Test file path generation."""
        settings = Settings()
        path = settings.get_file_path("test.json")
        assert isinstance(path, Path)
        assert path.name == "test.json"


class TestExceptions:
    """Test custom exceptions."""
    
    def test_data_file_not_found_error(self):
        """Test DataFileNotFoundError."""
        with pytest.raises(DataFileNotFoundError):
            raise DataFileNotFoundError("Test error")
    
    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        with pytest.raises(ModelNotFoundError):
            raise ModelNotFoundError("Test error")
    
    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        with pytest.raises(InvalidInputError):
            raise InvalidInputError("Test error")


class TestSemanticSearch:
    """Test semantic search functionality."""
    
    @patch('semantic_search_gita.Path.exists')
    def test_load_embeddings_file_not_found(self, mock_exists):
        """Test that missing embeddings file raises error."""
        from semantic_search_gita import SemanticSearchEngine
        
        mock_exists.return_value = False
        engine = SemanticSearchEngine()
        
        with pytest.raises(ModelNotFoundError):
            engine.load_embeddings()
    
    def test_validate_query_empty(self):
        """Test that empty query raises error."""
        from semantic_search_gita import SemanticSearchEngine
        
        engine = SemanticSearchEngine()
        
        with pytest.raises(InvalidInputError):
            engine.validate_query("")
    
    def test_validate_query_too_short(self):
        """Test that short query raises error."""
        from semantic_search_gita import SemanticSearchEngine
        
        engine = SemanticSearchEngine()
        
        with pytest.raises(InvalidInputError):
            engine.validate_query("ab")
    
    def test_validate_query_valid(self):
        """Test that valid query is accepted."""
        from semantic_search_gita import SemanticSearchEngine
        
        engine = SemanticSearchEngine()
        result = engine.validate_query("How to find peace?")
        
        assert result == "How to find peace?"


class TestTFIDFSearch:
    """Test TF-IDF search functionality."""
    
    @patch('search_tfidf.Path.exists')
    def test_load_model_file_not_found(self, mock_exists):
        """Test that missing model file raises error."""
        from search_tfidf import TFIDFSearchEngine
        
        mock_exists.return_value = False
        engine = TFIDFSearchEngine()
        
        with pytest.raises(ModelNotFoundError):
            engine.load_model()
    
    def test_emotion_keyword_detection(self):
        """Test emotion keyword detection."""
        from search_tfidf import EmotionKeywordMapper
        
        result = EmotionKeywordMapper.detect_emotions("I am feeling sad")
        assert "sad" in result.lower()
    
    def test_text_preprocessing(self):
        """Test text preprocessing."""
        from create_tfidf_model import TextPreprocessor
        
        preprocessor = TextPreprocessor()
        result = preprocessor.clean_text("Hello, world! This is a test.")
        
        assert "," not in result
        assert "!" not in result


class TestEmotionDetection:
    """Test emotion detection functionality."""
    
    def test_detect_depression(self):
        """Test depression detection."""
        from suggest_shloka import EmotionDetector
        
        result = EmotionDetector.detect("I want to commit suicide")
        assert result == "depression"
    
    def test_detect_anger(self):
        """Test anger detection."""
        from suggest_shloka import EmotionDetector
        
        result = EmotionDetector.detect("I am so angry")
        assert result == "anger"
    
    def test_detect_confusion(self):
        """Test confusion detection."""
        from suggest_shloka import EmotionDetector
        
        result = EmotionDetector.detect("I am confused about what to do")
        assert result == "confusion"
    
    def test_detect_general(self):
        """Test general emotion for unknown input."""
        from suggest_shloka import EmotionDetector
        
        result = EmotionDetector.detect("random text")
        assert result == "general"


class TestRecommendationStrategy:
    """Test recommendation strategy."""
    
    def test_get_strategy_depression(self):
        """Test strategy for depression."""
        from suggest_shloka import RecommendationStrategy
        
        strategy = RecommendationStrategy.get_strategy("depression")
        assert "motivation" in strategy["target"]
        assert "sadness" in strategy["avoid"]
    
    def test_get_strategy_general(self):
        """Test default strategy."""
        from suggest_shloka import RecommendationStrategy
        
        strategy = RecommendationStrategy.get_strategy("unknown")
        assert "motivation" in strategy["target"]


class TestGitaAPI:
    """Test unified API."""
    
    def test_api_initialization(self):
        """Test API initialization."""
        from gita_api import GitaAPI
        
        api = GitaAPI()
        assert api.semantic_engine is None
        assert api.tfidf_engine is None
        assert api.recommender is None
    
    def test_invalid_search_method(self):
        """Test that invalid search method raises error."""
        from gita_api import GitaAPI
        
        api = GitaAPI()
        
        with pytest.raises(InvalidInputError):
            api.search("test query", method="invalid")  # type: ignore
    
    def test_empty_query(self):
        """Test that empty query raises error."""
        from gita_api import GitaAPI
        
        api = GitaAPI()
        
        with pytest.raises(InvalidInputError):
            api.search("")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
