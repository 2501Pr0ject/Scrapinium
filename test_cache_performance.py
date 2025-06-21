#!/usr/bin/env python3
"""
Test de performance du cache multi-niveau Scrapinium.
Compare les performances avec et sans cache.
"""

import asyncio
import time
import sys
import os
from typing import List

# Ajouter le src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapinium.cache import get_cache_manager
from scrapinium.cache.models import generate_cache_key, CacheLevel
from scrapinium.models import ScrapingTaskCreate
from scrapinium.models.enums import OutputFormat, LLMProvider
from scrapinium.scraping.service import scraping_service


async def test_cache_performance():
    """Test de performance du cache."""
    print("🧪 Test de performance du cache multi-niveau")
    print("=" * 60)
    
    # URLs de test
    test_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json", 
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
    ]
    
    cache_manager = await get_cache_manager()
    
    try:
        # Vider le cache pour commencer proprement
        await cache_manager.clear()
        print("🧹 Cache vidé pour les tests")
        
        # Test 1: Scraping SANS cache
        print("\n" + "="*50)
        print("🐌 TEST 1: Scraping SANS cache")
        
        tasks_without_cache = []
        for url in test_urls:
            task_data = ScrapingTaskCreate(
                url=url,
                output_format=OutputFormat.PLAIN_TEXT
            )
            tasks_without_cache.append(task_data)
        
        start_time = time.time()
        
        results_without_cache = []
        for task_data in tasks_without_cache:
            result = await scraping_service.scrape_url(
                task_data, 
                use_cache=False  # Désactiver le cache
            )
            results_without_cache.append(result)
        
        time_without_cache = time.time() - start_time
        successful_without_cache = sum(1 for r in results_without_cache if r.get('status') == 'completed')
        
        print(f"⏱️  Temps sans cache: {time_without_cache:.2f}s")
        print(f"✅ Succès: {successful_without_cache}/{len(test_urls)}")
        print(f"🚀 Débit: {successful_without_cache/time_without_cache:.1f} req/s")
        
        # Afficher les stats de cache (devrait être vide)
        stats_empty = await cache_manager.get_stats()
        print(f"📊 Requêtes cache: {stats_empty['total_requests']} (devrait être 0)")
        
        # Test 2: Scraping AVEC cache (premier passage - cache miss)
        print("\n" + "="*50)
        print("🔥 TEST 2: Scraping AVEC cache (cache miss)")
        
        start_time = time.time()
        
        results_cache_miss = []
        for task_data in tasks_without_cache:
            result = await scraping_service.scrape_url(
                task_data,
                use_cache=True  # Activer le cache
            )
            results_cache_miss.append(result)
        
        time_cache_miss = time.time() - start_time
        successful_cache_miss = sum(1 for r in results_cache_miss if r.get('status') == 'completed')
        
        print(f"⏱️  Temps avec cache (miss): {time_cache_miss:.2f}s")
        print(f"✅ Succès: {successful_cache_miss}/{len(test_urls)}")
        print(f"🚀 Débit: {successful_cache_miss/time_cache_miss:.1f} req/s")
        
        # Afficher les stats de cache
        stats_miss = await cache_manager.get_stats()
        print(f"📊 Hit rate: {stats_miss['hit_rate']}%")
        print(f"📊 Entrées en cache: {stats_miss['performance']['entry_count']}")
        
        # Test 3: Scraping AVEC cache (deuxième passage - cache hit)
        print("\n" + "="*50)
        print("⚡ TEST 3: Scraping AVEC cache (cache hit)")
        
        start_time = time.time()
        
        results_cache_hit = []
        for task_data in tasks_without_cache:
            result = await scraping_service.scrape_url(
                task_data,
                use_cache=True  # Activer le cache
            )
            results_cache_hit.append(result)
        
        time_cache_hit = time.time() - start_time
        successful_cache_hit = sum(1 for r in results_cache_hit if r.get('status') == 'completed')
        cache_hits = sum(1 for r in results_cache_hit if r.get('from_cache', False))
        
        print(f"⏱️  Temps avec cache (hit): {time_cache_hit:.2f}s")
        print(f"✅ Succès: {successful_cache_hit}/{len(test_urls)}")
        print(f"🎯 Cache hits: {cache_hits}/{len(test_urls)}")
        print(f"🚀 Débit: {successful_cache_hit/time_cache_hit:.1f} req/s")
        
        # Afficher les stats finales de cache
        stats_final = await cache_manager.get_stats()
        print(f"📊 Hit rate final: {stats_final['hit_rate']}%")
        print(f"📊 Temps de réponse moyen: {stats_final['performance']['avg_response_time_ms']:.2f}ms")
        
        # Test 4: Test de concurrence avec cache
        print("\n" + "="*50)
        print("🏃‍♂️ TEST 4: Scraping CONCURRENT avec cache")
        
        # Créer des tâches mixtes (certaines en cache, d'autres non)
        mixed_urls = test_urls + [
            "https://httpbin.org/status/200",
            "https://httpbin.org/uuid",
        ]
        
        mixed_tasks = []
        for url in mixed_urls:
            task_data = ScrapingTaskCreate(
                url=url,
                output_format=OutputFormat.PLAIN_TEXT
            )
            mixed_tasks.append(task_data)
        
        start_time = time.time()
        
        # Lancer toutes les tâches en parallèle
        concurrent_results = await asyncio.gather(*[
            scraping_service.scrape_url(task_data, use_cache=True)
            for task_data in mixed_tasks
        ])
        
        time_concurrent = time.time() - start_time
        successful_concurrent = sum(1 for r in concurrent_results if r.get('status') == 'completed')
        cache_hits_concurrent = sum(1 for r in concurrent_results if r.get('from_cache', False))
        
        print(f"⏱️  Temps concurrent: {time_concurrent:.2f}s")
        print(f"✅ Succès: {successful_concurrent}/{len(mixed_urls)}")
        print(f"🎯 Cache hits: {cache_hits_concurrent}/{len(mixed_urls)}")
        print(f"🚀 Débit: {successful_concurrent/time_concurrent:.1f} req/s")
        
        # Statistiques de performance finales
        stats_concurrent = await cache_manager.get_stats()
        
        print("\n" + "="*60)
        print("📈 RÉSUMÉ DES PERFORMANCES")
        print("="*60)
        print(f"🐌 Sans cache:           {successful_without_cache/time_without_cache:.1f} req/s")
        print(f"🔥 Avec cache (miss):    {successful_cache_miss/time_cache_miss:.1f} req/s")
        print(f"⚡ Avec cache (hit):     {successful_cache_hit/time_cache_hit:.1f} req/s")
        print(f"🏃‍♂️ Concurrent + cache:   {successful_concurrent/time_concurrent:.1f} req/s")
        
        # Calcul des améliorations
        if time_without_cache > 0:
            improvement_hit = (successful_cache_hit/time_cache_hit) / (successful_without_cache/time_without_cache) * 100
            improvement_concurrent = (successful_concurrent/time_concurrent) / (successful_without_cache/time_without_cache) * 100
            
            print(f"\n🎯 AMÉLIORATIONS:")
            print(f"   Cache hit:       +{improvement_hit-100:.0f}%")
            print(f"   Concurrent:      +{improvement_concurrent-100:.0f}%")
        
        print(f"\n📊 STATISTIQUES CACHE:")
        print(f"   Hit rate:        {stats_concurrent['hit_rate']}%")
        print(f"   Entrées:         {stats_concurrent['performance']['entry_count']}")
        print(f"   Taille totale:   {stats_concurrent['performance']['total_size_bytes']} bytes")
        print(f"   Réponse moy.:    {stats_concurrent['performance']['avg_response_time_ms']:.1f}ms")
        
        # Détails par niveau de cache
        if 'memory_cache' in stats_concurrent:
            memory_stats = stats_concurrent['memory_cache']
            print(f"\n💾 CACHE MÉMOIRE:")
            print(f"   Utilisation:     {memory_stats.get('utilization', 0)*100:.1f}%")
            print(f"   Entrées:         {memory_stats.get('entry_count', 0)}")
            print(f"   Hits totaux:     {memory_stats.get('total_hits', 0)}")
        
        if 'redis_cache' in stats_concurrent and stats_concurrent['redis_cache'].get('connected'):
            redis_stats = stats_concurrent['redis_cache']
            print(f"\n🔴 CACHE REDIS:")
            print(f"   Connecté:        ✅")
            print(f"   Entrées:         {redis_stats.get('entry_count', 0)}")
            print(f"   Mémoire:         {redis_stats.get('memory_used_human', 'N/A')}")
        else:
            print(f"\n🔴 CACHE REDIS:      ❌ Non disponible")
        
        if improvement_hit > 300:
            print("\n🎉 EXCELLENT: Cache extrêmement efficace!")
        elif improvement_hit > 200:
            print("\n✅ TRÈS BON: Cache très efficace!")
        elif improvement_hit > 150:
            print("\n👍 BON: Cache efficace")
        else:
            print("\n⚠️  MOYEN: Cache pourrait être optimisé")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyage
        print("\n🧹 Nettoyage des ressources...")
        await cache_manager.cleanup()
        await scraping_service.cleanup()
        print("✅ Tests de cache terminés!")


if __name__ == "__main__":
    asyncio.run(test_cache_performance())