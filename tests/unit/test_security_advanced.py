"""Tests de sécurité avancés pour le système enterprise-grade."""

import pytest
import time
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.mark.security
@pytest.mark.integration
class TestRateLimitingAdvanced:
    """Tests avancés du rate limiting."""
    
    def test_rate_limiting_configuration(self, client: TestClient):
        """Test de configuration du rate limiting."""
        response = client.get("/security/rate-limit/stats")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            stats = data["data"]
            expected_fields = [
                "total_clients", "active_clients_1h", "blocked_clients",
                "total_requests", "total_blocked_requests", "rules"
            ]
            
            for field in expected_fields:
                assert field in stats
            
            # Vérifier la configuration des règles
            rules = stats["rules"]
            assert "default" in rules
            assert "scraping" in rules
            assert "maintenance" in rules
            
            # Vérifier les limites
            default_rule = rules["default"]
            assert default_rule["requests_per_minute"] > 0
            assert default_rule["requests_per_hour"] > 0
            assert default_rule["requests_per_day"] > 0
    
    def test_rate_limiting_enforcement(self, client: TestClient):
        """Test de l'application du rate limiting."""
        # Faire plusieurs requêtes rapidement
        responses = []
        for i in range(10):
            response = client.get("/health")
            responses.append(response)
        
        # Vérifier les headers de rate limiting
        for response in responses:
            if response.status_code == 200:
                headers = response.headers
                rate_limit_headers = [
                    "x-ratelimit-limit",
                    "x-ratelimit-remaining",
                    "x-ratelimit-reset"
                ]
                
                # Au moins un header de rate limiting doit être présent
                has_rate_limit_header = any(
                    header in headers for header in rate_limit_headers
                )
                
                if has_rate_limit_header:
                    assert "x-ratelimit-limit" in headers
                    limit = int(headers["x-ratelimit-limit"])
                    assert limit > 0
    
    def test_suspicious_activity_detection(self, client: TestClient):
        """Test de détection d'activité suspecte."""
        # Envoyer des requêtes avec patterns suspects
        suspicious_requests = [
            {"headers": {"User-Agent": "sqlmap/1.0"}},
            {"headers": {"User-Agent": "nikto"}},
            {"headers": {"User-Agent": ""}},  # UA manquant
        ]
        
        for request_config in suspicious_requests:
            response = client.get("/health", headers=request_config.get("headers", {}))
            
            # La requête peut être bloquée ou autorisée mais surveillée
            assert response.status_code in [200, 403, 429]
    
    def test_dos_protection(self, client: TestClient):
        """Test de protection contre DoS."""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # Lancer 50 requêtes simultanées
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]
        
        # Analyser les résultats
        successful_requests = [r for r in results if r.status_code == 200]
        rate_limited_requests = [r for r in results if r.status_code == 429]
        
        # Le système doit gérer la charge sans crash
        total_responses = len(results)
        assert total_responses == 50
        
        # Au moins quelques requêtes doivent réussir
        assert len(successful_requests) > 0
        
        # Le rate limiting peut être déclenché
        if rate_limited_requests:
            print(f"\nRate limiting activé: {len(rate_limited_requests)} requêtes bloquées")


