"""Analyseur de contenu avancé pour Scrapinium."""

import re
import json
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass
from collections import Counter
import hashlib
from urllib.parse import urlparse

@dataclass
class ContentFeatures:
    """Caractéristiques extraites du contenu."""
    # Structure et organisation
    heading_hierarchy: Dict[str, int]    # h1-h6 counts
    paragraph_count: int
    list_count: int
    table_count: int
    
    # Métriques textuelles
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    vocabulary_richness: float
    
    # Liens et médias
    internal_links: int
    external_links: int
    image_count: int
    video_count: int
    
    # Sémantique
    keywords: List[Tuple[str, int]]      # (keyword, frequency)
    topics: List[str]
    sentiment_score: float
    
    # Technique
    code_blocks: int
    formulas: int
    technical_terms: int
    
    # Qualité
    readability_score: float
    completeness_score: float
    authority_indicators: List[str]

class ContentAnalyzer:
    """Analyseur avancé de contenu web."""
    
    def __init__(self):
        # Mots vides français et anglais
        self.stop_words = {
            'fr': {
                'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais', 
                'donc', 'car', 'avec', 'dans', 'sur', 'pour', 'par', 'ce', 'qui', 'que',
                'dont', 'où', 'est', 'sont', 'être', 'avoir', 'fait', 'très', 'plus',
                'comme', 'tout', 'tous', 'peut', 'sans', 'après', 'avant', 'entre'
            },
            'en': {
                'the', 'and', 'or', 'but', 'with', 'from', 'about', 'this', 'that',
                'they', 'have', 'been', 'will', 'would', 'could', 'should', 'there',
                'their', 'what', 'when', 'where', 'which', 'very', 'more', 'most',
                'like', 'some', 'make', 'time', 'after', 'before', 'between'
            }
        }
        
        # Indicateurs d'autorité et de qualité
        self.authority_indicators = [
            # Auteur et crédibilité
            r'author:', r'by\s+\w+', r'written by', r'écrit par',
            r'expert', r'specialist', r'doctor', r'professor', r'phd',
            
            # Sources et références
            r'source:', r'sources?:', r'reference', r'citation',
            r'study', r'research', r'étude', r'recherche',
            
            # Dates et mise à jour
            r'updated:', r'last modified', r'mis à jour',
            r'published:', r'publié le',
            
            # Certifications et accréditations
            r'certified', r'accredited', r'certified by',
            r'certifié', r'accrédité'
        ]
        
        # Termes techniques par domaine
        self.technical_domains = {
            'programming': [
                'function', 'variable', 'class', 'method', 'array', 'object',
                'algorithm', 'framework', 'library', 'api', 'database',
                'javascript', 'python', 'java', 'html', 'css', 'sql'
            ],
            'science': [
                'hypothesis', 'experiment', 'analysis', 'data', 'result',
                'conclusion', 'methodology', 'statistical', 'correlation'
            ],
            'medicine': [
                'symptom', 'treatment', 'diagnosis', 'patient', 'therapy',
                'clinical', 'medical', 'health', 'disease', 'syndrome'
            ],
            'finance': [
                'investment', 'portfolio', 'risk', 'return', 'market',
                'stock', 'bond', 'asset', 'revenue', 'profit', 'loss'
            ]
        }
        
        # Patterns pour détecter du code
        self.code_patterns = [
            r'<code>.*?</code>',
            r'```.*?```',
            r'`[^`]+`',
            r'function\s+\w+\s*\(',
            r'class\s+\w+\s*[{:]',
            r'def\s+\w+\s*\(',
            r'import\s+\w+',
            r'#include\s*<',
            r'SELECT\s+.*FROM',
            r'<\w+[^>]*>'
        ]
        
        # Patterns pour les formules mathématiques
        self.formula_patterns = [
            r'\$[^$]+\$',           # LaTeX inline
            r'\$\$[^$]+\$\$',       # LaTeX block
            r'\\[a-zA-Z]+\{[^}]*\}', # LaTeX commands
            r'\b\d+\s*[+\-*/=]\s*\d+', # Simple equations
            r'[a-zA-Z]\s*=\s*[^,\s]+' # Variable assignments
        ]
    
    def analyze_content(self, html: str, text_content: str, url: str) -> ContentFeatures:
        """Analyse complète du contenu."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Nettoyer le contenu
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extraire les caractéristiques
        features = ContentFeatures(
            # Structure
            heading_hierarchy=self._analyze_heading_hierarchy(soup),
            paragraph_count=len(soup.find_all('p')),
            list_count=len(soup.find_all(['ul', 'ol'])),
            table_count=len(soup.find_all('table')),
            
            # Métriques textuelles
            word_count=len(text_content.split()),
            sentence_count=self._count_sentences(text_content),
            avg_sentence_length=self._calculate_avg_sentence_length(text_content),
            vocabulary_richness=self._calculate_vocabulary_richness(text_content),
            
            # Liens et médias
            internal_links=self._count_internal_links(soup, url),
            external_links=self._count_external_links(soup, url),
            image_count=len(soup.find_all('img')),
            video_count=len(soup.find_all(['video', 'iframe'])),
            
            # Sémantique
            keywords=self._extract_keywords(text_content),
            topics=self._identify_topics(text_content),
            sentiment_score=self._analyze_sentiment(text_content),
            
            # Technique
            code_blocks=self._count_code_blocks(html, text_content),
            formulas=self._count_formulas(text_content),
            technical_terms=self._count_technical_terms(text_content),
            
            # Qualité
            readability_score=self._calculate_readability(text_content),
            completeness_score=self._assess_completeness(soup, text_content),
            authority_indicators=self._find_authority_indicators(text_content)
        )
        
        return features
    
    def _analyze_heading_hierarchy(self, soup) -> Dict[str, int]:
        """Analyse la hiérarchie des titres."""
        hierarchy = {}
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            hierarchy[f'h{level}'] = len(headings)
        return hierarchy
    
    def _count_sentences(self, text: str) -> int:
        """Compte le nombre de phrases."""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calcule la longueur moyenne des phrases."""
        sentences = re.split(r'[.!?]+', text)
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        
        if not valid_sentences:
            return 0.0
        
        total_words = sum(len(sentence.split()) for sentence in valid_sentences)
        return total_words / len(valid_sentences)
    
    def _calculate_vocabulary_richness(self, text: str) -> float:
        """Calcule la richesse du vocabulaire (ratio mots uniques/total)."""
        words = text.lower().split()
        if not words:
            return 0.0
        
        unique_words = set(words)
        return len(unique_words) / len(words)
    
    def _count_internal_links(self, soup, url: str) -> int:
        """Compte les liens internes."""
        domain = urlparse(url).netloc
        internal_count = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                if href.startswith('/') or domain in href:
                    internal_count += 1
        
        return internal_count
    
    def _count_external_links(self, soup, url: str) -> int:
        """Compte les liens externes."""
        domain = urlparse(url).netloc
        external_count = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith('http'):
                if domain not in href:
                    external_count += 1
        
        return external_count
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """Extrait les mots-clés les plus fréquents."""
        # Nettoyer le texte
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text.lower())
        
        # Supprimer les mots vides
        filtered_words = []
        for word in words:
            is_stop_word = False
            for lang_stops in self.stop_words.values():
                if word in lang_stops:
                    is_stop_word = True
                    break
            if not is_stop_word:
                filtered_words.append(word)
        
        # Compter les fréquences
        word_counts = Counter(filtered_words)
        return word_counts.most_common(top_n)
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identifie les sujets principaux basés sur les termes techniques."""
        text_lower = text.lower()
        topics = []
        
        for domain, terms in self.technical_domains.items():
            matches = sum(1 for term in terms if term in text_lower)
            if matches >= 3:  # Seuil minimum
                topics.append(domain)
        
        return topics
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyse de sentiment simple basée sur des mots-clés."""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'bon', 'excellent', 'génial', 'formidable', 'parfait', 'super'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
            'mauvais', 'terrible', 'affreux', 'horrible', 'pire', 'déteste'
        ]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0  # Neutre
        
        return (positive_count - negative_count) / total_sentiment_words
    
    def _count_code_blocks(self, html: str, text: str) -> int:
        """Compte les blocs de code."""
        count = 0
        combined_text = html + " " + text
        
        for pattern in self.code_patterns:
            matches = re.findall(pattern, combined_text, re.DOTALL | re.IGNORECASE)
            count += len(matches)
        
        return count
    
    def _count_formulas(self, text: str) -> int:
        """Compte les formules mathématiques."""
        count = 0
        
        for pattern in self.formula_patterns:
            matches = re.findall(pattern, text)
            count += len(matches)
        
        return count
    
    def _count_technical_terms(self, text: str) -> int:
        """Compte les termes techniques."""
        text_lower = text.lower()
        count = 0
        
        for domain_terms in self.technical_domains.values():
            for term in domain_terms:
                count += len(re.findall(r'\b' + re.escape(term) + r'\b', text_lower))
        
        return count
    
    def _calculate_readability(self, text: str) -> float:
        """Calcule un score de lisibilité simplifié."""
        words = text.split()
        sentences = self._count_sentences(text)
        
        if not words or not sentences:
            return 0.0
        
        avg_words_per_sentence = len(words) / sentences
        
        # Score basé sur la longueur des phrases (Flesch-Kincaid simplifié)
        if avg_words_per_sentence <= 10:
            return 90.0  # Très facile
        elif avg_words_per_sentence <= 15:
            return 75.0  # Facile
        elif avg_words_per_sentence <= 20:
            return 60.0  # Moyennement facile
        elif avg_words_per_sentence <= 25:
            return 45.0  # Difficile
        else:
            return 30.0  # Très difficile
    
    def _assess_completeness(self, soup, text: str) -> float:
        """Évalue la complétude du contenu."""
        score = 0.0
        max_score = 100.0
        
        # Présence d'introduction
        if len(text) > 200:
            score += 15.0
        
        # Structure avec titres
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(headings) >= 3:
            score += 20.0
        elif len(headings) >= 1:
            score += 10.0
        
        # Présence de listes ou tableaux (organisation)
        lists = soup.find_all(['ul', 'ol', 'table'])
        if len(lists) >= 2:
            score += 15.0
        elif len(lists) >= 1:
            score += 10.0
        
        # Longueur suffisante
        word_count = len(text.split())
        if word_count >= 1000:
            score += 20.0
        elif word_count >= 500:
            score += 15.0
        elif word_count >= 200:
            score += 10.0
        
        # Présence d'images ou médias
        images = soup.find_all(['img', 'video', 'iframe'])
        if len(images) >= 2:
            score += 15.0
        elif len(images) >= 1:
            score += 10.0
        
        # Liens externes (sources)
        external_links = self._count_external_links(soup, "")
        if external_links >= 3:
            score += 15.0
        elif external_links >= 1:
            score += 10.0
        
        return min(score, max_score)
    
    def _find_authority_indicators(self, text: str) -> List[str]:
        """Trouve les indicateurs d'autorité dans le texte."""
        indicators = []
        text_lower = text.lower()
        
        for pattern in self.authority_indicators:
            matches = re.findall(pattern, text_lower)
            if matches:
                indicators.extend(matches)
        
        return list(set(indicators))  # Supprimer les doublons
    
    def generate_content_summary(self, features: ContentFeatures) -> Dict[str, Any]:
        """Génère un résumé des caractéristiques du contenu."""
        
        # Déterminer le type de contenu dominant
        content_type = self._determine_content_type(features)
        
        # Évaluer la qualité globale
        quality_score = self._calculate_quality_score(features)
        
        # Recommandations d'amélioration
        recommendations = self._generate_recommendations(features)
        
        summary = {
            'content_type': content_type,
            'quality': {
                'overall_score': quality_score,
                'readability': features.readability_score,
                'completeness': features.completeness_score,
                'authority': len(features.authority_indicators)
            },
            'metrics': {
                'word_count': features.word_count,
                'vocabulary_richness': features.vocabulary_richness,
                'avg_sentence_length': features.avg_sentence_length,
                'technical_complexity': features.technical_terms / max(features.word_count, 1) * 100
            },
            'structure': {
                'has_good_hierarchy': self._has_good_heading_hierarchy(features.heading_hierarchy),
                'has_lists': features.list_count > 0,
                'has_tables': features.table_count > 0,
                'has_media': features.image_count + features.video_count > 0
            },
            'topics': features.topics,
            'top_keywords': features.keywords[:10],
            'recommendations': recommendations
        }
        
        return summary
    
    def _determine_content_type(self, features: ContentFeatures) -> str:
        """Détermine le type de contenu basé sur les caractéristiques."""
        
        # Article technique/documentation
        if features.code_blocks > 5 or 'programming' in features.topics:
            return 'technical_article'
        
        # Article scientifique
        if features.formulas > 3 or 'science' in features.topics:
            return 'scientific_article'
        
        # Article éditorial/blog
        if features.sentiment_score != 0 and features.word_count > 500:
            return 'editorial_article'
        
        # Guide/tutorial
        if features.list_count > 3 and len(features.authority_indicators) > 0:
            return 'guide_tutorial'
        
        # Article informationnel
        if features.external_links > 5 and features.completeness_score > 70:
            return 'informational_article'
        
        return 'general_content'
    
    def _calculate_quality_score(self, features: ContentFeatures) -> float:
        """Calcule un score de qualité global."""
        score = 0.0
        
        # Lisibilité (25%)
        score += (features.readability_score / 100) * 25
        
        # Complétude (25%)
        score += (features.completeness_score / 100) * 25
        
        # Structure (20%)
        structure_score = 0
        if self._has_good_heading_hierarchy(features.heading_hierarchy):
            structure_score += 50
        if features.list_count > 0:
            structure_score += 25
        if features.table_count > 0:
            structure_score += 25
        score += (structure_score / 100) * 20
        
        # Richesse du contenu (15%)
        richness_score = min(100, features.vocabulary_richness * 100 + 
                           (features.image_count + features.video_count) * 10)
        score += (richness_score / 100) * 15
        
        # Autorité (15%)
        authority_score = min(100, len(features.authority_indicators) * 20)
        score += (authority_score / 100) * 15
        
        return round(score, 1)
    
    def _has_good_heading_hierarchy(self, hierarchy: Dict[str, int]) -> bool:
        """Vérifie si la hiérarchie des titres est bien structurée."""
        h1_count = hierarchy.get('h1', 0)
        h2_count = hierarchy.get('h2', 0)
        
        # Au moins un H1 et quelques H2/H3
        return h1_count >= 1 and (h2_count + hierarchy.get('h3', 0)) >= 2
    
    def _generate_recommendations(self, features: ContentFeatures) -> List[str]:
        """Génère des recommandations d'amélioration."""
        recommendations = []
        
        # Longueur du contenu
        if features.word_count < 300:
            recommendations.append("Développer le contenu - moins de 300 mots")
        elif features.word_count > 3000:
            recommendations.append("Considérer diviser en plusieurs articles")
        
        # Structure
        if not self._has_good_heading_hierarchy(features.heading_hierarchy):
            recommendations.append("Améliorer la hiérarchie des titres (H1, H2, H3)")
        
        # Lisibilité
        if features.readability_score < 50:
            recommendations.append("Simplifier les phrases pour améliorer la lisibilité")
        
        # Richesse
        if features.vocabulary_richness < 0.3:
            recommendations.append("Diversifier le vocabulaire")
        
        # Médias
        if features.image_count == 0 and features.word_count > 500:
            recommendations.append("Ajouter des images pour illustrer le contenu")
        
        # Sources
        if features.external_links < 2 and features.word_count > 800:
            recommendations.append("Ajouter des références et sources externes")
        
        # Complétude
        if features.completeness_score < 60:
            recommendations.append("Améliorer la complétude du contenu")
        
        return recommendations