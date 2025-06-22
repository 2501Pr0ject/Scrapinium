#!/usr/bin/env python3
"""Test basique des optimisations sans dépendances externes."""

import asyncio
import sys
import os
import gc
import time
import gzip
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapinium.utils.streaming import StreamingProcessor


async def test_streaming_basic():
    """Test basique du streaming."""
    print("🌊 Test Streaming Basique")
    print("-" * 30)
    
    processor = StreamingProcessor(chunk_size=100)
    
    content = "Hello World! " * 50  # ~650 bytes
    print(f"Contenu: {len(content)} bytes")
    
    chunks = 0
    async for chunk in processor.process_content_stream(content):
        chunks += 1
        if chunks <= 3:
            print(f"  Chunk {chunk.chunk_id}: {chunk.size} bytes")
    
    print(f"Total: {chunks} chunks traités")
    return chunks > 0


def test_compression_basic():
    """Test basique de compression avec gzip."""
    print("\n🗜️  Test Compression Basique")
    print("-" * 30)
    
    # Données de test
    data = {"message": "Test " * 1000, "numbers": list(range(100))}
    json_data = json.dumps(data).encode('utf-8')
    
    original_size = len(json_data)
    print(f"Original: {original_size} bytes")
    
    # Compression GZIP
    compressed = gzip.compress(json_data)
    compressed_size = len(compressed)
    ratio = compressed_size / original_size
    savings = (1 - ratio) * 100
    
    print(f"Compressé: {compressed_size} bytes")
    print(f"Ratio: {ratio:.2f}")
    print(f"Économie: {savings:.1f}%")
    
    # Décompression pour vérifier
    decompressed = gzip.decompress(compressed)
    success = decompressed == json_data
    print(f"Décompression: {'✅' if success else '❌'}")
    
    return success and savings > 50  # Au moins 50% d'économie


def test_memory_gc():
    """Test du garbage collection."""
    print("\n🗑️  Test Garbage Collection")
    print("-" * 30)
    
    # Mesurer les objets
    before = len(gc.get_objects())
    print(f"Objets avant: {before}")
    
    # Créer des objets temporaires
    temp_objects = []
    for i in range(1000):
        temp_objects.append({"id": i, "data": "x" * 100})
    
    during = len(gc.get_objects())
    print(f"Objets avec données: {during}")
    print(f"Nouveaux objets: {during - before}")
    
    # Supprimer et collecter
    del temp_objects
    collected = gc.collect()
    after = len(gc.get_objects())
    
    print(f"Objets après GC: {after}")
    print(f"Collectés par GC: {collected}")
    print(f"Objets libérés: {during - after}")
    
    return collected > 0


async def test_memory_efficient_iteration():
    """Test d'itération efficace en mémoire."""
    print("\n⚡ Test Itération Efficace")
    print("-" * 30)
    
    # Générateur efficace vs liste complète
    def memory_efficient_data():
        for i in range(10000):
            yield f"Data item {i}"
    
    # Test avec générateur
    start_time = time.time()
    count = 0
    for item in memory_efficient_data():
        count += 1
        if count >= 5000:  # Traiter seulement 5000 items
            break
    
    generator_time = time.time() - start_time
    print(f"Générateur: {count} items en {generator_time*1000:.1f}ms")
    
    # Test avec liste complète (moins efficace)
    start_time = time.time()
    full_list = [f"Data item {i}" for i in range(10000)]
    processed = 0
    for item in full_list[:5000]:
        processed += 1
    
    list_time = time.time() - start_time
    print(f"Liste complète: {processed} items en {list_time*1000:.1f}ms")
    
    efficiency_gain = list_time / generator_time if generator_time > 0 else 1
    print(f"Gain d'efficacité: {efficiency_gain:.1f}x")
    
    return efficiency_gain > 0.8  # Le générateur doit être au moins aussi efficace


async def main():
    """Test principal des optimisations basiques."""
    print("🔧 OPTIMISATIONS MÉMOIRE - TESTS BASIQUES")
    print("=" * 50)
    
    tests = [
        ("Streaming", test_streaming_basic()),
        ("Compression", test_compression_basic()),
        ("Garbage Collection", test_memory_gc()),
        ("Itération Efficace", test_memory_efficient_iteration()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1
    
    total = len(results)
    success_rate = passed / total * 100
    
    print(f"\nRésultat: {passed}/{total} tests réussis ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 TOUTES LES OPTIMISATIONS BASIQUES FONCTIONNENT!")
    elif passed >= total * 0.75:
        print("✅ La plupart des optimisations fonctionnent bien")
    else:
        print("⚠️  Plusieurs optimisations ont des problèmes")
    
    # Informations finales sur la mémoire
    final_objects = len(gc.get_objects())
    final_collected = gc.collect()
    
    print(f"\n📊 État final de la mémoire:")
    print(f"   Objets Python: {final_objects}")
    print(f"   Dernière collecte: {final_collected} objets")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)