#!/usr/bin/env python3
"""
Test complet des optimisations mémoire de Scrapinium.
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapinium.utils.memory import get_memory_monitor, setup_memory_monitoring
from scrapinium.utils.cleanup import get_resource_cleaner, get_auto_cleaner
from scrapinium.utils.streaming import StreamingProcessor, MemoryEfficientProcessor
from scrapinium.utils.compression import compress_data, get_best_compression, CompressionAlgorithm


async def test_memory_monitoring():
    """Test du système de surveillance mémoire."""
    print("🧪 Test surveillance mémoire")
    print("-" * 40)
    
    monitor = get_memory_monitor()
    
    # Snapshot initial
    initial_snapshot = await monitor.take_snapshot()
    print(f"Mémoire initiale: {initial_snapshot.process_memory_mb:.1f}MB")
    print(f"Objets GC: {initial_snapshot.gc_objects}")
    print(f"Coroutines actives: {initial_snapshot.active_coroutines}")
    
    # Créer une charge mémoire artificielle
    large_data = []
    for i in range(100):
        large_data.append("X" * 10000)  # 1MB total
    
    # Nouveau snapshot
    loaded_snapshot = await monitor.take_snapshot()
    print(f"Après charge: {loaded_snapshot.process_memory_mb:.1f}MB")
    print(f"Augmentation: {loaded_snapshot.process_memory_mb - initial_snapshot.process_memory_mb:.1f}MB")
    
    # Test GC forcé
    freed_objects = await monitor.force_gc()
    print(f"GC forcé: {freed_objects} objets libérés")
    
    # Test optimisation
    optimization_result = await monitor.optimize_memory()
    print(f"Optimisation: {optimization_result['memory_saved_mb']:.1f}MB économisés")
    
    # Nettoyer
    del large_data
    await monitor.force_gc()
    
    final_snapshot = await monitor.take_snapshot()
    print(f"Mémoire finale: {final_snapshot.process_memory_mb:.1f}MB")
    
    return True


async def test_resource_cleanup():
    """Test du système de nettoyage de ressources."""
    print("\n🧹 Test nettoyage ressources")
    print("-" * 40)
    
    cleaner = get_resource_cleaner()
    
    # Exécuter toutes les règles de nettoyage
    results = await cleaner.run_all_cleanup_rules()
    
    total_cleaned = 0
    total_freed = 0
    
    for result in results:
        print(f"{result.resource_type.value}: {result.items_cleaned} items, {result.bytes_freed} bytes")
        if result.success:
            total_cleaned += result.items_cleaned
            total_freed += result.bytes_freed
    
    print(f"Total: {total_cleaned} items, {total_freed // 1024 // 1024}MB libérés")
    
    # Statistiques
    stats = cleaner.get_cleanup_stats()
    print(f"Taux de succès: {stats['summary']['overall_success_rate']:.1%}")
    
    return True


def test_streaming_processor():
    """Test du processeur streaming."""
    print("\n🌊 Test processeur streaming")
    print("-" * 40)
    
    processor = StreamingProcessor(chunk_size=1024)
    
    # Créer du contenu volumineux
    large_content = "Test content " * 10000  # ~130KB
    
    print(f"Contenu original: {len(large_content)} bytes")
    
    async def process_stream():
        chunks_processed = 0
        total_bytes = 0
        
        async for chunk in processor.process_content_stream(large_content, max_size=50000):
            chunks_processed += 1
            total_bytes += chunk.size
            
            if chunks_processed <= 3:  # Afficher les 3 premiers
                print(f"Chunk {chunk.chunk_id}: {chunk.size} bytes (final: {chunk.is_final})")
        
        print(f"Total: {chunks_processed} chunks, {total_bytes} bytes traités")
        return chunks_processed > 0
    
    return asyncio.run(process_stream())


def test_compression():
    """Test des systèmes de compression."""
    print("\n🗜️  Test compression")
    print("-" * 40)
    
    # Test données texte
    test_data = {
        "message": "Hello World! " * 1000,
        "data": list(range(1000)),
        "metadata": {"timestamp": time.time(), "version": "1.0"}
    }
    
    print(f"Données originales: {len(str(test_data))} caractères")
    
    # Tester différents algorithmes
    algorithms = [
        CompressionAlgorithm.GZIP,
        CompressionAlgorithm.ZLIB,
        # CompressionAlgorithm.LZ4,  # Peut ne pas être disponible
        # CompressionAlgorithm.BROTLI,  # Peut ne pas être disponible
    ]
    
    best_result = None
    
    for algorithm in algorithms:
        try:
            result = compress_data(test_data, algorithm)
            ratio = result.compression_ratio
            saved = result.space_saved_percent
            
            print(f"{algorithm.value}: {result.compressed_size} bytes (ratio: {ratio:.2f}, économie: {saved:.1f}%)")
            
            if best_result is None or result.compressed_size < best_result.compressed_size:
                best_result = result
                
        except Exception as e:
            print(f"{algorithm.value}: ERREUR - {e}")
    
    if best_result:
        print(f"Meilleur: {best_result.algorithm.value} ({best_result.space_saved_percent:.1f}% économie)")
    
    return best_result is not None


async def test_memory_efficient_processing():
    """Test du processeur efficace en mémoire."""
    print("\n⚡ Test processeur efficace mémoire")
    print("-" * 40)
    
    processor = MemoryEfficientProcessor(max_memory_mb=10)
    
    # HTML volumineux simulé
    large_html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
    """ + "<p>This is test content. " * 5000 + """
    <a href="http://example.com">Link 1</a>
    <a href="http://test.com">Link 2</a>
    </body>
    </html>
    """
    
    print(f"HTML original: {len(large_html)} bytes")
    
    # Traitement efficace
    result = await processor.process_large_html(
        large_html,
        extract_text=True,
        extract_links=True,
        max_content_size=50000
    )
    
    print(f"Texte extrait: {len(result['text_content'])} caractères")
    print(f"Liens trouvés: {len(result['links'])}")
    print(f"Tronqué: {result['metadata']['truncated']}")
    print(f"Taille traitée: {result['metadata']['processed_size']} bytes")
    
    return len(result['text_content']) > 0


