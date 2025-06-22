"""Classificateur intelligent de contenu web."""

import re
import json
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import Counter
import numpy as np
from urllib.parse import urlparse

class PageType(Enum):
    """Types de pages web détectés."""
    ARTICLE = "article"
    ECOMMERCE = "ecommerce" 
    BLOG = "blog"
    FORUM = "forum"
    NEWS = "news"
    SOCIAL = "social"
    DOCUMENTATION = "documentation"
    LANDING = "landing"
    SEARCH_RESULTS = "search_results"
    UNKNOWN = "unknown"

class ContentQuality(Enum):
    """Qualité du contenu détectée."""
    HIGH = "high"          # Contenu riche et structuré
    MEDIUM = "medium"      # Contenu correct
    LOW = "low"           # Contenu pauvre
    SPAM = "spam"         # Contenu spam/publicitaire

@dataclass
class ClassificationResult:
    """Résultat de classification d'une page."""
    page_type: PageType
    confidence: float
    quality: ContentQuality
    language: str
    features: Dict[str, Any]
    metadata: Dict[str, Any]

class ContentClassifier:
    """Classificateur intelligent de contenu web."""
    
    def __init__(self):
        self.language_patterns = {
            'fr': [
                r'\b(le|la|les|un|une|des|du|de|et|ou|mais|donc|car|avec|dans|sur|pour|par)\b',
                r'\b(français|france|article|contenu)\b'
            ],
            'en': [
                r'\b(the|and|or|but|with|from|about|this|that|they|have|been|will)\b',
                r'\b(english|article|content|website)\b'
            ],
            'es': [
                r'\b(el|la|los|las|un|una|de|en|y|o|pero|con|por|para)\b',
                r'\b(español|artículo|contenido)\b'
            ]
        }
        
        # Patterns pour détecter les types de pages
        self.page_patterns = {
            PageType.ARTICLE: {
                'selectors': ['article', '.article', '.post', '.content', '.entry'],
                'keywords': ['article', 'author', 'published', 'read more', 'share'],
                'url_patterns': [r'/article/', r'/post/', r'/blog/', r'/news/']
            },
            PageType.ECOMMERCE: {
                'selectors': ['.product', '.price', '.cart', '.buy', '.shop'],
                'keywords': ['price', 'buy now', 'add to cart', 'product', 'purchase', 'shipping'],
                'url_patterns': [r'/product/', r'/shop/', r'/store/', r'/buy/']
            },
            PageType.BLOG: {
                'selectors': ['.blog', '.post', '.entry', '.article-content'],
                'keywords': ['blog', 'posted by', 'comments', 'tags', 'category'],
                'url_patterns': [r'/blog/', r'/posts/', r'/entries/']
            },
            PageType.FORUM: {
                'selectors': ['.forum', '.thread', '.reply', '.discussion'],
                'keywords': ['forum', 'thread', 'reply', 'discussion', 'topic', 'post'],
                'url_patterns': [r'/forum/', r'/thread/', r'/discussion/']
            },
            PageType.NEWS: {
                'selectors': ['.news', '.article', '.story'],
                'keywords': ['breaking news', 'latest', 'updated', 'reporter', 'news'],
                'url_patterns': [r'/news/', r'/breaking/', r'/latest/']
            },
            PageType.DOCUMENTATION: {
                'selectors': ['.docs', '.documentation', '.api', '.guide'],
                'keywords': ['documentation', 'api', 'guide', 'tutorial', 'reference'],
                'url_patterns': [r'/docs/', r'/documentation/', r'/api/', r'/guide/']
            }
        }
        
        # Indicateurs de qualité
        self.quality_indicators = {
            'high': {
                'min_word_count': 500,
                'structured_content': True,
                'headings_present': True,
                'images_present': True,
                'low_ad_ratio': True
            },
            'spam': {
                'keywords': ['click here', 'free money', 'limited time', 'act now', 'guaranteed'],
                'excessive_caps': True,
                'excessive_punctuation': True,
                'low_content_ratio': True
            }
        }
    
    def classify_page(self, html: str, url: str, metadata: Dict[str, Any] = None) -> ClassificationResult:
        """Classifie une page web complète."""
        
        # Extraire les features de base
        features = self._extract_features(html, url)
        
        # Détecter le type de page
        page_type, type_confidence = self._classify_page_type(features, url)
        
        # Évaluer la qualité du contenu
        quality = self._assess_content_quality(features)
        
        # Détecter la langue
        language = self._detect_language(features['text_content'])
        
        # Construire les métadonnées enrichies
        enriched_metadata = {
            'word_count': features['word_count'],
            'heading_count': features['heading_count'],
            'link_count': features['link_count'],
            'image_count': features['image_count'],
            'text_density': features['text_density'],
            'structure_score': features['structure_score'],
            **(metadata or {})
        }
        
        return ClassificationResult(
            page_type=page_type,
            confidence=type_confidence,
            quality=quality,
            language=language,
            features=features,
            metadata=enriched_metadata
        )
    
    def _extract_features(self, html: str, url: str) -> Dict[str, Any]:
        """Extrait les caractéristiques de la page."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Nettoyer le HTML (enlever scripts, styles, etc.)
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extraire le texte principal
        text_content = soup.get_text()
        words = text_content.split()
        
        # Compter les éléments structurels
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        links = soup.find_all('a', href=True)
        images = soup.find_all('img')
        paragraphs = soup.find_all('p')
        
        # Calculer la densité de texte
        html_length = len(html)
        text_length = len(text_content.strip())
        text_density = text_length / html_length if html_length > 0 else 0
        
        # Score de structure (basé sur la présence d'éléments structurels)
        structure_score = min(100, (
            len(headings) * 10 +
            min(len(paragraphs), 20) * 2 +
            (20 if soup.find('article') else 0) +
            (15 if soup.find('main') else 0)
        ))
        
        # Détecter les sélecteurs spéciaux
        special_selectors = []
        for page_type, patterns in self.page_patterns.items():
            for selector in patterns['selectors']:
                if soup.select(selector):
                    special_selectors.append((page_type.value, selector))
        
        # Analyser l'URL
        parsed_url = urlparse(url)
        url_path = parsed_url.path.lower()
        
        return {
            'word_count': len(words),
            'text_content': text_content[:5000],  # Premiers 5000 chars pour analyse
            'heading_count': len(headings),
            'link_count': len(links),
            'image_count': len(images),
            'paragraph_count': len(paragraphs),
            'text_density': text_density,
            'structure_score': structure_score,
            'special_selectors': special_selectors,
            'url_path': url_path,
            'domain': parsed_url.netloc,
            'title': soup.find('title').get_text() if soup.find('title') else '',
            'meta_description': self._get_meta_description(soup),
            'has_forms': len(soup.find_all('form')) > 0,
            'has_tables': len(soup.find_all('table')) > 0
        }
    
    def _classify_page_type(self, features: Dict[str, Any], url: str) -> Tuple[PageType, float]:
        """Classifie le type de page."""
        scores = {page_type: 0.0 for page_type in PageType}
        
        # Analyser les sélecteurs spéciaux trouvés
        for page_type_str, selector in features['special_selectors']:
            try:
                page_type = PageType(page_type_str)
                scores[page_type] += 20
            except ValueError:
                pass
        
        # Analyser l'URL
        url_lower = url.lower()
        for page_type, patterns in self.page_patterns.items():
            for pattern in patterns['url_patterns']:
                if re.search(pattern, url_lower):
                    scores[page_type] += 15
        
        # Analyser le contenu textuel
        text_lower = features['text_content'].lower()
        for page_type, patterns in self.page_patterns.items():
            keyword_matches = sum(1 for keyword in patterns['keywords'] 
                                if keyword in text_lower)
            scores[page_type] += keyword_matches * 5
        
        # Heuristiques basées sur la structure
        if features['word_count'] > 300 and features['structure_score'] > 50:
            scores[PageType.ARTICLE] += 10
        
        if features['has_forms'] and 'price' in text_lower:
            scores[PageType.ECOMMERCE] += 15
        
        if features['heading_count'] > 5 and 'documentation' in text_lower:
            scores[PageType.DOCUMENTATION] += 10
        
        # Trouver le type avec le score le plus élevé
        best_type = max(scores.items(), key=lambda x: x[1])
        
        if best_type[1] > 10:  # Seuil de confiance minimum
            confidence = min(0.95, best_type[1] / 100)
            return best_type[0], confidence
        else:
            return PageType.UNKNOWN, 0.1
    
    def _assess_content_quality(self, features: Dict[str, Any]) -> ContentQuality:
        """Évalue la qualité du contenu."""
        
        # Détecter le spam
        text_lower = features['text_content'].lower()
        spam_indicators = 0
        
        for spam_keyword in self.quality_indicators['spam']['keywords']:
            if spam_keyword in text_lower:
                spam_indicators += 1
        
        # Détecter l'excès de majuscules
        caps_ratio = sum(1 for c in features['text_content'] if c.isupper()) / max(len(features['text_content']), 1)
        if caps_ratio > 0.3:
            spam_indicators += 2
        
        # Détecter l'excès de ponctuation
        punct_ratio = sum(1 for c in features['text_content'] if c in '!?.,;:') / max(len(features['text_content']), 1)
        if punct_ratio > 0.1:
            spam_indicators += 1
        
        if spam_indicators >= 3:
            return ContentQuality.SPAM
        
        # Évaluer la qualité
        quality_score = 0
        
        # Nombre de mots
        if features['word_count'] >= 500:
            quality_score += 25
        elif features['word_count'] >= 200:
            quality_score += 15
        elif features['word_count'] >= 50:
            quality_score += 5
        
        # Structure
        if features['structure_score'] > 70:
            quality_score += 30
        elif features['structure_score'] > 40:
            quality_score += 20
        elif features['structure_score'] > 20:
            quality_score += 10
        
        # Densité de texte
        if features['text_density'] > 0.1:
            quality_score += 20
        elif features['text_density'] > 0.05:
            quality_score += 10
        
        # Présence d'images et de liens
        if features['image_count'] > 0:
            quality_score += 10
        if features['link_count'] > 0:
            quality_score += 5
        
        # Classification finale
        if quality_score >= 70:
            return ContentQuality.HIGH
        elif quality_score >= 40:
            return ContentQuality.MEDIUM
        else:
            return ContentQuality.LOW
    
    def _detect_language(self, text: str) -> str:
        """Détecte la langue du contenu."""
        text_lower = text.lower()
        
        language_scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            language_scores[lang] = score
        
        if not language_scores or max(language_scores.values()) == 0:
            return 'unknown'
        
        detected_lang = max(language_scores.items(), key=lambda x: x[1])
        return detected_lang[0] if detected_lang[1] > 5 else 'unknown'
    
    def _get_meta_description(self, soup) -> str:
        """Extrait la meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')
        
        # Essayer og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content')
        
        return ''
    
    def get_content_insights(self, classification: ClassificationResult) -> Dict[str, Any]:
        """Génère des insights sur le contenu classifié."""
        
        insights = {
            'summary': f"Page de type '{classification.page_type.value}' "
                      f"avec une qualité '{classification.quality.value}' "
                      f"(confiance: {classification.confidence:.1%})",
            
            'recommendations': [],
            'extraction_strategy': self._get_extraction_strategy(classification),
            'quality_metrics': {
                'readability_score': self._calculate_readability_score(classification.features),
                'content_richness': self._calculate_content_richness(classification.features),
                'structure_quality': classification.features['structure_score']
            }
        }
        
        # Recommandations basées sur le type de page
        if classification.page_type == PageType.ARTICLE:
            insights['recommendations'].append("Extraire le titre, auteur, date et contenu principal")
        elif classification.page_type == PageType.ECOMMERCE:
            insights['recommendations'].append("Focus sur les prix, descriptions produits et avis")
        elif classification.page_type == PageType.BLOG:
            insights['recommendations'].append("Extraire les métadonnées du post et les commentaires")
        
        # Recommandations basées sur la qualité
        if classification.quality == ContentQuality.LOW:
            insights['recommendations'].append("Contenu peu dense - vérifier les éléments cachés")
        elif classification.quality == ContentQuality.SPAM:
            insights['recommendations'].append("Contenu détecté comme spam - filtrage recommandé")
        
        return insights
    
    def _get_extraction_strategy(self, classification: ClassificationResult) -> Dict[str, Any]:
        """Détermine la stratégie d'extraction optimale."""
        
        strategy = {
            'selectors': [],
            'priority_elements': [],
            'avoid_elements': ['nav', 'footer', 'aside', '.ad', '.advertisement']
        }
        
        # Stratégies par type de page
        if classification.page_type == PageType.ARTICLE:
            strategy['selectors'] = ['article', '.content', '.post-content', '.entry-content']
            strategy['priority_elements'] = ['h1', 'h2', 'p', 'img', 'blockquote']
        
        elif classification.page_type == PageType.ECOMMERCE:
            strategy['selectors'] = ['.product', '.product-details', '.item-description']
            strategy['priority_elements'] = ['.price', '.description', '.reviews', 'img']
        
        elif classification.page_type == PageType.BLOG:
            strategy['selectors'] = ['.post', '.entry', '.blog-content']
            strategy['priority_elements'] = ['h1', 'h2', '.meta', '.content', '.tags']
        
        elif classification.page_type == PageType.DOCUMENTATION:
            strategy['selectors'] = ['.docs', '.documentation', '.api-docs']
            strategy['priority_elements'] = ['h1', 'h2', 'h3', 'code', '.example', 'table']
        
        return strategy
    
    def _calculate_readability_score(self, features: Dict[str, Any]) -> float:
        """Calcule un score de lisibilité simple."""
        
        if features['word_count'] == 0:
            return 0.0
        
        # Ratio mots/phrases (approximation)
        sentences = features['text_content'].count('.') + features['text_content'].count('!') + features['text_content'].count('?')
        sentences = max(sentences, 1)
        
        avg_words_per_sentence = features['word_count'] / sentences
        
        # Score basé sur la longueur moyenne des phrases
        if avg_words_per_sentence <= 15:
            return 85.0  # Très lisible
        elif avg_words_per_sentence <= 25:
            return 70.0  # Lisible
        elif avg_words_per_sentence <= 35:
            return 55.0  # Moyennement lisible
        else:
            return 30.0  # Difficile à lire
    
    def _calculate_content_richness(self, features: Dict[str, Any]) -> float:
        """Calcule la richesse du contenu."""
        
        richness_score = 0
        
        # Diversité des éléments
        if features['heading_count'] > 0:
            richness_score += 20
        if features['image_count'] > 0:
            richness_score += 15
        if features['link_count'] > 0:
            richness_score += 10
        if features['has_tables']:
            richness_score += 10
        
        # Longueur du contenu
        if features['word_count'] > 1000:
            richness_score += 25
        elif features['word_count'] > 500:
            richness_score += 15
        elif features['word_count'] > 200:
            richness_score += 10
        
        # Structure
        richness_score += min(20, features['structure_score'] / 5)
        
        return min(100.0, richness_score)