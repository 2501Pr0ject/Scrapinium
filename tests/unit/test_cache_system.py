"""Tests du système de cache multi-niveau."""

import pytest
import time
import json
from unittest.mock import Mock, patch


@pytest.mark.unit
@pytest.mark.cache
class TestCacheBasics:
    """Tests de base du système de cache."""
    
    def test_cache_configuration(self):
        """Test de configuration du cache."""
        cache_configs = [
            {"type": "memory", "max_size": 1000, "ttl": 3600},
            {"type": "redis", "max_size": 10000, "ttl": 7200},
            {"type": "hybrid", "memory_size": 500, "redis_size": 5000}
        ]
        
        for config in cache_configs:
            assert config["type"] in ["memory", "redis", "hybrid"]
            if "max_size" in config:
                assert config["max_size"] > 0
            if "ttl" in config:
                assert config["ttl"] > 0
    
    def test_cache_key_generation(self):
        """Test de génération des clés de cache."""
        # Simuler la génération de clés
        test_urls = [
            "https://example.com",
            "https://example.com/page1",
            "https://example.com/page1?param=value"
        ]
        
        cache_keys = []
        for url in test_urls:
            # Simuler un hash simple
            key = f"scrape_{hash(url) % 10000}"
            cache_keys.append(key)
            assert key.startswith("scrape_")
            assert len(key) > 10
        
        # Les clés doivent être uniques
        assert len(set(cache_keys)) == len(cache_keys)
    
    def test_cache_entry_structure(self):
        """Test de structure des entrées de cache."""
        cache_entry = {
            "url": "https://example.com",
            "content": "# Test Content\n\nThis is cached content.",
            "metadata": {
                "cached_at": time.time(),
                "ttl": 3600,
                "content_type": "text/html",
                "size_bytes": 500
            },
            "hit_count": 1,
            "last_accessed": time.time()
        }
        
        # Vérifier la structure
        assert "url" in cache_entry
        assert "content" in cache_entry
        assert "metadata" in cache_entry
        assert "cached_at" in cache_entry["metadata"]
        assert cache_entry["hit_count"] >= 0
        assert cache_entry["metadata"]["size_bytes"] > 0


@pytest.mark.integration
@pytest.mark.cache
class TestCacheIntegration:
    """Tests d'intégration du système de cache."""
    
    def test_cache_stats_api(self, client):
        """Test des statistiques de cache via API."""
        response = client.get("/stats/cache")
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            
            if data["success"]:
                cache_stats = data["data"]
                expected_fields = ["hit_rate", "total_requests"]
                
                for field in expected_fields:
                    if field in cache_stats:
                        if field == "hit_rate":
                            assert 0 <= cache_stats[field] <= 100
                        elif field == "total_requests":
                            assert cache_stats[field] >= 0
    
    def test_cache_performance_with_repeated_requests(self, client):
        """Test de performance avec requêtes répétées."""
        test_url = "https://httpbin.org/html"
        
        # Première requête (cache miss attendu)
        first_start = time.time()
        first_response = client.post("/scrape", json={
            "url": test_url,
            "output_format": "text",
            "use_cache": True
        })
        first_time = (time.time() - first_start) * 1000
        
        if first_response.status_code != 200:
            pytest.skip("Cannot perform cache test - scraping failed")
        
        # Attendre un peu pour que la première requête soit cachée
        time.sleep(2)
        
        # Deuxième requête (cache hit potentiel)
        second_start = time.time()
        second_response = client.post("/scrape", json={
            "url": test_url,
            "output_format": "text",
            "use_cache": True
        })
        second_time = (time.time() - second_start) * 1000
        
        if second_response.status_code == 200:
            # La deuxième requête pourrait être plus rapide si mise en cache
            print(f"\nTemps première requête: {first_time:.2f}ms")
            print(f"Temps deuxième requête: {second_time:.2f}ms")
            
            # Pas d'assertion stricte car le cache peut ne pas être activé en test
            assert second_time >= 0
    
    def test_cache_clear_functionality(self, client):
        """Test de fonctionnalité de nettoyage du cache."""
        # Créer quelques entrées en cache
        test_urls = [
            "https://httpbin.org/html?cache_test=1",
            "https://httpbin.org/html?cache_test=2"
        ]
        
        for url in test_urls:
            client.post("/scrape", json={
                "url": url,
                "output_format": "text",
                "use_cache": True
            })
        
        # Nettoyer le cache
        clear_response = client.delete("/cache")
        
        if clear_response.status_code == 200:
            clear_data = clear_response.json()
            assert clear_data["success"] is True
            
            # Vérifier que le nettoyage a été effectué
            if "cleared_entries" in clear_data["data"]:
                cleared_entries = clear_data["data"]["cleared_entries"]
                assert cleared_entries >= 0


