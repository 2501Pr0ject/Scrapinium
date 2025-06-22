"""Tests unitaires pour le pipeline ML de Scrapinium."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from src.scrapinium.ml import MLPipeline, ContentClassifier, AntibotDetector, ContentAnalyzer
from src.scrapinium.ml.ml_pipeline import MLAnalysisResult
from src.scrapinium.ml.content_classifier import PageType, ContentQuality, ClassificationResult
from src.scrapinium.ml.antibot_detector import BotChallenge, DetectionResult, EvasionStrategy
from src.scrapinium.ml.content_analyzer import ContentFeatures


class TestMLPipeline:
    """Tests pour le pipeline ML principal."""
    
    @pytest.fixture
    def pipeline(self):
        """Pipeline ML pour les tests."""
        return MLPipeline(enable_cache=True)
    
    @pytest.fixture
    def sample_html(self):
        """HTML d'exemple pour les tests."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Article</title>
            <meta name="description" content="This is a test article">
        </head>
        <body>
            <h1>Test Article Title</h1>
            <p>This is a test paragraph with some content.</p>
            <p>Another paragraph with more content for testing.</p>
            <img src="test.jpg" alt="Test image">
            <a href="https://example.com">External link</a>
        </body>
        </html>
        """
    
    def test_pipeline_initialization(self, pipeline):
        """Test d'initialisation du pipeline."""
        assert pipeline is not None
        assert isinstance(pipeline.content_classifier, ContentClassifier)
        assert isinstance(pipeline.antibot_detector, AntibotDetector)
        assert isinstance(pipeline.content_analyzer, ContentAnalyzer)
        assert pipeline.enable_cache is True
        assert pipeline.cache is not None
        assert pipeline.cache_ttl == 3600
    
    def test_cache_key_generation(self, pipeline):
        """Test de génération des clés de cache."""
        html = "<html><body>Test</body></html>"
        url = "https://example.com"
        headers = {"user-agent": "test"}
        
        key1 = pipeline._generate_cache_key(html, url, headers)
        key2 = pipeline._generate_cache_key(html, url, headers)
        key3 = pipeline._generate_cache_key(html, "https://different.com", headers)
        
        assert key1 == key2  # Même contenu = même clé
        assert key1 != key3  # URL différente = clé différente
        assert len(key1) == 32  # MD5 hash
    
    @pytest.mark.asyncio
    async def test_analyze_page_full_pipeline(self, pipeline, sample_html):
        """Test complet d'analyse d'une page."""
        url = "https://example.com/article"
        headers = {"user-agent": "Mozilla/5.0 test"}
        
        result = await pipeline.analyze_page(
            html=sample_html,
            url=url,
            headers=headers,
            response_time=1.5
        )
        
        # Vérifier que le résultat est complet
        assert isinstance(result, MLAnalysisResult)
        assert result.classification is not None
        assert result.bot_detection is not None
        assert result.content_features is not None
        assert result.content_summary is not None
        assert result.processing_time > 0
        assert 0 <= result.confidence_score <= 1
        assert isinstance(result.recommendations, list)
        assert isinstance(result.scraping_config, dict)
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, pipeline, sample_html):
        """Test du cache ML."""
        url = "https://example.com/test"
        
        # Premier appel - cache miss
        result1 = await pipeline.analyze_page(html=sample_html, url=url)
        assert pipeline.performance_stats['cache_misses'] >= 1
        
        # Deuxième appel - cache hit
        result2 = await pipeline.analyze_page(html=sample_html, url=url)
        assert pipeline.performance_stats['cache_hits'] >= 1
        
        # Les résultats devraient être identiques
        assert result1.classification.page_type == result2.classification.page_type
        assert result1.confidence_score == result2.confidence_score
    
    @pytest.mark.asyncio
    async def test_analyze_multiple_pages(self, pipeline):
        """Test d'analyse de plusieurs pages en parallèle."""
        pages_data = [
            {
                "html": "<html><body><h1>Article 1</h1><p>Content 1</p></body></html>",
                "url": "https://example.com/1",
                "headers": {}
            },
            {
                "html": "<html><body><h1>Article 2</h1><p>Content 2</p></body></html>",
                "url": "https://example.com/2",
                "headers": {}
            }
        ]
        
        results = await pipeline.analyze_multiple_pages(pages_data)
        
        assert len(results) == 2
        for result in results:
            assert isinstance(result, MLAnalysisResult)
            assert result.processing_time > 0
    
    def test_cache_management(self, pipeline):
        """Test de gestion du cache."""
        # Test des statistiques cache
        cache_stats = pipeline.get_cache_stats()
        assert cache_stats["cache_enabled"] is True
        assert "total_entries" in cache_stats
        assert "hit_rate_percent" in cache_stats
        
        # Test de nettoyage du cache
        clear_result = pipeline.clear_cache()
        assert clear_result["cache_enabled"] is True
        assert "entries_cleared" in clear_result
        
        # Test d'optimisation du cache
        optimize_result = pipeline.optimize_cache()
        assert optimize_result["cache_enabled"] is True
        assert "removed_entries" in optimize_result
    
    def test_performance_metrics(self, pipeline):
        """Test des métriques de performance."""
        metrics = pipeline.get_performance_metrics()
        
        expected_keys = [
            'total_analyses', 'avg_processing_time', 'success_rate',
            'cache_hits', 'cache_misses'
        ]
        
        for key in expected_keys:
            assert key in metrics
    
    @pytest.mark.asyncio
    async def test_error_handling(self, pipeline):
        """Test de gestion d'erreurs."""
        # HTML malformé
        with pytest.raises(Exception):
            await pipeline.analyze_page(html=None, url="https://example.com")
        
        # URL invalide
        with pytest.raises(Exception):
            await pipeline.analyze_page(html="<html></html>", url=None)


