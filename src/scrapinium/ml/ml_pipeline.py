"""Pipeline Machine Learning intégré pour Scrapinium."""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .content_classifier import ContentClassifier, ClassificationResult
from .antibot_detector import AntibotDetector, DetectionResult as BotDetectionResult
from .content_analyzer import ContentAnalyzer, ContentFeatures

@dataclass
class MLAnalysisResult:
    """Résultat complet de l'analyse ML."""
    # Classification de contenu
    classification: ClassificationResult
    
    # Détection anti-bot
    bot_detection: BotDetectionResult
    
    # Analyse de contenu
    content_features: ContentFeatures
    content_summary: Dict[str, Any]
    
    # Métadonnées
    processing_time: float
    confidence_score: float
    recommendations: List[str]
    
    # Configuration recommandée pour le scraping
    scraping_config: Dict[str, Any]

class MLPipeline:
    """Pipeline ML intégré pour l'analyse intelligente de contenu web."""
    
    def __init__(self):
        self.content_classifier = ContentClassifier()
        self.antibot_detector = AntibotDetector()
        self.content_analyzer = ContentAnalyzer()
        
        # Métriques de performance
        self.analysis_history = []
        self.performance_stats = {
            'total_analyses': 0,
            'avg_processing_time': 0.0,
            'success_rate': 0.0
        }
    
    async def analyze_page(self, html: str, url: str, headers: Dict[str, str] = None, 
                          response_time: float = None, metadata: Dict[str, Any] = None) -> MLAnalysisResult:
        """Analyse complète d'une page web avec ML."""
        
        start_time = datetime.now()
        
        try:
            # 1. Classification du contenu
            classification = self.content_classifier.classify_page(
                html=html, 
                url=url, 
                metadata=metadata
            )
            
            # 2. Détection anti-bot
            bot_detection = self.antibot_detector.analyze_page(
                html=html,
                headers=headers or {},
                url=url,
                response_time=response_time
            )
            
            # 3. Analyse de contenu avancée
            text_content = classification.features.get('text_content', '')
            content_features = self.content_analyzer.analyze_content(
                html=html,
                text_content=text_content,
                url=url
            )
            
            # 4. Générer le résumé de contenu
            content_summary = self.content_analyzer.generate_content_summary(content_features)
            
            # 5. Calculer le temps de traitement
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 6. Calculer le score de confiance global
            confidence_score = self._calculate_global_confidence(
                classification, bot_detection, content_features
            )
            
            # 7. Générer les recommandations
            recommendations = self._generate_recommendations(
                classification, bot_detection, content_summary
            )
            
            # 8. Créer la configuration de scraping optimisée
            scraping_config = self._create_scraping_config(
                classification, bot_detection, content_features
            )
            
            # Créer le résultat complet
            result = MLAnalysisResult(
                classification=classification,
                bot_detection=bot_detection,
                content_features=content_features,
                content_summary=content_summary,
                processing_time=processing_time,
                confidence_score=confidence_score,
                recommendations=recommendations,
                scraping_config=scraping_config
            )
            
            # Mettre à jour les statistiques
            self._update_performance_stats(result, success=True)
            
            return result
            
        except Exception as e:
            self._update_performance_stats(None, success=False)
            raise Exception(f"Erreur dans le pipeline ML: {str(e)}")
    
    def _calculate_global_confidence(self, classification: ClassificationResult, 
                                   bot_detection: BotDetectionResult, 
                                   content_features: ContentFeatures) -> float:
        """Calcule un score de confiance global."""
        
        # Score de classification (40%)
        classification_score = classification.confidence * 0.4
        
        # Score de détection bot (30%)
        # Plus il y a de défis détectés, moins on est confiant
        bot_score = max(0, 1.0 - bot_detection.confidence) * 0.3
        
        # Score de qualité du contenu (30%)
        content_quality_score = 0.0
        if hasattr(content_features, 'readability_score'):
            content_quality_score = (content_features.readability_score / 100) * 0.15
        if hasattr(content_features, 'completeness_score'):
            content_quality_score += (content_features.completeness_score / 100) * 0.15
        
        global_score = classification_score + bot_score + content_quality_score
        return round(min(1.0, max(0.0, global_score)), 3)
    
    def _generate_recommendations(self, classification: ClassificationResult,
                                bot_detection: BotDetectionResult,
                                content_summary: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse ML."""
        
        recommendations = []
        
        # Recommandations basées sur la classification
        if classification.confidence < 0.7:
            recommendations.append("Confiance de classification faible - vérifier le type de contenu")
        
        if classification.quality.value == 'spam':
            recommendations.append("Contenu détecté comme spam - filtrage recommandé")
        elif classification.quality.value == 'low':
            recommendations.append("Qualité de contenu faible - extraction sélective recommandée")
        
        # Recommandations basées sur la détection anti-bot
        if bot_detection.confidence > 0.5:
            recommendations.append("Défis anti-bot détectés - utiliser le mode furtif")
            
            if len(bot_detection.challenges) > 2:
                recommendations.append("Multiples défis détectés - rotation d'IP recommandée")
        
        # Recommandations basées sur l'analyse de contenu
        content_quality = content_summary.get('quality', {})
        if content_quality.get('overall_score', 0) < 50:
            recommendations.append("Score de qualité faible - extraction ciblée recommandée")
        
        # Recommandations d'amélioration du contenu
        content_recommendations = content_summary.get('recommendations', [])
        recommendations.extend([f"Contenu: {rec}" for rec in content_recommendations[:3]])
        
        return recommendations
    
    def _create_scraping_config(self, classification: ClassificationResult,
                              bot_detection: BotDetectionResult,
                              content_features: ContentFeatures) -> Dict[str, Any]:
        """Crée une configuration de scraping optimisée."""
        
        config = {
            'extraction_strategy': {},
            'anti_bot_config': {},
            'performance_settings': {},
            'quality_filters': {}
        }
        
        # Stratégie d'extraction basée sur la classification
        insights = self.content_classifier.get_content_insights(classification)
        config['extraction_strategy'] = insights.get('extraction_strategy', {})
        
        # Configuration anti-bot
        if bot_detection.confidence > 0.3:
            stealth_config = self.antibot_detector.create_stealth_configuration(bot_detection)
            config['anti_bot_config'] = stealth_config
            
            # Délais recommandés
            delays = self.antibot_detector.get_recommended_delays(bot_detection.challenges)
            config['anti_bot_config']['delays'] = delays
        
        # Paramètres de performance
        config['performance_settings'] = {
            'concurrent_requests': 1 if bot_detection.confidence > 0.5 else 3,
            'request_delay': 2.0 if bot_detection.confidence > 0.5 else 1.0,
            'timeout': 30 if classification.page_type.value == 'ecommerce' else 15,
            'retries': 3 if bot_detection.confidence > 0.5 else 1
        }
        
        # Filtres de qualité
        config['quality_filters'] = {
            'min_word_count': 50 if classification.quality.value == 'high' else 200,
            'skip_if_spam': classification.quality.value == 'spam',
            'extract_images': content_features.image_count > 0,
            'extract_links': content_features.internal_links + content_features.external_links > 5
        }
        
        return config
    
    def _update_performance_stats(self, result: Optional[MLAnalysisResult], success: bool):
        """Met à jour les statistiques de performance."""
        
        self.performance_stats['total_analyses'] += 1
        
        if success and result:
            # Mettre à jour le temps de traitement moyen
            current_avg = self.performance_stats['avg_processing_time']
            total = self.performance_stats['total_analyses']
            
            new_avg = ((current_avg * (total - 1)) + result.processing_time) / total
            self.performance_stats['avg_processing_time'] = round(new_avg, 3)
            
            # Ajouter à l'historique (garder les 100 derniers)
            self.analysis_history.append({
                'timestamp': datetime.now().isoformat(),
                'processing_time': result.processing_time,
                'confidence_score': result.confidence_score,
                'page_type': result.classification.page_type.value,
                'bot_challenges': len(result.bot_detection.challenges)
            })
            
            if len(self.analysis_history) > 100:
                self.analysis_history = self.analysis_history[-100:]
        
        # Calculer le taux de succès
        successful_analyses = len([h for h in self.analysis_history if 'confidence_score' in h])
        self.performance_stats['success_rate'] = successful_analyses / self.performance_stats['total_analyses']
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance du pipeline."""
        
        if not self.analysis_history:
            return self.performance_stats
        
        # Calculer des métriques supplémentaires
        processing_times = [h['processing_time'] for h in self.analysis_history]
        confidence_scores = [h['confidence_score'] for h in self.analysis_history]
        
        metrics = self.performance_stats.copy()
        metrics.update({
            'min_processing_time': min(processing_times) if processing_times else 0,
            'max_processing_time': max(processing_times) if processing_times else 0,
            'avg_confidence_score': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'recent_analyses': len(self.analysis_history),
            'page_types_distribution': self._get_page_types_distribution(),
            'bot_detection_frequency': self._get_bot_detection_frequency()
        })
        
        return metrics
    
    def _get_page_types_distribution(self) -> Dict[str, int]:
        """Retourne la distribution des types de pages analysées."""
        from collections import Counter
        
        page_types = [h.get('page_type', 'unknown') for h in self.analysis_history]
        return dict(Counter(page_types))
    
    def _get_bot_detection_frequency(self) -> Dict[str, Any]:
        """Retourne les statistiques de détection anti-bot."""
        
        bot_challenges = [h.get('bot_challenges', 0) for h in self.analysis_history]
        
        return {
            'pages_with_challenges': len([c for c in bot_challenges if c > 0]),
            'avg_challenges_per_page': sum(bot_challenges) / len(bot_challenges) if bot_challenges else 0,
            'max_challenges': max(bot_challenges) if bot_challenges else 0
        }
    
    async def analyze_multiple_pages(self, pages_data: List[Dict[str, Any]]) -> List[MLAnalysisResult]:
        """Analyse multiple pages en parallèle."""
        
        tasks = []
        for page_data in pages_data:
            task = self.analyze_page(
                html=page_data.get('html', ''),
                url=page_data.get('url', ''),
                headers=page_data.get('headers', {}),
                response_time=page_data.get('response_time'),
                metadata=page_data.get('metadata', {})
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les exceptions
        valid_results = []
        for result in results:
            if isinstance(result, MLAnalysisResult):
                valid_results.append(result)
            else:
                print(f"Erreur dans l'analyse: {result}")
        
        return valid_results
    
    def create_analysis_report(self, results: List[MLAnalysisResult]) -> Dict[str, Any]:
        """Crée un rapport d'analyse pour plusieurs pages."""
        
        if not results:
            return {'error': 'Aucun résultat à analyser'}
        
        # Statistiques globales
        total_pages = len(results)
        avg_confidence = sum(r.confidence_score for r in results) / total_pages
        avg_processing_time = sum(r.processing_time for r in results) / total_pages
        
        # Distribution des types de contenu
        page_types = [r.classification.page_type.value for r in results]
        page_types_dist = dict(Counter(page_types))
        
        # Qualité du contenu
        quality_scores = [r.content_summary.get('quality', {}).get('overall_score', 0) for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Défis anti-bot
        pages_with_bot_challenges = sum(1 for r in results if len(r.bot_detection.challenges) > 0)
        
        # Recommandations les plus fréquentes
        all_recommendations = []
        for r in results:
            all_recommendations.extend(r.recommendations)
        common_recommendations = dict(Counter(all_recommendations).most_common(10))
        
        report = {
            'summary': {
                'total_pages_analyzed': total_pages,
                'average_confidence_score': round(avg_confidence, 3),
                'average_processing_time': round(avg_processing_time, 3),
                'average_quality_score': round(avg_quality, 1)
            },
            'content_distribution': {
                'page_types': page_types_dist,
                'quality_distribution': {
                    'high_quality': len([q for q in quality_scores if q >= 75]),
                    'medium_quality': len([q for q in quality_scores if 50 <= q < 75]),
                    'low_quality': len([q for q in quality_scores if q < 50])
                }
            },
            'security_analysis': {
                'pages_with_bot_protection': pages_with_bot_challenges,
                'protection_rate': round(pages_with_bot_challenges / total_pages * 100, 1),
                'most_common_challenges': self._get_most_common_challenges(results)
            },
            'recommendations': {
                'most_frequent': common_recommendations,
                'critical_issues': self._identify_critical_issues(results)
            },
            'performance_insights': {
                'fastest_analysis': min(r.processing_time for r in results),
                'slowest_analysis': max(r.processing_time for r in results),
                'most_confident_analysis': max(r.confidence_score for r in results),
                'least_confident_analysis': min(r.confidence_score for r in results)
            }
        }
        
        return report
    
    def _get_most_common_challenges(self, results: List[MLAnalysisResult]) -> Dict[str, int]:
        """Identifie les défis anti-bot les plus fréquents."""
        from collections import Counter
        
        all_challenges = []
        for result in results:
            all_challenges.extend([c.value for c in result.bot_detection.challenges])
        
        return dict(Counter(all_challenges).most_common(5))
    
    def _identify_critical_issues(self, results: List[MLAnalysisResult]) -> List[str]:
        """Identifie les problèmes critiques dans l'analyse."""
        
        critical_issues = []
        
        # Pages avec beaucoup de défis anti-bot
        high_protection_pages = [r for r in results if len(r.bot_detection.challenges) >= 3]
        if len(high_protection_pages) > len(results) * 0.3:
            critical_issues.append(f"{len(high_protection_pages)} pages avec protection anti-bot élevée")
        
        # Pages de très faible qualité
        low_quality_pages = [r for r in results 
                           if r.content_summary.get('quality', {}).get('overall_score', 0) < 30]
        if len(low_quality_pages) > len(results) * 0.2:
            critical_issues.append(f"{len(low_quality_pages)} pages de très faible qualité")
        
        # Confiance globale faible
        low_confidence_pages = [r for r in results if r.confidence_score < 0.5]
        if len(low_confidence_pages) > len(results) * 0.25:
            critical_issues.append(f"{len(low_confidence_pages)} analyses avec faible confiance")
        
        return critical_issues