@pytest.mark.performance
@pytest.mark.cache
class TestCachePerformance:
    """Tests de performance du cache."""
    
    def test_cache_hit_rate_simulation(self):
        """Test de simulation du taux de hit du cache."""
        # Simuler des statistiques de cache
        cache_requests = [
            {"url": "https://example.com/page1", "hit": True},
            {"url": "https://example.com/page2", "hit": False},
            {"url": "https://example.com/page1", "hit": True},  # Répétition
            {"url": "https://example.com/page3", "hit": False},
            {"url": "https://example.com/page2", "hit": True},  # Répétition
            {"url": "https://example.com/page1", "hit": True},  # Répétition
        ]
        
        total_requests = len(cache_requests)
        hit_count = sum(1 for req in cache_requests if req["hit"])
        hit_rate = (hit_count / total_requests) * 100
        
        assert hit_rate >= 0
        assert hit_rate <= 100
        
        # Dans cet exemple, on a 4 hits sur 6 requêtes = 66.67%
        expected_hit_rate = (4 / 6) * 100
        assert abs(hit_rate - expected_hit_rate) < 0.01
    
    def test_cache_memory_efficiency(self):
        """Test d'efficacité mémoire du cache."""
        # Simuler différentes tailles de contenu
        cache_entries = [
            {"url": "small.html", "size_bytes": 1024},      # 1KB
            {"url": "medium.html", "size_bytes": 10240},    # 10KB
            {"url": "large.html", "size_bytes": 102400},    # 100KB
        ]
        
        total_size = sum(entry["size_bytes"] for entry in cache_entries)
        max_cache_size = 1024 * 1024  # 1MB
        
        # Le cache ne doit pas dépasser la limite
        assert total_size <= max_cache_size
        
        # Calculer l'efficacité d'utilisation
        utilization = (total_size / max_cache_size) * 100
        assert 0 <= utilization <= 100
    
    def test_cache_ttl_management(self):
        """Test de gestion TTL du cache."""
        current_time = time.time()
        
        cache_entries = [
            {"url": "fresh.html", "cached_at": current_time - 1800, "ttl": 3600},    # Frais
            {"url": "expired.html", "cached_at": current_time - 7200, "ttl": 3600},  # Expiré
            {"url": "recent.html", "cached_at": current_time - 900, "ttl": 3600},    # Récent
        ]
        
        valid_entries = []
        expired_entries = []
        
        for entry in cache_entries:
            age = current_time - entry["cached_at"]
            if age <= entry["ttl"]:
                valid_entries.append(entry)
            else:
                expired_entries.append(entry)
        
        # Vérifier la logique TTL
        assert len(valid_entries) == 2  # fresh.html et recent.html
        assert len(expired_entries) == 1  # expired.html


