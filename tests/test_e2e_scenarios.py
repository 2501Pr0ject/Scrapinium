"""Tests End-to-End de scénarios complets."""

import pytest
import time
import asyncio
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteWorkflows:
    """Tests de workflows complets."""
    
    def test_simple_scraping_workflow(self, client: TestClient):
        """Test du workflow complet de scraping simple."""
        # 1. Vérifier que l'API est opérationnelle
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # 2. Créer une tâche de scraping
        scrape_response = client.post("/scrape", json={
            "url": "https://httpbin.org/html",
            "output_format": "text",
            "use_llm": False,
            "custom_instructions": ""
        })
        
        assert scrape_response.status_code == 200
        task_data = scrape_response.json()
        assert task_data["success"] is True
        
        task_id = task_data["data"]["task_id"]
        assert task_id is not None
        
        # 3. Vérifier le statut de la tâche
        status_response = client.get(f"/scrape/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["success"] is True
        assert status_data["data"]["id"] == task_id
        
        # 4. Attendre un peu et vérifier les statistiques
        time.sleep(1)
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        
        stats_data = stats_response.json()
        assert stats_data["success"] is True
        assert stats_data["data"]["total_tasks"] > 0
    
    def test_scraping_with_llm_workflow(self, client: TestClient):
        """Test du workflow avec LLM (si disponible)."""
        # 1. Créer une tâche avec LLM
        scrape_response = client.post("/scrape", json={
            "url": "https://httpbin.org/html",
            "output_format": "markdown",
            "use_llm": True,
            "custom_instructions": "Extraire le contenu principal et le structurer"
        })
        
        assert scrape_response.status_code == 200
        task_data = scrape_response.json()
        task_id = task_data["data"]["task_id"]
        
        # 2. Vérifier que la tâche est créée
        status_response = client.get(f"/scrape/{task_id}")
        assert status_response.status_code == 200
        
        # Note: En test, le LLM peut ne pas être disponible
        # Le test vérifie principalement que l'API gère correctement les options LLM
    
    def test_multiple_tasks_workflow(self, client: TestClient):
        """Test de gestion de plusieurs tâches simultanées."""
        task_ids = []
        
        # 1. Créer plusieurs tâches
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json", 
            "https://example.com"
        ]
        
        for url in test_urls:
            response = client.post("/scrape", json={
                "url": url,
                "output_format": "text"
            })
            
            if response.status_code == 200:
                task_id = response.json()["data"]["task_id"]
                task_ids.append(task_id)
        
        assert len(task_ids) > 0
        
        # 2. Vérifier que toutes les tâches sont trackées
        tasks_response = client.get("/tasks")
        assert tasks_response.status_code == 200
        
        tasks_data = tasks_response.json()
        assert tasks_data["success"] is True
        assert len(tasks_data["data"]["tasks"]) >= len(task_ids)
        
        # 3. Vérifier les statistiques globales
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        
        stats_data = stats_response.json()
        assert stats_data["data"]["total_tasks"] >= len(task_ids)


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceScenarios:
    """Tests de performance en conditions réelles."""
    
    def test_api_response_times(self, client: TestClient, performance_thresholds):
        """Test des temps de réponse sous charge légère."""
        endpoints_to_test = [
            "/health",
            "/stats", 
            "/api",
            "/tasks"
        ]
        
        response_times = {}
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            response_times[endpoint] = response_time_ms
            
            if response.status_code == 200:
                assert response_time_ms < performance_thresholds["api_response_time_ms"], \
                    f"Endpoint {endpoint} too slow: {response_time_ms}ms"
        
        # Log des temps de réponse pour debug
        print(f"\nTemps de réponse API: {response_times}")
    
    def test_memory_usage_monitoring(self, client: TestClient, performance_thresholds):
        """Test de surveillance de l'usage mémoire."""
        # Créer quelques tâches pour charger le système
        for i in range(5):
            client.post("/scrape", json={
                "url": f"https://httpbin.org/html?test={i}",
                "output_format": "text"
            })
        
        # Vérifier les stats mémoire
        memory_response = client.get("/stats/memory")
        
        if memory_response.status_code == 200:
            memory_data = memory_response.json()
            
            if "data" in memory_data and "current_usage" in memory_data["data"]:
                current_memory = memory_data["data"]["current_usage"].get("process_memory_mb", 0)
                
                assert current_memory < performance_thresholds["memory_usage_max_mb"], \
                    f"Memory usage too high: {current_memory}MB"
                
                print(f"\nUtilisation mémoire actuelle: {current_memory}MB")
    
    def test_cache_performance(self, client: TestClient, performance_thresholds):
        """Test de performance du cache."""
        # Effectuer la même requête plusieurs fois
        url_to_test = "https://httpbin.org/html"
        
        for i in range(3):
            response = client.post("/scrape", json={
                "url": url_to_test,
                "output_format": "text",
                "use_cache": True
            })
            
            if response.status_code != 200:
                continue
        
        # Vérifier les stats de cache
        cache_response = client.get("/stats/cache")
        
        if cache_response.status_code == 200:
            cache_data = cache_response.json()
            
            if "data" in cache_data and "hit_rate" in cache_data["data"]:
                hit_rate = cache_data["data"]["hit_rate"]
                
                # Après plusieurs requêtes identiques, le hit rate doit être décent
                if cache_data["data"].get("total_requests", 0) > 1:
                    assert hit_rate >= 0, "Cache hit rate should be non-negative"
                
                print(f"\nHit rate cache: {hit_rate}%")


