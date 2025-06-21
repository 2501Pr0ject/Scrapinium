#!/usr/bin/env python3
"""Test simplifié du cache."""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapinium.cache import get_cache_manager
from scrapinium.cache.models import generate_cache_key


async def test_cache_basic():
    """Test basique du cache."""
    print("🧪 Test basique du cache multi-niveau")
    print("=" * 50)
    
    cache_manager = await get_cache_manager()
    
    try:
        # Test 1: Set/Get basique
        print("\n1. Test Set/Get basique")
        key = "test_key"
        value = {"message": "Hello Cache!", "timestamp": time.time()}
        
        # Mettre en cache
        success = await cache_manager.set(key, value, ttl=60)
        print(f"   Set: {'✅' if success else '❌'}")
        
        # Récupérer du cache
        cached_value = await cache_manager.get(key)
        print(f"   Get: {'✅' if cached_value == value else '❌'}")
        
        # Test 2: Cache miss
        print("\n2. Test Cache miss")
        missing_value = await cache_manager.get("non_existent_key")
        print(f"   Miss: {'✅' if missing_value is None else '❌'}")
        
        # Test 3: Génération de clés
        print("\n3. Test génération de clés")
        url = "https://example.com"
        params = {"format": "json", "llm": "ollama"}
        cache_key = generate_cache_key(url, params)
        print(f"   Clé générée: {cache_key[:16]}...")
        
        # Test 4: Statistiques
        print("\n4. Test statistiques")
        stats = await cache_manager.get_stats()
        print(f"   Hit rate: {stats['hit_rate']}%")
        print(f"   Entrées: {stats['performance']['entry_count']}")
        print(f"   Requêtes: {stats['total_requests']}")
        
        # Test 5: Performance
        print("\n5. Test performance")
        test_data = {"large_data": "x" * 1000}  # 1KB de données
        
        # 10 écritures/lectures
        start_time = time.time()
        for i in range(10):
            await cache_manager.set(f"perf_test_{i}", test_data, ttl=60)
            result = await cache_manager.get(f"perf_test_{i}")
        
        elapsed = time.time() - start_time
        print(f"   10 set/get: {elapsed*1000:.1f}ms")
        print(f"   Débit: {20/elapsed:.1f} ops/sec")
        
        # Statistiques finales
        final_stats = await cache_manager.get_stats()
        print(f"\n📊 Statistiques finales:")
        print(f"   Hit rate: {final_stats['hit_rate']}%")
        print(f"   Temps réponse: {final_stats['performance']['avg_response_time_ms']:.1f}ms")
        print(f"   Entrées total: {final_stats['performance']['entry_count']}")
        
        if 'memory_cache' in final_stats:
            memory_stats = final_stats['memory_cache']
            print(f"   Cache mémoire: {memory_stats.get('entry_count', 0)} entrées")
        
        if 'redis_cache' in final_stats:
            redis_stats = final_stats['redis_cache']
            if redis_stats.get('connected'):
                print(f"   Cache Redis: ✅ {redis_stats.get('entry_count', 0)} entrées")
            else:
                print(f"   Cache Redis: ❌ Non disponible")
        
        print("\n✅ Test basique réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await cache_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_cache_basic())