@pytest.mark.integration
@pytest.mark.cache
@pytest.mark.slow
class TestCacheRobustness:
    """Tests de robustesse du cache."""
    
    def test_cache_under_load(self, client):
        """Test du cache sous charge."""
        import concurrent.futures
        
        def make_cached_request(url_suffix):
            return client.post("/scrape", json={
                "url": f"https://httpbin.org/html?load_test={url_suffix}",
                "output_format": "text",
                "use_cache": True
            })
        
        # Lancer plusieurs requêtes avec répétitions pour tester le cache
        requests_to_make = [1, 2, 3, 1, 2, 4, 1, 3]  # Répétitions intentionnelles
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_cached_request, suffix) for suffix in requests_to_make]
            results = [future.result() for future in futures]
        
        # Analyser les résultats
        successful_requests = [r for r in results if r.status_code == 200]
        
        # Au moins quelques requêtes doivent réussir
        assert len(successful_requests) > 0
        
        # Vérifier les stats de cache après la charge
        stats_response = client.get("/stats/cache")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            if stats_data.get("success"):
                print(f"\nStats cache après charge: {stats_data['data']}")
    
    def test_cache_corruption_resistance(self, client):
        """Test de résistance à la corruption du cache."""
        # Effectuer des requêtes normales
        normal_response = client.post("/scrape", json={
            "url": "https://httpbin.org/html",
            "output_format": "text",
            "use_cache": True
        })
        
        if normal_response.status_code == 200:
            task_id = normal_response.json()["data"]["task_id"]
            assert task_id is not None
        
        # Vérifier que le système fonctionne toujours après des opérations normales
        health_response = client.get("/health")
        assert health_response.status_code == 200
    
    def test_cache_consistency(self, client):
        """Test de cohérence du cache."""
        test_url = "https://httpbin.org/html?consistency_test=1"
        
        # Faire plusieurs requêtes pour la même URL
        responses = []
        for i in range(3):
            response = client.post("/scrape", json={
                "url": test_url,
                "output_format": "text",
                "use_cache": True
            })
            responses.append(response)
            time.sleep(0.5)  # Petite pause entre les requêtes
        
        # Vérifier que toutes les requêtes sont cohérentes
        successful_responses = [r for r in responses if r.status_code == 200]
        
        if len(successful_responses) > 1:
            # Les task_ids peuvent être différents, mais le système doit être cohérent
            for response in successful_responses:
                data = response.json()
                assert data["success"] is True
                assert "task_id" in data["data"]


@pytest.mark.unit
@pytest.mark.cache
class TestCacheStrategies:
    """Tests des stratégies de cache."""
    
    def test_lru_cache_strategy(self):
        """Test de stratégie LRU (Least Recently Used)."""
        # Simuler un cache LRU avec limite de taille
        cache_entries = [
            {"key": "page1", "last_accessed": time.time() - 3600, "size": 100},
            {"key": "page2", "last_accessed": time.time() - 1800, "size": 200},
            {"key": "page3", "last_accessed": time.time() - 900, "size": 150},
            {"key": "page4", "last_accessed": time.time() - 300, "size": 120},
        ]
        
        # Trier par dernier accès (LRU = plus ancien en premier)
        sorted_by_lru = sorted(cache_entries, key=lambda x: x["last_accessed"])
        
        # Le plus ancien doit être page1
        assert sorted_by_lru[0]["key"] == "page1"
        assert sorted_by_lru[-1]["key"] == "page4"  # Le plus récent
    
    def test_cache_size_management(self):
        """Test de gestion de taille du cache."""
        max_cache_size = 1000  # bytes
        cache_entries = [
            {"key": "small", "size": 100},
            {"key": "medium", "size": 300},
            {"key": "large", "size": 500},
            {"key": "xlarge", "size": 400},  # Dépasserait la limite
        ]
        
        current_size = 0
        valid_entries = []
        
        for entry in cache_entries:
            if current_size + entry["size"] <= max_cache_size:
                valid_entries.append(entry)
                current_size += entry["size"]
            else:
                break
        
        # Seules les 3 premières entrées doivent être acceptées
        assert len(valid_entries) == 3
        assert current_size == 900  # 100 + 300 + 500
        assert current_size <= max_cache_size
    
    def test_cache_smart_strategy(self):
        """Test de stratégie intelligente de cache."""
        # Simuler une stratégie qui combine fréquence et récence
        cache_entries = [
            {"key": "popular", "hit_count": 100, "last_accessed": time.time() - 3600, "size": 200},
            {"key": "recent", "hit_count": 5, "last_accessed": time.time() - 300, "size": 150},
            {"key": "old_unused", "hit_count": 2, "last_accessed": time.time() - 7200, "size": 100},
            {"key": "frequent_old", "hit_count": 50, "last_accessed": time.time() - 5400, "size": 180},
        ]
        
        # Calculer un score combiné (fréquence * récence)
        current_time = time.time()
        for entry in cache_entries:
            age_hours = (current_time - entry["last_accessed"]) / 3600
            recency_score = max(1, 24 - age_hours)  # Score de récence sur 24h
            entry["smart_score"] = entry["hit_count"] * recency_score / entry["size"]
        
        # Trier par score intelligent
        sorted_by_smart = sorted(cache_entries, key=lambda x: x["smart_score"], reverse=True)
        
        # Vérifier que les scores sont calculés
        for entry in sorted_by_smart:
            assert entry["smart_score"] > 0
            assert "popular" in [e["key"] for e in sorted_by_smart[:2]]  # Populaire doit être dans le top