"""Détecteur anti-bot intelligent pour Scrapinium."""

import random
import time
import hashlib
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import re

class BotChallenge(Enum):
    """Types de défis anti-bot détectés."""
    CLOUDFLARE = "cloudflare"
    RECAPTCHA = "recaptcha"
    RATE_LIMITING = "rate_limiting"
    JS_CHALLENGE = "js_challenge"
    CAPTCHA = "captcha"
    FINGERPRINTING = "fingerprinting"
    UNKNOWN = "unknown"

class EvasionStrategy(Enum):
    """Stratégies d'évasion disponibles."""
    STEALTH_MODE = "stealth_mode"      # Mode furtif maximum
    HUMAN_SIMULATION = "human_simulation"  # Simulation comportement humain
    ROTATION = "rotation"              # Rotation IP/User-Agent
    DELAY_RANDOMIZATION = "delay_randomization"  # Délais aléatoires
    BROWSER_PROFILE = "browser_profile"  # Profils navigateur réalistes

@dataclass
class DetectionResult:
    """Résultat de détection anti-bot."""
    challenges: List[BotChallenge]
    confidence: float
    strategies: List[EvasionStrategy]
    parameters: Dict[str, Any]
    warnings: List[str]

class AntibotDetector:
    """Détecteur intelligent anti-bot avec stratégies d'évasion."""
    
    def __init__(self):
        # Signatures de détection anti-bot
        self.bot_signatures = {
            BotChallenge.CLOUDFLARE: [
                r'cloudflare', r'cf-ray', r'__cf_bm', r'cf_clearance',
                r'checking your browser', r'security check', r'ray id'
            ],
            BotChallenge.RECAPTCHA: [
                r'recaptcha', r'g-recaptcha', r'grecaptcha',
                r'captcha-delivery', r'recaptcha-v2'
            ],
            BotChallenge.RATE_LIMITING: [
                r'rate limit', r'too many requests', r'429',
                r'slow down', r'temporarily blocked'
            ],
            BotChallenge.JS_CHALLENGE: [
                r'enable javascript', r'javascript required',
                r'js_challenge', r'jschl_vc', r'jschl_answer'
            ],
            BotChallenge.CAPTCHA: [
                r'captcha', r'verify you are human', r'prove you are not a robot',
                r'security verification', r'human verification'
            ],
            BotChallenge.FINGERPRINTING: [
                r'canvas fingerprint', r'webgl fingerprint', r'audio fingerprint',
                r'device fingerprint', r'browser fingerprint'
            ]
        }
        
        # User-Agents réalistes par OS/navigateur
        self.realistic_user_agents = {
            'chrome_windows': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
            ],
            'firefox_windows': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0'  
            ],
            'chrome_mac': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ],
            'safari_mac': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15'
            ]
        }
        
        # Headers cohérents par navigateur
        self.browser_headers = {
            'chrome': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            },
            'firefox': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        }
        
        # Plages de délais réalistes (en secondes)
        self.delay_ranges = {
            'reading': (2, 8),      # Temps de lecture
            'clicking': (0.5, 2),   # Temps avant clic
            'typing': (0.1, 0.3),   # Délai entre caractères
            'page_load': (1, 3),    # Attente chargement page
            'scrolling': (0.5, 1.5) # Délai scroll
        }
    
    def analyze_page(self, html: str, headers: Dict[str, str], url: str, 
                    response_time: float = None) -> DetectionResult:
        """Analyse une page pour détecter les défis anti-bot."""
        
        challenges = []
        confidence_scores = {}
        warnings = []
        
        # Analyser le contenu HTML
        html_lower = html.lower()
        
        for challenge_type, signatures in self.bot_signatures.items():
            score = 0
            matches = []
            
            for signature in signatures:
                if re.search(signature, html_lower):
                    score += 1
                    matches.append(signature)
            
            if score > 0:
                challenges.append(challenge_type)
                confidence_scores[challenge_type] = min(1.0, score / len(signatures))
                
                if score >= 2:
                    warnings.append(f"Défi {challenge_type.value} détecté avec confiance élevée")
        
        # Analyser les headers de réponse
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        
        # Détecter Cloudflare
        if any(header.startswith('cf-') for header in headers_lower.keys()):
            if BotChallenge.CLOUDFLARE not in challenges:
                challenges.append(BotChallenge.CLOUDFLARE)
            confidence_scores[BotChallenge.CLOUDFLARE] = max(
                confidence_scores.get(BotChallenge.CLOUDFLARE, 0), 0.8
            )
        
        # Détecter rate limiting par code de statut ou headers
        if 'retry-after' in headers_lower or 'x-ratelimit' in str(headers_lower):
            challenges.append(BotChallenge.RATE_LIMITING)
            confidence_scores[BotChallenge.RATE_LIMITING] = 0.9
            warnings.append("Rate limiting détecté - ralentir les requêtes")
        
        # Analyser le temps de réponse
        if response_time and response_time > 10:
            warnings.append(f"Temps de réponse élevé ({response_time:.1f}s) - possible détection bot")
        
        # Calculer la confiance globale
        global_confidence = max(confidence_scores.values()) if confidence_scores else 0.0
        
        # Déterminer les stratégies d'évasion
        strategies = self._get_evasion_strategies(challenges, confidence_scores)
        
        # Paramètres pour les stratégies
        parameters = self._generate_evasion_parameters(challenges, url)
        
        return DetectionResult(
            challenges=challenges,
            confidence=global_confidence,
            strategies=strategies,
            parameters=parameters,
            warnings=warnings
        )
    
    def _get_evasion_strategies(self, challenges: List[BotChallenge], 
                              confidence_scores: Dict[BotChallenge, float]) -> List[EvasionStrategy]:
        """Détermine les stratégies d'évasion appropriées."""
        strategies = []
        
        # Stratégies par type de défi
        if BotChallenge.CLOUDFLARE in challenges:
            strategies.extend([EvasionStrategy.STEALTH_MODE, EvasionStrategy.DELAY_RANDOMIZATION])
        
        if BotChallenge.RATE_LIMITING in challenges:
            strategies.extend([EvasionStrategy.DELAY_RANDOMIZATION, EvasionStrategy.ROTATION])
        
        if BotChallenge.FINGERPRINTING in challenges:
            strategies.extend([EvasionStrategy.BROWSER_PROFILE, EvasionStrategy.ROTATION])
        
        if BotChallenge.JS_CHALLENGE in challenges:
            strategies.append(EvasionStrategy.HUMAN_SIMULATION)
        
        # Stratégies par niveau de confiance
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0
        
        if max_confidence > 0.8:
            strategies.append(EvasionStrategy.STEALTH_MODE)
        elif max_confidence > 0.5:
            strategies.append(EvasionStrategy.HUMAN_SIMULATION)
        
        # Toujours recommander la simulation humaine si des défis sont détectés
        if challenges and EvasionStrategy.HUMAN_SIMULATION not in strategies:
            strategies.append(EvasionStrategy.HUMAN_SIMULATION)
        
        return list(set(strategies))  # Supprimer les doublons
    
    def _generate_evasion_parameters(self, challenges: List[BotChallenge], url: str) -> Dict[str, Any]:
        """Génère les paramètres pour les stratégies d'évasion."""
        domain = urlparse(url).netloc
        
        # Générer un profil navigateur cohérent
        browser_profile = self._generate_browser_profile()
        
        # Délais adaptatifs basés sur les défis détectés
        base_delay = 1.0
        if BotChallenge.CLOUDFLARE in challenges:
            base_delay *= 2.0
        if BotChallenge.RATE_LIMITING in challenges:
            base_delay *= 3.0
        
        parameters = {
            'browser_profile': browser_profile,
            'delays': {
                'base_delay': base_delay,
                'random_factor': random.uniform(0.5, 1.5),
                'page_delays': {
                    'min': base_delay * 0.5,
                    'max': base_delay * 2.0
                }
            },
            'rotation': {
                'user_agent_pool': self._get_user_agent_pool(),
                'header_variations': self._get_header_variations(browser_profile['browser']),
                'proxy_recommendation': len(challenges) > 2
            },
            'stealth': {
                'disable_images': BotChallenge.FINGERPRINTING in challenges,
                'disable_javascript': False,  # Dangereux pour les JS challenges
                'randomize_viewport': True,
                'simulate_mouse_movement': True
            }
        }
        
        return parameters
    
    def _generate_browser_profile(self) -> Dict[str, Any]:
        """Génère un profil navigateur cohérent et réaliste."""
        # Choisir aléatoirement un type de navigateur
        browser_types = list(self.realistic_user_agents.keys())
        browser_type = random.choice(browser_types)
        
        browser_name = browser_type.split('_')[0]
        os_name = browser_type.split('_')[1] if '_' in browser_type else 'windows'
        
        user_agent = random.choice(self.realistic_user_agents[browser_type])
        
        # Générer des propriétés cohérentes
        profile = {
            'browser': browser_name,
            'os': os_name,
            'user_agent': user_agent,
            'headers': self.browser_headers.get(browser_name, self.browser_headers['chrome']).copy(),
            'viewport': self._generate_realistic_viewport(),
            'timezone': self._generate_realistic_timezone(),
            'language': 'fr-FR'
        }
        
        # Ajouter le User-Agent aux headers
        profile['headers']['User-Agent'] = user_agent
        
        return profile
    
    def _generate_realistic_viewport(self) -> Dict[str, int]:
        """Génère une taille de viewport réaliste."""
        common_resolutions = [
            (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
            (1280, 720), (1600, 900), (2560, 1440), (1920, 1200)
        ]
        
        width, height = random.choice(common_resolutions)
        
        return {
            'width': width,
            'height': height - random.randint(100, 200)  # Soustraire la barre du navigateur
        }
    
    def _generate_realistic_timezone(self) -> str:
        """Génère un fuseau horaire réaliste."""
        timezones = [
            'Europe/Paris', 'Europe/London', 'America/New_York',
            'America/Los_Angeles', 'Europe/Berlin', 'Europe/Madrid'
        ]
        return random.choice(timezones)
    
    def _get_user_agent_pool(self) -> List[str]:
        """Retourne un pool d'User-Agents pour la rotation."""
        pool = []
        for ua_list in self.realistic_user_agents.values():
            pool.extend(ua_list)
        return pool
    
    def _get_header_variations(self, browser: str) -> List[Dict[str, str]]:
        """Génère des variations de headers pour un navigateur."""
        base_headers = self.browser_headers.get(browser, self.browser_headers['chrome'])
        variations = []
        
        # Créer quelques variations subtiles
        for _ in range(3):
            headers = base_headers.copy()
            
            # Varier Accept-Language
            if random.random() < 0.3:
                headers['Accept-Language'] = 'en-US,en;q=0.9,fr;q=0.8'
            
            # Varier DNT header (parfois présent, parfois non)
            if random.random() < 0.5:
                headers['DNT'] = '1'
            
            variations.append(headers)
        
        return variations
    
    def get_recommended_delays(self, challenges: List[BotChallenge]) -> Dict[str, Tuple[float, float]]:
        """Retourne des délais recommandés basés sur les défis détectés."""
        base_multiplier = 1.0
        
        # Augmenter les délais selon les défis
        if BotChallenge.CLOUDFLARE in challenges:
            base_multiplier *= 2.0
        if BotChallenge.RATE_LIMITING in challenges:
            base_multiplier *= 3.0
        if BotChallenge.FINGERPRINTING in challenges:
            base_multiplier *= 1.5
        
        recommended_delays = {}
        for action, (min_delay, max_delay) in self.delay_ranges.items():
            recommended_delays[action] = (
                min_delay * base_multiplier,
                max_delay * base_multiplier
            )
        
        return recommended_delays
    
    def generate_human_like_delay(self, action: str, challenges: List[BotChallenge] = None) -> float:
        """Génère un délai qui simule le comportement humain."""
        challenges = challenges or []
        delays = self.get_recommended_delays(challenges)
        
        if action in delays:
            min_delay, max_delay = delays[action]
        else:
            min_delay, max_delay = (0.5, 2.0)
        
        # Distribution plus réaliste (pas uniforme)
        # Utiliser une distribution beta pour simuler les temps de réaction humains
        import numpy as np
        
        # Paramètres pour distribution beta (forme de cloche asymétrique)
        alpha, beta = 2, 5
        random_factor = np.random.beta(alpha, beta)
        
        delay = min_delay + (max_delay - min_delay) * random_factor
        
        # Ajouter une petite variation aléatoire
        jitter = random.uniform(-0.1, 0.1) * delay
        final_delay = max(0.1, delay + jitter)
        
        return final_delay
    
    def create_stealth_configuration(self, detection_result: DetectionResult) -> Dict[str, Any]:
        """Crée une configuration complète pour le mode furtif."""
        params = detection_result.parameters
        
        stealth_config = {
            # Configuration navigateur
            'user_agent': params['browser_profile']['user_agent'],
            'headers': params['browser_profile']['headers'],
            'viewport': params['browser_profile']['viewport'],
            
            # Configuration délais
            'delays': params['delays'],
            
            # Configuration comportementale
            'behavior': {
                'simulate_mouse': True,
                'random_scrolling': True,
                'random_clicks': False,  # Éviter les clics non nécessaires
                'typing_simulation': True
            },
            
            # Configuration technique
            'technical': {
                'disable_images': params['stealth']['disable_images'],
                'disable_webrtc': True,
                'spoof_canvas': True,
                'spoof_webgl': True,
                'randomize_plugins': True
            },
            
            # Recommandations réseau
            'network': {
                'use_proxy': params['rotation']['proxy_recommendation'],
                'rotate_session': len(detection_result.challenges) > 1,
                'max_concurrent_requests': 1 if BotChallenge.RATE_LIMITING in detection_result.challenges else 3
            }
        }
        
        return stealth_config