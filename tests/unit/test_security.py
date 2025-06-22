"""Tests de sécurité pour Scrapinium."""

import pytest
from fastapi.testclient import TestClient
import time
import json


@pytest.mark.integration
@pytest.mark.slow
class TestSecurityBasics:
    """Tests de sécurité de base."""
    
    def test_no_sensitive_info_in_responses(self, client: TestClient):
        """Vérifier qu'aucune info sensible n'est exposée."""
        endpoints = ["/health", "/stats", "/api"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                content = response.text.lower()
                
                # Mots-clés sensibles à ne pas exposer
                sensitive_keywords = [
                    "password", "secret", "key", "token", 
                    "private", "credential", "auth"
                ]
                
                for keyword in sensitive_keywords:
                    assert keyword not in content, f"Sensitive keyword '{keyword}' found in {endpoint}"
    
    def test_cors_headers(self, client: TestClient):
        """Test de la configuration CORS."""
        response = client.options("/health")
        
        # Vérifier que les headers CORS sont présents
        headers = response.headers
        assert "access-control-allow-origin" in headers or response.status_code == 405
    
    def test_sql_injection_protection(self, client: TestClient):
        """Test de protection contre l'injection SQL."""
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "'; SELECT * FROM information_schema.tables; --"
        ]
        
        for payload in malicious_payloads:
            # Test sur différents endpoints qui acceptent des paramètres
            response = client.get(f"/scrape/{payload}")
            # Doit retourner 404 (non trouvé) et non 500 (erreur serveur)
            assert response.status_code in [404, 422], f"Potential SQL injection vulnerability with payload: {payload}"
    
    def test_xss_protection(self, client: TestClient):
        """Test de protection contre XSS."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            # Test avec des données POST
            response = client.post("/scrape", json={
                "url": f"https://example.com/{payload}",
                "output_format": "text"
            })
            
            # L'URL doit être validée et rejetée
            if response.status_code == 200:
                # Si accepté, vérifier que le payload n'est pas reflété tel quel
                content = response.text
                assert payload not in content, f"Potential XSS vulnerability with payload: {payload}"


@pytest.mark.integration
class TestInputValidation:
    """Tests de validation des entrées."""
    
    def test_url_validation(self, client: TestClient):
        """Test de validation des URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "http://",
            "https://",
            ""
        ]
        
        for invalid_url in invalid_urls:
            response = client.post("/scrape", json={
                "url": invalid_url,
                "output_format": "text"
            })
            
            # Doit être rejeté avec une erreur de validation
            assert response.status_code == 422, f"URL should be rejected: {invalid_url}"
    
    def test_output_format_validation(self, client: TestClient):
        """Test de validation des formats de sortie."""
        invalid_formats = [
            "invalid_format",
            "exe",
            "script",
            "<script>",
            "../../../etc/passwd"
        ]
        
        for invalid_format in invalid_formats:
            response = client.post("/scrape", json={
                "url": "https://example.com",
                "output_format": invalid_format
            })
            
            # Doit être rejeté
            assert response.status_code == 422, f"Format should be rejected: {invalid_format}"
    
    def test_custom_instructions_validation(self, client: TestClient):
        """Test de validation des instructions personnalisées."""
        # Instructions très longues
        long_instruction = "A" * 10000
        response = client.post("/scrape", json={
            "url": "https://example.com",
            "output_format": "text",
            "custom_instructions": long_instruction
        })
        
        # Doit soit être accepté avec troncature, soit rejeté
        assert response.status_code in [200, 422]
        
        # Instructions avec caractères dangereux
        dangerous_instructions = [
            "<?php system($_GET['cmd']); ?>",
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --"
        ]
        
        for instruction in dangerous_instructions:
            response = client.post("/scrape", json={
                "url": "https://example.com",
                "output_format": "text",
                "custom_instructions": instruction
            })
            
            # Doit être traité de manière sécurisée
            assert response.status_code in [200, 422]


