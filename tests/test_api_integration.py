"""Tests d'intégration API REST."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.integration
class TestAPIHealthAndStatus:
    """Tests de santé et statut de l'API."""
    
    def test_health_check(self, client: TestClient):
        """Test du endpoint de health check."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "api" in data
        assert data["api"] == "healthy"
    
    def test_api_info(self, client: TestClient):
        """Test des informations API."""
        response = client.get("/api")
        assert response.status_code == 200
        
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_stats_endpoint(self, client: TestClient):
        """Test du endpoint de statistiques."""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        stats = data["data"]
        required_fields = [
            "total_tasks", "active_tasks", "completed_tasks", 
            "failed_tasks", "success_rate"
        ]
        for field in required_fields:
            assert field in stats


@pytest.mark.api
@pytest.mark.integration
class TestScrapeEndpoints:
    """Tests des endpoints de scraping."""
    
    def test_scrape_endpoint_validation(self, client: TestClient):
        """Test de validation des paramètres de scraping."""
        # Test sans URL
        response = client.post("/scrape", json={})
        assert response.status_code == 422  # Validation error
        
        # Test avec URL invalide
        response = client.post("/scrape", json={"url": "not-a-url"})
        assert response.status_code == 422
        
        # Test avec URL valide mais minimal
        response = client.post("/scrape", json={
            "url": "https://example.com",
            "output_format": "text"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data["data"]
    
    def test_task_status_endpoint(self, client: TestClient):
        """Test du endpoint de statut de tâche."""
        # Test avec ID inexistant
        response = client.get("/scrape/nonexistent-id")
        assert response.status_code == 404
        
        # Test après création d'une tâche
        create_response = client.post("/scrape", json={
            "url": "https://example.com",
            "output_format": "text"
        })
        task_id = create_response.json()["data"]["task_id"]
        
        # Vérifier le statut
        status_response = client.get(f"/scrape/{task_id}")
        assert status_response.status_code == 200
        
        data = status_response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["id"] == task_id
    
    def test_tasks_list_endpoint(self, client: TestClient):
        """Test du endpoint de liste des tâches."""
        response = client.get("/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "tasks" in data["data"]
        assert "total" in data["data"]
        assert "active" in data["data"]
        assert "completed" in data["data"]
        
        # Test avec limite
        response = client.get("/tasks?limit=5")
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.cache
class TestCacheEndpoints:
    """Tests des endpoints de cache."""
    
    def test_cache_stats_endpoint(self, client: TestClient):
        """Test des statistiques de cache."""
        response = client.get("/stats/cache")
        
        # Le cache peut ne pas être disponible en test
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            cache_data = data["data"]
            expected_fields = ["hit_rate", "total_requests"]
            for field in expected_fields:
                assert field in cache_data
    
    def test_cache_clear_endpoint(self, client: TestClient):
        """Test du nettoyage de cache."""
        response = client.delete("/cache")
        
        # Le cache peut ne pas être disponible en test
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.memory
class TestMemoryEndpoints:
    """Tests des endpoints de mémoire."""
    
    def test_memory_stats_endpoint(self, client: TestClient):
        """Test des statistiques mémoire."""
        response = client.get("/stats/memory")
        
        # La surveillance mémoire peut ne pas être disponible
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            memory_data = data["data"]
            assert "current_usage" in memory_data
    
    def test_maintenance_gc_endpoint(self, client: TestClient):
        """Test du garbage collection forcé."""
        response = client.post("/maintenance/gc")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "objects_freed" in data["data"]
    
    def test_maintenance_optimize_endpoint(self, client: TestClient):
        """Test de l'optimisation mémoire."""
        response = client.post("/maintenance/optimize")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.performance
class TestAPIPerformance:
    """Tests de performance API."""
    
    def test_health_check_response_time(self, client: TestClient, performance_thresholds):
        """Test du temps de réponse du health check."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        response_time = (time.time() - start_time) * 1000  # en ms
        
        assert response.status_code == 200
        assert response_time < performance_thresholds["api_response_time_ms"]
    
    def test_stats_endpoint_response_time(self, client: TestClient, performance_thresholds):
        """Test du temps de réponse des statistiques."""
        import time
        
        start_time = time.time()
        response = client.get("/stats")
        response_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < performance_thresholds["api_response_time_ms"]
    
    def test_concurrent_requests(self, client: TestClient):
        """Test de requêtes concurrentes."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/health")
        
        # Exécuter 10 requêtes simultanées
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # Toutes les requêtes doivent réussir
        for response in results:
            assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestErrorHandling:
    """Tests de gestion d'erreurs."""
    
    def test_404_handling(self, client: TestClient):
        """Test de gestion des erreurs 404."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_invalid_json_handling(self, client: TestClient):
        """Test de gestion JSON invalide."""
        response = client.post(
            "/scrape",
            data="invalid-json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_malformed_request_handling(self, client: TestClient):
        """Test de gestion de requêtes malformées."""
        # Test avec paramètres manquants
        response = client.post("/scrape", json={"invalid": "data"})
        assert response.status_code == 422
        
        # Test avec types incorrects
        response = client.post("/scrape", json={
            "url": 123,  # Devrait être string
            "output_format": "text"
        })
        assert response.status_code == 422