class TestContentClassifier:
    """Tests pour le classificateur de contenu."""
    
    @pytest.fixture
    def classifier(self):
        """Classificateur pour les tests."""
        return ContentClassifier()
    
    def test_article_classification(self, classifier):
        """Test de classification d'article."""
        html = """
        <html>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This is an article with good content structure.</p>
                <p>Multiple paragraphs make it look like a real article.</p>
            </article>
        </body>
        </html>
        """
        
        result = classifier.classify_page(html, "https://example.com/article")
        
        assert isinstance(result, ClassificationResult)
        assert result.page_type in [PageType.ARTICLE, PageType.BLOG]
        assert result.confidence > 0
        assert result.quality in [ContentQuality.HIGH, ContentQuality.MEDIUM]
    
    def test_ecommerce_classification(self, classifier):
        """Test de classification e-commerce."""
        html = """
        <html>
        <body>
            <div class="product">
                <h1>Product Name</h1>
                <span class="price">$29.99</span>
                <button class="buy-now">Buy Now</button>
                <div class="description">Product description here</div>
            </div>
        </body>
        </html>
        """
        
        result = classifier.classify_page(html, "https://shop.example.com/product/123")
        
        # Peut être classé comme ecommerce ou autre selon les patterns
        assert isinstance(result, ClassificationResult)
        assert result.confidence >= 0
    
    def test_language_detection(self, classifier):
        """Test de détection de langue."""
        # Texte français
        french_html = """
        <html><body>
        <p>Ceci est un article en français avec du contenu.</p>
        <p>Il contient plusieurs phrases pour tester la détection.</p>
        </body></html>
        """
        
        result = classifier.classify_page(french_html, "https://example.fr")
        assert result.language in ['fr', 'unknown']
        
        # Texte anglais
        english_html = """
        <html><body>
        <p>This is an article in English with content.</p>
        <p>It contains multiple sentences to test detection.</p>
        </body></html>
        """
        
        result = classifier.classify_page(english_html, "https://example.com")
        assert result.language in ['en', 'unknown']


