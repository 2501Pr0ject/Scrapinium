#!/usr/bin/env python3
"""Test simplifié des optimisations mémoire."""

import asyncio
import sys
import os
import gc
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapinium.utils.streaming import StreamingProcessor
from scrapinium.utils.compression import compress_data, CompressionAlgorithm


async def test_streaming():
    """Test du streaming processor."""
    print("🌊 Test Streaming Processor")
    print("-" * 30)
    
    processor = StreamingProcessor(chunk_size=1024)
    
    # Créer du contenu
    content = "Hello World! " * 1000  # ~13KB
    print(f"Contenu: {len(content)} bytes")
    
    chunks = 0
    total_bytes = 0
    
    async for chunk in processor.process_content_stream(content):
        chunks += 1
        total_bytes += chunk.size
        if chunks <= 3:
            print(f"  Chunk {chunk.chunk_id}: {chunk.size} bytes")
    
    print(f"Total: {chunks} chunks, {total_bytes} bytes")
    
    # Statistiques
    stats = processor.get_stats()
    print(f"Stats: {stats['total_chunks']} chunks, {stats['processed_bytes']} bytes")
    
    return chunks > 0


def test_compression():
    """Test de compression."""
    print("\n🗜️  Test Compression")
    print("-" * 30)
    
    # Données de test
    data = {
        "message": "Test data " * 500,
        "numbers": list(range(1000)),
        "timestamp": time.time()
    }
    
    import json
    original_size = len(json.dumps(data))
    print(f"Données originales: {original_size} bytes")
    
    # Test GZIP
    try:
        result = compress_data(data, CompressionAlgorithm.GZIP)
        ratio = result.compression_ratio
        saved = result.space_saved_percent
        
        print(f"GZIP: {result.compressed_size} bytes")
        print(f"Ratio: {ratio:.2f} (économie: {saved:.1f}%)")
        print(f"Efficace: {result.is_effective}")
        
        return result.is_effective
    except Exception as e:
        print(f"Erreur compression: {e}")
        return False


def test_memory_usage():
    """Test de l'utilisation mémoire."""
    print("\n💾 Test Utilisation Mémoire")
    print("-" * 30)
    
    # Avant
    objects_before = len(gc.get_objects())
    print(f"Objets avant: {objects_before}")
    
    # Créer des données
    large_list = []
    for i in range(10000):
        large_list.append(f"Item {i}")
    
    objects_during = len(gc.get_objects())
    print(f"Objets pendant: {objects_during}")
    print(f"Objets créés: {objects_during - objects_before}")
    
    # Nettoyer
    del large_list
    collected = gc.collect()
    
    objects_after = len(gc.get_objects())
    print(f"Objets après GC: {objects_after}")
    print(f"Objets collectés: {collected}")
    print(f"Objets libérés: {objects_during - objects_after}")
    
    return collected > 0


async def main():
    """Test principal."""
    print("🧪 Test Optimisations Mémoire (Simplifié)")
    print("=" * 50)
    
    results = []
    
    # Tests
    results.append(await test_streaming())
    results.append(test_compression())
    results.append(test_memory_usage())
    
    # Résumé
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS")
    print("=" * 50)
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
    else:
        print("⚠️  Certains tests ont échoué")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}")