async def test_full_optimization_suite():
    """Test complet de tous les systèmes d'optimisation."""
    print("🚀 SUITE COMPLÈTE D'OPTIMISATION MÉMOIRE")
    print("=" * 60)
    
    results = {}
    
    try:
        # 1. Surveillance mémoire
        results["memory_monitoring"] = await test_memory_monitoring()
        
        # 2. Nettoyage ressources  
        results["resource_cleanup"] = await test_resource_cleanup()
        
        # 3. Streaming
        results["streaming"] = test_streaming_processor()
        
        # 4. Compression
        results["compression"] = test_compression()
        
        # 5. Traitement efficace
        results["efficient_processing"] = await test_memory_efficient_processing()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:.<30} {status}")
            if success:
                passed += 1
        
        print(f"\nRésultat global: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 TOUS LES SYSTÈMES D'OPTIMISATION FONCTIONNENT!")
        elif passed > total * 0.8:
            print("✅ La plupart des optimisations fonctionnent")
        else:
            print("⚠️  Plusieurs systèmes d'optimisation ont des problèmes")
        
        # Rapport mémoire final
        monitor = get_memory_monitor()
        final_report = monitor.get_memory_report()
        
        print(f"\n📊 ÉTAT MÉMOIRE FINAL:")
        print(f"   Utilisation actuelle: {final_report['current_usage']['process_memory_mb']:.1f}MB")
        print(f"   Pic d'utilisation: {final_report['statistics']['peak_usage_mb']:.1f}MB")
        print(f"   Tendance: {final_report['statistics']['usage_trend']}")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_optimization_suite())
    exit(0 if success else 1)