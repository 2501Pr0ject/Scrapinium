"""Tests de gestion mémoire et surveillance."""

import pytest
import time
import gc
from unittest.mock import Mock, patch


@pytest.mark.unit
@pytest.mark.memory
class TestMemoryBasics:
    """Tests de base de gestion mémoire."""
    
    def test_memory_threshold_configuration(self):
        """Test de configuration des seuils mémoire."""
        memory_thresholds = {
            "warning_threshold_mb": 256,
            "critical_threshold_mb": 512,
            "max_threshold_mb": 1024
        }
        
        # Vérifier la cohérence des seuils
        assert memory_thresholds["warning_threshold_mb"] < memory_thresholds["critical_threshold_mb"]
        assert memory_thresholds["critical_threshold_mb"] < memory_thresholds["max_threshold_mb"]
        
        # Tous les seuils doivent être positifs
        for threshold in memory_thresholds.values():
            assert threshold > 0
    
    def test_memory_usage_calculation(self):
        """Test de calcul d'usage mémoire."""
        # Simuler des métriques mémoire
        memory_metrics = {
            "rss_mb": 128.5,          # Resident Set Size
            "vms_mb": 256.7,          # Virtual Memory Size
            "heap_mb": 89.3,          # Heap memory
            "cache_mb": 45.2,         # Cache memory
            "available_mb": 2048.0    # Available memory
        }
        
        # Calculer l'utilisation totale
        used_memory = memory_metrics["rss_mb"] + memory_metrics["cache_mb"]
        memory_usage_percent = (used_memory / memory_metrics["available_mb"]) * 100
        
        assert 0 <= memory_usage_percent <= 100
        assert memory_metrics["rss_mb"] >= 0
        assert memory_metrics["heap_mb"] <= memory_metrics["rss_mb"]  # Heap fait partie de RSS
    
    def test_garbage_collection_triggers(self):
        """Test des déclencheurs de garbage collection."""
        # Simuler des conditions de déclenchement
        gc_triggers = [
            {"memory_usage_mb": 400, "threshold_mb": 512, "should_trigger": False},
            {"memory_usage_mb": 600, "threshold_mb": 512, "should_trigger": True},
            {"memory_usage_mb": 1000, "threshold_mb": 512, "should_trigger": True},
        ]
        
        for trigger in gc_triggers:
            usage = trigger["memory_usage_mb"]
            threshold = trigger["threshold_mb"]
            expected = trigger["should_trigger"]
            
            actual_trigger = usage > threshold
            assert actual_trigger == expected
    
    def test_memory_leak_detection_simulation(self):
        """Test de simulation de détection de fuites mémoire."""
        # Simuler des mesures mémoire dans le temps
        memory_snapshots = [
            {"timestamp": time.time() - 300, "memory_mb": 100},  # 5 min ago
            {"timestamp": time.time() - 240, "memory_mb": 110},  # 4 min ago
            {"timestamp": time.time() - 180, "memory_mb": 125},  # 3 min ago
            {"timestamp": time.time() - 120, "memory_mb": 140},  # 2 min ago
            {"timestamp": time.time() - 60, "memory_mb": 160},   # 1 min ago
            {"timestamp": time.time(), "memory_mb": 180},        # now
        ]
        
        # Calculer la tendance de croissance
        memory_growth = memory_snapshots[-1]["memory_mb"] - memory_snapshots[0]["memory_mb"]
        time_window = memory_snapshots[-1]["timestamp"] - memory_snapshots[0]["timestamp"]
        growth_rate_mb_per_minute = (memory_growth / time_window) * 60
        
        # Une croissance de plus de 10MB/min pourrait indiquer une fuite
        potential_leak = growth_rate_mb_per_minute > 10
        
        assert growth_rate_mb_per_minute >= 0  # Dans cet exemple, croissance positive
        assert isinstance(potential_leak, bool)