@pytest.mark.integration
@pytest.mark.performance
class TestDOSProtection:
    """Tests de protection contre les attaques DoS."""
    
    def test_request_size_limits(self, client: TestClient):
        """Test des limites de taille de requête."""
        # Requête très large
        large_data = {
            "url": "https://example.com",
            "output_format": "text",
            "custom_instructions": "X" * 100000  # 100KB
        }
        
        response = client.post("/scrape", json=large_data)
        
        # Doit soit être rejeté, soit traité avec limite
        assert response.status_code in [200, 413, 422]
    
    def test_concurrent_request_handling(self, client: TestClient):
        """Test de gestion des requêtes simultanées."""
        import concurrent.futures
        
        def make_request():
            return client.post("/scrape", json={
                "url": "https://httpbin.org/delay/1",
                "output_format": "text"
            })
        
        # Lancer plusieurs requêtes simultanément
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # Le serveur doit gérer les requêtes sans crasher
        successful_requests = [r for r in results if r.status_code == 200]
        error_requests = [r for r in results if r.status_code >= 500]
        
        # Au moins quelques requêtes doivent réussir
        assert len(successful_requests) > 0
        # Pas d'erreurs serveur critiques
        assert len(error_requests) < len(results) * 0.5  # Moins de 50% d'erreurs


@pytest.mark.integration
class TestDataSanitization:
    """Tests de sanitisation des données."""
    
    def test_response_sanitization(self, client: TestClient):
        """Test de sanitisation des réponses."""
        response = client.get("/health")
        
        if response.status_code == 200:
            # Vérifier que la réponse est du JSON valide
            try:
                data = response.json()
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.fail("Response is not valid JSON")
            
            # Vérifier qu'il n'y a pas de code exécutable
            content = response.text
            dangerous_patterns = [
                "<script>", "</script>",
                "javascript:",
                "data:text/html",
                "eval(",
                "setTimeout(",
                "setInterval("
            ]
            
            for pattern in dangerous_patterns:
                assert pattern not in content, f"Dangerous pattern found: {pattern}"
    
    def test_error_message_sanitization(self, client: TestClient):
        """Test de sanitisation des messages d'erreur."""
        # Provoquer une erreur avec du contenu potentiellement dangereux
        malicious_id = "<script>alert('xss')</script>"
        response = client.get(f"/scrape/{malicious_id}")
        
        assert response.status_code == 404
        
        # Vérifier que le contenu malicieux n'est pas reflété
        content = response.text
        assert "<script>" not in content
        assert "alert(" not in content


@pytest.mark.integration
class TestAuthenticationReadiness:
    """Tests de préparation pour l'authentification future."""
    
    def test_endpoints_without_auth(self, client: TestClient):
        """Test que les endpoints publics fonctionnent sans auth."""
        public_endpoints = [
            "/health",
            "/api",
            "/"  # Interface web
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            # Doit être accessible sans authentification
            assert response.status_code in [200, 404]  # 404 si template manquant
    
    def test_sensitive_endpoints_structure(self, client: TestClient):
        """Test de la structure pour futures restrictions d'accès."""
        # Ces endpoints pourraient nécessiter une auth future
        potentially_protected_endpoints = [
            "/maintenance/gc",
            "/maintenance/optimize", 
            "/maintenance/cleanup",
            "/stats/memory",
            "/stats/cache"
        ]
        
        for endpoint in potentially_protected_endpoints:
            response = client.post(endpoint) if endpoint.startswith("/maintenance") else client.get(endpoint)
            
            # Pour l'instant accessible, mais structure prête pour auth
            assert response.status_code in [200, 405, 500]  # Pas de 403 car pas d'auth encore


@pytest.mark.integration
class TestSecurityHeaders:
    """Tests des headers de sécurité."""
    
    def test_security_headers_presence(self, client: TestClient):
        """Test de la présence des headers de sécurité."""
        response = client.get("/health")
        
        headers = response.headers
        
        # Headers recommandés (peuvent ne pas tous être présents)
        recommended_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY", 
            "x-xss-protection": "1; mode=block"
        }
        
        # Au moins vérifier qu'il n'y a pas d'headers dangereux
        dangerous_headers = ["server", "x-powered-by"]
        
        for header in dangerous_headers:
            if header in headers:
                # Header présent mais ne doit pas révéler d'info sensible
                value = headers[header].lower()
                assert "version" not in value
                assert "python" not in value or "fastapi" not in value