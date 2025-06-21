#!/usr/bin/env python3
"""
Test de performance du pool de navigateurs Scrapinium.
Compare les performances avec et sans pool.
"""

import asyncio
import time
import sys
import os
from typing import List

# Ajouter le src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapinium.scraping.browser import quick_scrape, get_browser_stats, browser_manager


async def test_concurrent_scraping(urls: List[str], description: str = ""):
    """Teste le scraping concurrent de plusieurs URLs."""
    print(f"\n🧪 {description}")
    print(f"📊 Test de {len(urls)} URLs en parallèle...")
    
    start_time = time.time()
    
    # Lancer tous les scraping en parallèle
    tasks = [quick_scrape(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyser les résultats
    successful = 0
    failed = 0
    total_execution_time = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed += 1
            print(f"❌ Erreur: {result}")
        else:
            if result.get('status_code') == 200:
                successful += 1
                total_execution_time += result.get('execution_time_ms', 0)
            else:
                failed += 1
    
    avg_execution_time = total_execution_time / successful if successful > 0 else 0
    
    print(f"⏱️  Temps total: {total_time:.2f}s")
    print(f"✅ Succès: {successful}/{len(urls)}")
    print(f"❌ Échecs: {failed}/{len(urls)}")
    print(f"📈 Temps moyen par requête: {avg_execution_time:.0f}ms")
    print(f"🚀 Débit: {successful/total_time:.1f} requêtes/seconde")
    
    return {
        'total_time': total_time,
        'successful': successful,
        'failed': failed,
        'avg_execution_time': avg_execution_time,
        'throughput': successful/total_time if total_time > 0 else 0
    }


async def main():
    """Test principal de performance."""
    print("🏁 Début des tests de performance du pool de navigateurs")
    print("=" * 60)
    
    # URLs de test (sites rapides et fiables)
    test_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
        "https://httpbin.org/ip",
        "https://httpbin.org/uuid",
        "https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l",
        "https://httpbin.org/status/200",
    ]
    
    try:
        # Afficher les stats initiales
        print("\n📊 Statistiques initiales du pool:")
        initial_stats = await get_browser_stats()
        print(f"   • Navigateurs totaux: {initial_stats['browser_pool']['total_browsers']}")
        print(f"   • Navigateurs disponibles: {initial_stats['browser_pool']['available_browsers']}")
        
        # Test 1: Scraping séquentiel (pour comparaison)
        print("\n" + "="*60)
        print("🐌 TEST 1: Scraping SÉQUENTIEL (référence)")
        start_time = time.time()
        sequential_results = []
        for url in test_urls[:4]:  # Limiter à 4 pour le test séquentiel
            result = await quick_scrape(url)
            sequential_results.append(result)
        
        sequential_time = time.time() - start_time
        sequential_successful = sum(1 for r in sequential_results if r.get('status_code') == 200)
        
        print(f"⏱️  Temps total séquentiel: {sequential_time:.2f}s")
        print(f"✅ Succès: {sequential_successful}/{len(test_urls[:4])}")
        print(f"🚀 Débit séquentiel: {sequential_successful/sequential_time:.1f} requêtes/seconde")
        
        # Test 2: Scraping concurrent avec pool
        print("\n" + "="*60)
        concurrent_stats = await test_concurrent_scraping(
            test_urls,
            "🚀 TEST 2: Scraping CONCURRENT avec pool optimisé"
        )
        
        # Test 3: Test de stress (plus d'URLs que de navigateurs)
        stress_urls = test_urls * 2  # 16 URLs pour 3 navigateurs
        print("\n" + "="*60)
        stress_stats = await test_concurrent_scraping(
            stress_urls,
            "💪 TEST 3: Test de STRESS (16 URLs pour 3 navigateurs)"
        )
        
        # Afficher les stats finales du pool
        print("\n📊 Statistiques finales du pool:")
        final_stats = await get_browser_stats()
        browser_pool_stats = final_stats['browser_pool']
        
        print(f"   • Requêtes totales traitées: {browser_pool_stats['total_requests']}")
        print(f"   • Temps d'attente moyen: {browser_pool_stats['avg_wait_time_ms']:.1f}ms")
        print(f"   • Pic d'utilisation: {browser_pool_stats['peak_usage']}/{browser_pool_stats['total_browsers']}")
        print(f"   • Contextes en cache: {final_stats['context_pool']['available_contexts']}")
        
        # Calcul de l'amélioration
        improvement = (concurrent_stats['throughput'] / (sequential_successful/sequential_time)) * 100
        
        print("\n" + "="*60)
        print("📈 RÉSUMÉ DES PERFORMANCES")
        print("="*60)
        print(f"🐌 Séquentiel:     {sequential_successful/sequential_time:.1f} req/s")
        print(f"🚀 Concurrent:     {concurrent_stats['throughput']:.1f} req/s")
        print(f"💪 Stress test:    {stress_stats['throughput']:.1f} req/s")
        print(f"📊 Amélioration:   +{improvement-100:.0f}% vs séquentiel")
        
        if improvement > 200:
            print("🎉 EXCELLENT: Pool de navigateurs très efficace!")
        elif improvement > 150:
            print("✅ BON: Pool de navigateurs efficace")
        else:
            print("⚠️  MOYEN: Pool pourrait être optimisé davantage")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyage
        print("\n🧹 Nettoyage des ressources...")
        await browser_manager.cleanup()
        print("✅ Tests terminés!")


if __name__ == "__main__":
    asyncio.run(main())