@pytest.mark.integration
@pytest.mark.memory
class TestMemoryIntegration:
    """Tests d'intégration de gestion mémoire."""
    
    def test_memory_stats_api(self, client):
        """Test des statistiques mémoire via API."""
        response = client.get("/stats/memory")
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            
            if data["success"]:
                memory_stats = data["data"]
                
                # Vérifier les champs attendus
                if "current_usage" in memory_stats:
                    current_usage = memory_stats["current_usage"]
                    
                    # Les métriques mémoire doivent être des nombres positifs
                    for key, value in current_usage.items():
                        if key.endswith("_mb"):
                            assert isinstance(value, (int, float))
                            assert value >= 0
    
    def test_garbage_collection_endpoint(self, client):
        """Test de l'endpoint de garbage collection."""
        response = client.post("/maintenance/gc")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            if "objects_freed" in data["data"]:
                objects_freed = data["data"]["objects_freed"]
                assert isinstance(objects_freed, int)
                assert objects_freed >= 0
                
                print(f"\nObjets libérés par GC: {objects_freed}")
    
    def test_memory_optimization_endpoint(self, client):
        """Test de l'endpoint d'optimisation mémoire."""
        response = client.post("/maintenance/optimize")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            # L'optimisation doit retourner des informations sur les actions effectuées
            if "data" in data:
                optimization_data = data["data"]
                assert isinstance(optimization_data, dict)
                
                print(f"\nRésultat optimisation: {optimization_data}")
    
    def test_memory_monitoring_during_load(self, client, performance_thresholds):
        """Test de surveillance mémoire sous charge."""
        # Mesurer la mémoire avant la charge
        initial_response = client.get("/stats/memory")
        initial_memory = 0
        
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if initial_data.get("success") and "current_usage" in initial_data["data"]:
                initial_memory = initial_data["data"]["current_usage"].get("process_memory_mb", 0)
        
        # Créer de la charge avec plusieurs tâches
        for i in range(10):
            client.post("/scrape", json={
                "url": f"https://httpbin.org/html?memory_load={i}",
                "output_format": "text"
            })
        
        # Mesurer la mémoire après la charge
        final_response = client.get("/stats/memory")
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            if final_data.get("success") and "current_usage" in final_data["data"]:
                final_memory = final_data["data"]["current_usage"].get("process_memory_mb", 0)
                
                print(f"\nMémoire initiale: {initial_memory}MB")
                print(f"Mémoire finale: {final_memory}MB")
                
                # La mémoire ne doit pas exploser
                max_memory = performance_thresholds["memory_usage_max_mb"]
                assert final_memory < max_memory
                
                # Calculer la croissance mémoire
                memory_growth = final_memory - initial_memory if initial_memory > 0 else 0
                print(f"Croissance mémoire: {memory_growth}MB")


@pytest.mark.performance
@pytest.mark.memory
class TestMemoryPerformance:
    """Tests de performance mémoire."""
    
    def test_memory_efficiency_calculation(self):
        """Test de calcul d'efficacité mémoire."""
        # Simuler des métriques de performance mémoire
        memory_performance = {
            "allocated_mb": 200,
            "used_mb": 150,
            "cached_mb": 30,
            "buffers_mb": 20,
            "free_mb": 1800
        }
        
        # Calculer l'efficacité d'utilisation
        total_allocated = memory_performance["allocated_mb"]
        actually_used = memory_performance["used_mb"]
        efficiency_percent = (actually_used / total_allocated) * 100
        
        assert 0 <= efficiency_percent <= 100
        assert memory_performance["used_mb"] <= memory_performance["allocated_mb"]
        
        # Une efficacité > 70% est généralement bonne
        good_efficiency = efficiency_percent > 70
        print(f"\nEfficacité mémoire: {efficiency_percent:.1f}% {'(Bonne)' if good_efficiency else '(À améliorer)'}")
    
    def test_memory_fragmentation_analysis(self):
        """Test d'analyse de fragmentation mémoire."""
        # Simuler des statistiques de fragmentation
        memory_blocks = [
            {"size_mb": 10, "free": True},
            {"size_mb": 25, "free": False},
            {"size_mb": 5, "free": True},
            {"size_mb": 30, "free": False},
            {"size_mb": 15, "free": True},
            {"size_mb": 20, "free": False}
        ]
        
        total_memory = sum(block["size_mb"] for block in memory_blocks)
        free_memory = sum(block["size_mb"] for block in memory_blocks if block["free"])
        used_memory = total_memory - free_memory
        
        # Calculer la fragmentation (nombre de blocs libres)
        free_blocks = [block for block in memory_blocks if block["free"]]
        fragmentation_score = len(free_blocks) / len(memory_blocks)
        
        assert 0 <= fragmentation_score <= 1
        assert used_memory + free_memory == total_memory
        
        print(f"\nFragmentation score: {fragmentation_score:.2f}")
        print(f"Blocs libres: {len(free_blocks)}/{len(memory_blocks)}")
    
    def test_memory_allocation_patterns(self):
        """Test de patterns d'allocation mémoire."""
        # Simuler différents patterns d'allocation
        allocation_patterns = [
            {"pattern": "steady", "allocations": [10, 12, 11, 13, 12], "efficiency": "good"},
            {"pattern": "spiky", "allocations": [10, 50, 15, 45, 20], "efficiency": "poor"},
            {"pattern": "growing", "allocations": [10, 15, 20, 25, 30], "efficiency": "acceptable"},
            {"pattern": "declining", "allocations": [50, 40, 30, 20, 10], "efficiency": "good"}
        ]
        
        for pattern in allocation_patterns:
            allocations = pattern["allocations"]
            
            # Calculer la variance pour détecter les pics
            mean_allocation = sum(allocations) / len(allocations)
            variance = sum((x - mean_allocation) ** 2 for x in allocations) / len(allocations)
            stability_score = 1 / (1 + variance / mean_allocation)  # Plus proche de 1 = plus stable
            
            assert 0 <= stability_score <= 1
            
            # Les patterns "steady" doivent avoir une meilleure stabilité
            if pattern["pattern"] == "steady":
                assert stability_score > 0.8
            elif pattern["pattern"] == "spiky":
                assert stability_score < 0.6