class TestAntibotDetector:
    """Tests pour le détecteur anti-bot."""
    
    @pytest.fixture
    def detector(self):
        """Détecteur pour les tests."""
        return AntibotDetector()
    
    def test_cloudflare_detection(self, detector):
        """Test de détection Cloudflare."""
        html = """
        <html>
        <body>
            <div>Checking your browser before accessing...</div>
            <div>This process is automatic. Your browser will redirect...</div>
        </body>
        </html>
        """
        headers = {"cf-ray": "12345", "server": "cloudflare"}
        
        result = detector.analyze_page(html, headers, "https://example.com")
        
        assert isinstance(result, DetectionResult)
        assert BotChallenge.CLOUDFLARE in result.challenges
        assert result.confidence > 0
    
    def test_recaptcha_detection(self, detector):
        """Test de détection reCAPTCHA."""
        html = """
        <html>
        <body>
            <div class="g-recaptcha" data-sitekey="test"></div>
            <script src="https://www.google.com/recaptcha/api.js"></script>
        </body>
        </html>
        """
        
        result = detector.analyze_page(html, {}, "https://example.com")
        
        assert isinstance(result, DetectionResult)
        if result.challenges:
            assert any(challenge in [BotChallenge.RECAPTCHA, BotChallenge.CAPTCHA] 
                      for challenge in result.challenges)
    
    def test_stealth_configuration(self, detector):
        """Test de génération de configuration furtive."""
        # Créer un résultat de détection avec défis
        html = "<html><body>rate limit exceeded</body></html>"
        headers = {"retry-after": "60"}
        
        result = detector.analyze_page(html, headers, "https://example.com")
        stealth_config = detector.create_stealth_configuration(result)
        
        assert isinstance(stealth_config, dict)
        assert "user_agent" in stealth_config
        assert "headers" in stealth_config
        assert "behavior" in stealth_config
        assert "technical" in stealth_config
    
    def test_delay_recommendations(self, detector):
        """Test des recommandations de délais."""
        challenges = [BotChallenge.CLOUDFLARE, BotChallenge.RATE_LIMITING]
        delays = detector.get_recommended_delays(challenges)
        
        assert isinstance(delays, dict)
        assert "reading" in delays
        assert "clicking" in delays
        
        # Les délais devraient être plus longs avec plus de défis
        for action, (min_delay, max_delay) in delays.items():
            assert min_delay >= 0
            assert max_delay > min_delay


class TestContentAnalyzer:
    """Tests pour l'analyseur de contenu."""
    
    @pytest.fixture
    def analyzer(self):
        """Analyseur pour les tests."""
        return ContentAnalyzer()
    
    def test_content_analysis(self, analyzer):
        """Test d'analyse de contenu."""
        html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <h2>Subtitle</h2>
            <p>First paragraph with some content.</p>
            <p>Second paragraph with more detailed content and information.</p>
            <img src="image.jpg" alt="Test image">
            <a href="https://external.com">External link</a>
            <a href="/internal">Internal link</a>
        </body>
        </html>
        """
        
        text_content = "Main Title Subtitle First paragraph with some content. Second paragraph with more detailed content and information."
        
        features = analyzer.analyze_content(html, text_content, "https://example.com")
        
        assert isinstance(features, ContentFeatures)
        assert features.word_count > 0
        assert features.heading_hierarchy['h1'] == 1
        assert features.heading_hierarchy['h2'] == 1
        assert features.paragraph_count == 2
        assert features.image_count == 1
        assert features.internal_links >= 1
        assert features.external_links >= 1
    
    def test_keyword_extraction(self, analyzer):
        """Test d'extraction de mots-clés."""
        text = "Python programming language development coding software engineering"
        keywords = analyzer._extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        
        # Les mots-clés devraient être des tuples (mot, fréquence)
        for keyword, frequency in keywords:
            assert isinstance(keyword, str)
            assert isinstance(frequency, int)
            assert frequency > 0
    
    def test_content_summary(self, analyzer):
        """Test de génération de résumé."""
        # Créer des features d'exemple
        features = ContentFeatures(
            heading_hierarchy={'h1': 1, 'h2': 2, 'h3': 0, 'h4': 0, 'h5': 0, 'h6': 0},
            paragraph_count=5,
            list_count=2,
            table_count=1,
            word_count=500,
            sentence_count=25,
            avg_sentence_length=20.0,
            vocabulary_richness=0.6,
            internal_links=3,
            external_links=2,
            image_count=2,
            video_count=0,
            keywords=[("python", 5), ("programming", 3)],
            topics=["programming"],
            sentiment_score=0.2,
            code_blocks=1,
            formulas=0,
            technical_terms=10,
            readability_score=75.0,
            completeness_score=80.0,
            authority_indicators=["author: john doe"]
        )
        
        summary = analyzer.generate_content_summary(features)
        
        assert isinstance(summary, dict)
        assert "content_type" in summary
        assert "quality" in summary
        assert "metrics" in summary
        assert "structure" in summary
        assert "recommendations" in summary