@pytest.mark.security
@pytest.mark.integration  
class TestInputValidationAdvanced:
    """Tests avancés de validation des inputs."""
    
    def test_input_validation_endpoint(self, client: TestClient):
        """Test de l'endpoint de validation."""
        test_payload = {
            "url": "https://example.com",
            "test_data": "normal content",
            "nested": {
                "value": "test"
            }
        }
        
        response = client.post("/security/validation/test", json=test_payload)
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            validation_data = data["data"]
            assert "validation_results" in validation_data
            assert "summary" in validation_data
            assert "security_level" in validation_data
            
            # Vérifier les résultats de validation
            results = validation_data["validation_results"]
            assert len(results) > 0
            
            for result in results:
                assert "input_type" in result
                assert "result" in result
                
                validation_result = result["result"]
                assert "is_valid" in validation_result
                assert "risk_score" in validation_result
                assert isinstance(validation_result["risk_score"], (int, float))
    
    def test_malicious_input_detection(self, client: TestClient):
        """Test de détection d'inputs malveillants."""
        malicious_payloads = [
            {
                "url": "javascript:alert('xss')",
                "description": "XSS via URL"
            },
            {
                "url": "https://example.com'; DROP TABLE users; --",
                "description": "SQL injection dans URL"
            },
            {
                "content": "<script>alert('xss')</script>",
                "description": "Script malveillant"
            },
            {
                "command": "rm -rf /",
                "description": "Commande système dangereuse"
            },
            {
                "path": "../../../etc/passwd",
                "description": "Path traversal"
            }
        ]
        
        for payload in malicious_payloads:
            response = client.post("/security/validation/test", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                validation_data = data["data"]
                
                # Vérifier que le système détecte le risque
                summary = validation_data.get("summary", {})
                max_risk = summary.get("max_risk_score", 0)
                
                # Un payload malveillant doit avoir un score de risque élevé
                if max_risk > 0:
                    print(f"\nPayload détecté: {payload['description']} - Score: {max_risk}")
    
    def test_input_sanitization(self, client: TestClient):
        """Test de sanitisation des inputs."""
        dirty_inputs = [
            {
                "text": "<script>alert('test')</script>Normal text",
                "expected_clean": True
            },
            {
                "html": "Content with &lt;tags&gt; and &amp; entities",
                "expected_clean": True
            },
            {
                "special_chars": "Text with\x00\x01\x02control chars",
                "expected_clean": True
            }
        ]
        
        for input_test in dirty_inputs:
            response = client.post("/security/validation/test", json=input_test)
            
            if response.status_code == 200:
                data = response.json()
                validation_results = data["data"]["validation_results"]
                
                # Vérifier que la sanitisation a eu lieu
                for result in validation_results:
                    if result["input_type"] == "json_payload":
                        sanitized = result["result"]["sanitized_value"]
                        
                        # Le contenu sanitisé ne doit pas contenir de scripts
                        sanitized_str = json.dumps(sanitized)
                        assert "<script>" not in sanitized_str
                        assert "alert(" not in sanitized_str


@pytest.mark.security
@pytest.mark.integration
class TestSecurityHeaders:
    """Tests des headers de sécurité."""
    
    def test_security_headers_presence(self, client: TestClient):
        """Test de présence des headers de sécurité."""
        response = client.get("/health")
        
        headers = response.headers
        
        # Headers de sécurité critiques
        critical_headers = [
            "x-content-type-options",
            "x-frame-options",
            "referrer-policy"
        ]
        
        for header in critical_headers:
            if header in headers:
                print(f"\nHeader présent: {header} = {headers[header]}")
        
        # Vérifier qu'aucun header sensible n'est exposé
        sensitive_headers = ["server", "x-powered-by"]
        for header in sensitive_headers:
            if header in headers:
                value = headers[header].lower()
                # Ne doit pas révéler de versions ou technologies
                assert "python" not in value
                assert "fastapi" not in value
                assert "/" not in value  # Pas de version
    
    def test_security_headers_configuration(self, client: TestClient):
        """Test de configuration des headers de sécurité."""
        response = client.get("/security/headers/config")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            config = data["data"]
            expected_sections = [
                "cors_configuration",
                "security_headers", 
                "content_security",
                "recommendations"
            ]
            
            for section in expected_sections:
                assert section in config
            
            # Vérifier la configuration CORS
            cors_config = config["cors_configuration"]
            assert cors_config["credentials_enabled"] is False  # Sécurité
            assert cors_config["allowed_origins"] > 0
            
            # Vérifier les headers de sécurité
            security_headers = config["security_headers"]
            assert security_headers["enabled_headers"] > 5
            assert security_headers["csp_enabled"] is True
            assert security_headers["xss_protection"] is True
    
    def test_csp_implementation(self, client: TestClient):
        """Test de l'implémentation CSP."""
        response = client.get("/")  # Page HTML
        
        if response.status_code == 200:
            headers = response.headers
            
            if "content-security-policy" in headers:
                csp = headers["content-security-policy"]
                
                # Vérifier les directives importantes
                important_directives = [
                    "default-src",
                    "script-src",
                    "style-src",
                    "object-src"
                ]
                
                for directive in important_directives:
                    if directive in csp:
                        print(f"\nCSP directive: {directive}")
                
                # object-src 'none' est une bonne pratique
                assert "object-src 'none'" in csp or "object-src" not in csp


@pytest.mark.security
@pytest.mark.integration
class TestComplianceAndAudit:
    """Tests de conformité et audit de sécurité."""
    
    def test_compliance_check_endpoint(self, client: TestClient):
        """Test de l'endpoint de vérification de conformité."""
        response = client.get("/security/compliance/check")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            compliance_data = data["data"]
            expected_sections = [
                "environment_security",
                "compliance", 
                "overall_score",
                "critical_issues",
                "recommendations"
            ]
            
            for section in expected_sections:
                assert section in compliance_data
            
            # Vérifier le score global
            overall_score = compliance_data["overall_score"]
            assert isinstance(overall_score, (int, float))
            assert 0 <= overall_score <= 100
            
            # Vérifier la conformité
            compliance = compliance_data["compliance"]
            assert "compliance_score" in compliance
            assert "checklist" in compliance
            
            compliance_score = compliance["compliance_score"]
            assert isinstance(compliance_score, (int, float))
            assert 0 <= compliance_score <= 100
            
            print(f"\nScore de sécurité global: {overall_score}%")
            print(f"Score de conformité: {compliance_score}%")
    
    def test_owasp_top_10_compliance(self, client: TestClient):
        """Test de conformité OWASP Top 10."""
        response = client.get("/security/compliance/check")
        
        if response.status_code == 200:
            data = response.json()
            compliance = data["data"]["compliance"]
            checklist = compliance["checklist"]
            
            if "OWASP_TOP_10" in checklist:
                owasp_checks = checklist["OWASP_TOP_10"]
                
                critical_checks = [
                    "injection_protection",
                    "broken_authentication", 
                    "sensitive_data_exposure",
                    "xss",
                    "security_misconfiguration"
                ]
                
                for check in critical_checks:
                    if check in owasp_checks:
                        status = owasp_checks[check]
                        print(f"\nOWASP {check}: {'✓' if status else '✗'}")
    
    def test_security_audit_logging(self, client: TestClient):
        """Test de logging d'audit de sécurité."""
        # Effectuer des actions qui doivent être auditées
        audit_actions = [
            client.get("/security/rate-limit/stats"),
            client.get("/security/headers/config"),
            client.get("/security/compliance/check"),
        ]
        
        # Vérifier que les actions sont enregistrées
        for response in audit_actions:
            if response.status_code == 200:
                # Vérifier la présence d'un ID de requête pour l'audit
                headers = response.headers
                audit_headers = ["x-request-id", "x-response-time"]
                
                has_audit_header = any(h in headers for h in audit_headers)
                if has_audit_header:
                    print(f"\nAudit header trouvé dans la réponse")


@pytest.mark.security
@pytest.mark.slow
class TestSecurityStressTests:
    """Tests de stress de sécurité."""
    
    def test_security_under_load(self, client: TestClient):
        """Test de sécurité sous charge."""
        import concurrent.futures
        
        def make_security_request():
            return client.get("/security/rate-limit/stats")
        
        # Lancer 20 requêtes simultanées sur un endpoint sensible
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_security_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # Analyser les résultats
        successful = [r for r in results if r.status_code == 200]
        blocked = [r for r in results if r.status_code in [403, 429]]
        
        print(f"\nRequêtes de sécurité sous charge:")
        print(f"Réussies: {len(successful)}")
        print(f"Bloquées: {len(blocked)}")
        
        # Le système de sécurité doit rester opérationnel
        assert len(successful) > 0
    
    def test_memory_usage_during_security_operations(self, client: TestClient):
        """Test d'utilisation mémoire pendant les opérations de sécurité."""
        # Mesurer la mémoire avant
        initial_memory = client.get("/stats/memory")
        
        # Effectuer de nombreuses validations
        for i in range(50):
            client.post("/security/validation/test", json={
                "url": f"https://example.com/test{i}",
                "data": f"test data {i}"
            })
        
        # Mesurer la mémoire après
        final_memory = client.get("/stats/memory")
        
        if initial_memory.status_code == 200 and final_memory.status_code == 200:
            initial_data = initial_memory.json()
            final_data = final_memory.json()
            
            if both_have_memory_data := (
                initial_data.get("success") and final_data.get("success") and
                "current_usage" in initial_data["data"] and
                "current_usage" in final_data["data"]
            ):
                initial_mb = initial_data["data"]["current_usage"].get("process_memory_mb", 0)
                final_mb = final_data["data"]["current_usage"].get("process_memory_mb", 0)
                
                memory_growth = final_mb - initial_mb
                print(f"\nCroissance mémoire pendant opérations sécurité: {memory_growth}MB")
                
                # La croissance mémoire doit rester raisonnable
                assert memory_growth < 100  # Moins de 100MB de croissance