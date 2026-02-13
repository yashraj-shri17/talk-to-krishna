"""
Setup script for Talk to Krishna application.

This script helps set up the application by:
1. Checking dependencies
2. Generating embeddings
3. Building TF-IDF model
4. Running basic tests
"""
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

from src.logger import setup_logger
from src.config import settings

logger = setup_logger("setup", "INFO")


class SetupManager:
    """Manage application setup process."""
    
    def __init__(self):
        """Initialize setup manager."""
        self.base_dir = Path(__file__).parent
        self.errors: List[str] = []
        
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        logger.info("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.errors.append(
                f"Python 3.8+ required, found {version.major}.{version.minor}"
            )
            return False
        
        logger.info(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        logger.info("Checking dependencies...")
        
        required_packages = [
            "numpy",
            "scikit-learn",
            "sentence-transformers",
            "pydantic",
            "pydantic-settings",
            "colorlog"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                logger.info(f"✓ {package}")
            except ImportError:
                missing.append(package)
                logger.warning(f"✗ {package} not found")
        
        if missing:
            self.errors.append(
                f"Missing packages: {', '.join(missing)}. "
                "Run: pip install -r requirements.txt"
            )
            return False
        
        return True
    
    def check_data_files(self) -> bool:
        """Check if required data files exist."""
        logger.info("Checking data files...")
        
        required_files = [
            settings.gita_emotions_path,
        ]
        
        missing = []
        for file_path in required_files:
            if file_path.exists():
                logger.info(f"✓ {file_path.name}")
            else:
                missing.append(file_path.name)
                logger.warning(f"✗ {file_path.name} not found")
        
        if missing:
            self.errors.append(
                f"Missing data files: {', '.join(missing)}. "
                "Please ensure data files are in the data/ directory."
            )
            return False
        
        return True
    
    def generate_embeddings(self) -> bool:
        """Generate embeddings if not already present."""
        logger.info("Checking embeddings...")
        
        if settings.embeddings_path.exists():
            logger.info(f"✓ Embeddings already exist at {settings.embeddings_path}")
            return True
        
        logger.info("Generating embeddings (this may take a few minutes)...")
        
        try:
            from src.create_embeddings import EmbeddingGenerator
            
            generator = EmbeddingGenerator()
            generator.create_embeddings()
            
            logger.info("✓ Embeddings generated successfully")
            return True
            
        except Exception as e:
            self.errors.append(f"Failed to generate embeddings: {e}")
            return False
    
    def build_tfidf_model(self) -> bool:
        """Build TF-IDF model if not already present."""
        logger.info("Checking TF-IDF model...")
        
        if settings.tfidf_model_path.exists():
            logger.info(f"✓ TF-IDF model already exists at {settings.tfidf_model_path}")
            return True
        
        logger.info("Building TF-IDF model...")
        
        try:
            from src.create_tfidf_model import TFIDFModelBuilder
            
            builder = TFIDFModelBuilder()
            builder.build_model()
            
            logger.info("✓ TF-IDF model built successfully")
            return True
            
        except Exception as e:
            self.errors.append(f"Failed to build TF-IDF model: {e}")
            return False
    
    def run_basic_tests(self) -> bool:
        """Run basic functionality tests."""
        logger.info("Running basic tests...")
        
        try:
            # Test semantic search
            from src.semantic_search_gita import SemanticSearchEngine
            engine = SemanticSearchEngine()
            results = engine.search("peace", top_k=1)
            
            if results:
                logger.info("✓ Semantic search working")
            else:
                logger.warning("⚠ Semantic search returned no results")
            
            # Test TF-IDF search
            from src.search_tfidf import TFIDFSearchEngine
            tfidf = TFIDFSearchEngine()
            results = tfidf.search("shanti", top_k=1)
            
            if results:
                logger.info("✓ TF-IDF search working")
            else:
                logger.warning("⚠ TF-IDF search returned no results")
            
            # Test recommender
            from src.suggest_shloka import ShlokaRecommender
            recommender = ShlokaRecommender()
            results = recommender.recommend("I am confused", top_k=1)
            
            if results:
                logger.info("✓ Emotion-based recommender working")
            else:
                logger.warning("⚠ Recommender returned no results")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Tests failed: {e}")
            return False
    
    def setup(self, skip_tests: bool = False) -> bool:
        """
        Run complete setup process.
        
        Args:
            skip_tests: Whether to skip running tests
            
        Returns:
            True if setup successful, False otherwise
        """
        logger.info("=" * 70)
        logger.info("Starting Talk to Krishna Setup")
        logger.info("=" * 70)
        
        steps = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("Data Files", self.check_data_files),
            ("Embeddings", self.generate_embeddings),
            ("TF-IDF Model", self.build_tfidf_model),
        ]
        
        if not skip_tests:
            steps.append(("Basic Tests", self.run_basic_tests))
        
        for step_name, step_func in steps:
            logger.info(f"\n--- {step_name} ---")
            if not step_func():
                logger.error(f"✗ {step_name} failed")
                break
        
        logger.info("\n" + "=" * 70)
        
        if self.errors:
            logger.error("Setup completed with errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
            return False
        else:
            logger.info("✓ Setup completed successfully!")
            logger.info("\nYou can now use the application:")
            logger.info("  python main.py 'your query' [method]")
            logger.info("  python cli.py  (interactive mode)")
            return True


def main():
    """Main entry point for setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup Talk to Krishna application"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running basic tests"
    )
    
    args = parser.parse_args()
    
    setup_manager = SetupManager()
    success = setup_manager.setup(skip_tests=args.skip_tests)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