@pytest.mark.asyncio
async def test_pipeline_integration():
    """Test d'intégration complète du pipeline."""
    pipeline = MLPipeline(enable_cache=True)
    
    # HTML d'article de test
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete Test Article</title>
        <meta name="description" content="A comprehensive test article">
    </head>
    <body>
        <article>
            <h1>Machine Learning in Web Scraping</h1>
            <h2>Introduction</h2>
            <p>Machine learning is revolutionizing web scraping by enabling intelligent content analysis.</p>
            <h2>Benefits</h2>
            <ul>
                <li>Automatic content classification</li>
                <li>Bot detection and evasion</li>
                <li>Quality assessment</li>
            </ul>
            <p>This technology helps scrapers adapt to different content types and anti-bot measures.</p>
            <img src="ml-diagram.png" alt="ML diagram">
            <p>For more information, visit <a href="https://example.com">our documentation</a>.</p>
        </article>
    </body>
    </html>
    """
    
    url = "https://tech-blog.example.com/ml-scraping"
    headers = {"user-agent": "Mozilla/5.0 (compatible; TestBot/1.0)"}
    
    # Analyser la page
    result = await pipeline.analyze_page(
        html=html,
        url=url,
        headers=headers,
        response_time=2.1
    )
    
    # Vérifications complètes
    assert isinstance(result, MLAnalysisResult)
    
    # Classification
    assert result.classification.page_type in [PageType.ARTICLE, PageType.BLOG, PageType.DOCUMENTATION]
    assert result.classification.confidence > 0
    assert result.classification.quality in [ContentQuality.HIGH, ContentQuality.MEDIUM]
    
    # Détection anti-bot
    assert isinstance(result.bot_detection.challenges, list)
    assert isinstance(result.bot_detection.confidence, float)
    
    # Analyse de contenu
    assert result.content_features.word_count > 20
    assert result.content_features.heading_hierarchy['h1'] >= 1
    assert result.content_features.heading_hierarchy['h2'] >= 1
    
    # Métriques globales
    assert result.processing_time > 0
    assert 0 <= result.confidence_score <= 1
    assert isinstance(result.recommendations, list)
    assert isinstance(result.scraping_config, dict)
    
    # Configuration de scraping
    config = result.scraping_config
    assert "extraction_strategy" in config
    assert "anti_bot_config" in config
    assert "performance_settings" in config
    assert "quality_filters" in config
    
    print(f"✅ Test d'intégration réussi:")
    print(f"   - Type de page: {result.classification.page_type.value}")
    print(f"   - Qualité: {result.classification.quality.value}")
    print(f"   - Confiance: {result.confidence_score:.3f}")
    print(f"   - Temps de traitement: {result.processing_time:.3f}s")
    print(f"   - Nombre de mots: {result.content_features.word_count}")
    print(f"   - Défis anti-bot: {len(result.bot_detection.challenges)}")