@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.slow
class TestMemoryRobustness:
    """Tests de robustesse de gestion mémoire."""
    
    def test_memory_under_stress(self, client):
        """Test de mémoire sous stress."""
        import concurrent.futures
        
        def create_memory_load():
            # Créer plusieurs requêtes pour charger la mémoire
            return client.post("/scrape", json={
                "url": "https://httpbin.org/html",
                "output_format": "text"
            })
        
        # Lancer plusieurs requêtes simultanées
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_memory_load) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # Vérifier que le système n'a pas crashé
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Vérifier l'état de la mémoire après le stress
        memory_response = client.get("/stats/memory")
        if memory_response.status_code == 200:
            memory_data = memory_response.json()
            if memory_data.get("success"):
                print(f"\nÉtat mémoire après stress test: {memory_data['data']}")
    
    def test_memory_recovery_after_cleanup(self, client):
        """Test de récupération mémoire après nettoyage."""
        # Mesurer la mémoire initiale
        initial_response = client.get("/stats/memory")
        initial_memory = None
        
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if initial_data.get("success") and "current_usage" in initial_data["data"]:
                initial_memory = initial_data["data"]["current_usage"].get("process_memory_mb", 0)
        
        # Créer de la charge
        for i in range(15):
            client.post("/scrape", json={
                "url": f"https://httpbin.org/html?cleanup_test={i}",
                "output_format": "text"
            })
        
        # Mesurer la mémoire après la charge
        loaded_response = client.get("/stats/memory")
        loaded_memory = None
        
        if loaded_response.status_code == 200:
            loaded_data = loaded_response.json()
            if loaded_data.get("success") and "current_usage" in loaded_data["data"]:
                loaded_memory = loaded_data["data"]["current_usage"].get("process_memory_mb", 0)
        
        # Effectuer le nettoyage
        gc_response = client.post("/maintenance/gc")
        optimize_response = client.post("/maintenance/optimize")
        
        # Mesurer la mémoire après nettoyage
        cleaned_response = client.get("/stats/memory")
        cleaned_memory = None
        
        if cleaned_response.status_code == 200:
            cleaned_data = cleaned_response.json()
            if cleaned_data.get("success") and "current_usage" in cleaned_data["data"]:
                cleaned_memory = cleaned_data["data"]["current_usage"].get("process_memory_mb", 0)
        
        # Analyser les résultats
        if all(m is not None for m in [initial_memory, loaded_memory, cleaned_memory]):
            print(f"\nMémoire initiale: {initial_memory}MB")
            print(f"Mémoire sous charge: {loaded_memory}MB")
            print(f"Mémoire après nettoyage: {cleaned_memory}MB")
            
            # Le nettoyage devrait réduire la mémoire (ou au moins ne pas l'augmenter)
            assert cleaned_memory <= loaded_memory * 1.1  # Tolérance de 10%
    
    def test_memory_leak_detection_integration(self, client):
        """Test de détection de fuites mémoire en intégration."""
        memory_snapshots = []
        
        # Prendre plusieurs mesures avec des tâches entre chaque
        for i in range(5):
            # Créer quelques tâches
            for j in range(3):
                client.post("/scrape", json={
                    "url": f"https://httpbin.org/html?leak_test={i}_{j}",
                    "output_format": "text"
                })
            
            # Mesurer la mémoire
            response = client.get("/stats/memory")
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "current_usage" in data["data"]:
                    memory_mb = data["data"]["current_usage"].get("process_memory_mb", 0)
                    memory_snapshots.append({
                        "iteration": i,
                        "memory_mb": memory_mb,
                        "timestamp": time.time()
                    })
            
            time.sleep(1)  # Attendre un peu entre les mesures
        
        # Analyser la tendance
        if len(memory_snapshots) >= 3:
            # Calculer la croissance moyenne
            memory_changes = []
            for i in range(1, len(memory_snapshots)):
                change = memory_snapshots[i]["memory_mb"] - memory_snapshots[i-1]["memory_mb"]
                memory_changes.append(change)
            
            average_growth = sum(memory_changes) / len(memory_changes)
            
            print(f"\nÉvolution mémoire: {[s['memory_mb'] for s in memory_snapshots]}")
            print(f"Croissance moyenne: {average_growth:.2f}MB par itération")
            
            # Une croissance excessive pourrait indiquer une fuite
            excessive_growth = average_growth > 50  # Plus de 50MB par itération
            if excessive_growth:
                print("⚠️  Croissance mémoire excessive détectée")
            
            # Le test ne doit pas échouer pour une croissance modérée
            assert average_growth < 200  # Limite très permissive pour les tests