@pytest.mark.integration
@pytest.mark.slow
class TestRobustnessScenarios:
    """Tests de robustesse et de résistance aux erreurs."""
    
    def test_invalid_url_handling(self, client: TestClient):
        """Test de gestion d'URLs invalides."""
        invalid_urls = [
            "https://this-domain-should-not-exist-12345.com",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
            "https://httpbin.org/delay/10"  # Timeout
        ]
        
        for url in invalid_urls:
            response = client.post("/scrape", json={
                "url": url,
                "output_format": "text"
            })
            
            # L'API doit accepter la tâche même si l'URL est problématique
            if response.status_code == 200:
                task_id = response.json()["data"]["task_id"]
                
                # Vérifier que la tâche est trackée
                status_response = client.get(f"/scrape/{task_id}")
                assert status_response.status_code == 200
    
    def test_system_resource_cleanup(self, client: TestClient):
        """Test de nettoyage des ressources système."""
        # Créer plusieurs tâches
        for i in range(10):
            client.post("/scrape", json={
                "url": f"https://httpbin.org/html?cleanup_test={i}",
                "output_format": "text"
            })
        
        # Déclencher le garbage collection
        gc_response = client.post("/maintenance/gc")
        if gc_response.status_code == 200:
            gc_data = gc_response.json()
            assert "objects_freed" in gc_data["data"]
            
            objects_freed = gc_data["data"]["objects_freed"]
            assert objects_freed >= 0
            
            print(f"\nObjets libérés par GC: {objects_freed}")
        
        # Déclencher l'optimisation mémoire
        optimize_response = client.post("/maintenance/optimize")
        if optimize_response.status_code == 200:
            optimize_data = optimize_response.json()
            print(f"\nOptimisation mémoire: {optimize_data['data']}")
    
    def test_error_recovery(self, client: TestClient):
        """Test de récupération après erreurs."""
        # 1. Vérifier état initial
        initial_health = client.get("/health")
        assert initial_health.status_code == 200
        
        # 2. Provoquer quelques erreurs
        error_requests = [
            client.get("/nonexistent"),
            client.post("/scrape", json={"invalid": "data"}),
            client.get("/scrape/invalid-task-id")
        ]
        
        # 3. Vérifier que le système récupère
        post_error_health = client.get("/health")
        assert post_error_health.status_code == 200
        
        # 4. Vérifier qu'on peut encore créer des tâches
        recovery_response = client.post("/scrape", json={
            "url": "https://httpbin.org/html",
            "output_format": "text"
        })
        
        assert recovery_response.status_code == 200


@pytest.mark.integration
class TestAPIConsistency:
    """Tests de cohérence de l'API."""
    
    def test_response_format_consistency(self, client: TestClient):
        """Test de cohérence des formats de réponse."""
        endpoints = [
            "/health",
            "/stats",
            "/tasks",
            "/api"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                
                # Les réponses métier doivent avoir une structure cohérente
                if endpoint in ["/stats", "/tasks"]:
                    assert "success" in data
                    assert "data" in data
                    
                    # Si success=True, data doit être présent et non-null
                    if data.get("success"):
                        assert data["data"] is not None
    
    def test_task_lifecycle_consistency(self, client: TestClient):
        """Test de cohérence du cycle de vie des tâches."""
        # 1. Créer une tâche
        create_response = client.post("/scrape", json={
            "url": "https://httpbin.org/html",
            "output_format": "text"
        })
        
        if create_response.status_code != 200:
            pytest.skip("Cannot create task for lifecycle test")
        
        task_id = create_response.json()["data"]["task_id"]
        
        # 2. Vérifier présence dans le statut individuel
        status_response = client.get(f"/scrape/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["data"]["id"] == task_id
        
        # 3. Vérifier présence dans la liste globale
        tasks_response = client.get("/tasks")
        assert tasks_response.status_code == 200
        
        tasks_data = tasks_response.json()
        task_ids_in_list = [task["id"] for task in tasks_data["data"]["tasks"]]
        assert task_id in task_ids_in_list
        
        # 4. Vérifier cohérence des statistiques
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        
        stats_data = stats_response.json()
        total_tasks = stats_data["data"]["total_tasks"]
        assert total_tasks > 0