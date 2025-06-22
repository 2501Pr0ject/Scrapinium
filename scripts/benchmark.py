#!/usr/bin/env python3
"""
Script de benchmark pour Scrapinium.
Lance des tests de performance complets.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import json
import argparse
from pathlib import Path

import aiohttp

# Configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_URLS = [
    "https://httpbin.org/html",
    "https://httpbin.org/json", 
    "https://httpbin.org/delay/1",
    "https://example.com",
    "https://httpbin.org/headers"
]


class ScrapiniumBenchmark:
    """Classe principale pour les benchmarks Scrapinium."""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """Vérifie que l'API est accessible."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False
    
    async def benchmark_single_scrape(self, url: str, use_llm: bool = False) -> Dict[str, Any]:
        """Benchmark d'un scraping unique."""
        
        start_time = time.perf_counter()
        
        try:
            # Créer la tâche
            task_data = {
                "url": url,
                "output_format": "markdown",
                "use_llm": use_llm,
                "llm_provider": "ollama"
            }
            
            async with self.session.post(f"{self.base_url}/scrape", json=task_data) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"Failed to create task: {response.status}",
                        "duration_ms": 0
                    }
                
                task_result = await response.json()
                task_id = task_result["data"]["task_id"]
            
            # Attendre la completion
            max_wait = 30  # 30 seconds timeout
            wait_time = 0
            
            while wait_time < max_wait:
                async with self.session.get(f"{self.base_url}/scrape/{task_id}") as response:
                    if response.status == 200:
                        status_result = await response.json()
                        task_status = status_result["data"]["status"]
                        
                        if task_status == "completed":
                            end_time = time.perf_counter()
                            duration_ms = (end_time - start_time) * 1000
                            
                            return {
                                "success": True,
                                "duration_ms": duration_ms,
                                "url": url,
                                "use_llm": use_llm,
                                "task_id": task_id,
                                "metadata": status_result["data"].get("metadata", {})
                            }
                        
                        elif task_status == "failed":
                            return {
                                "success": False,
                                "error": status_result["data"].get("error", "Unknown error"),
                                "duration_ms": (time.perf_counter() - start_time) * 1000
                            }
                
                await asyncio.sleep(0.5)
                wait_time += 0.5
            
            return {
                "success": False,
                "error": "Timeout waiting for task completion",
                "duration_ms": (time.perf_counter() - start_time) * 1000
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start_time) * 1000
            }
    
    async def benchmark_concurrent_scrapes(
        self, 
        urls: List[str], 
        concurrency: int = 5,
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """Benchmark de scraping concurrent."""
        
        print(f"🚀 Démarrage benchmark concurrent: {len(urls)} URLs, concurrence {concurrency}")
        
        start_time = time.perf_counter()
        
        # Limiter la concurrence
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.benchmark_single_scrape(url, use_llm)
        
        # Lancer toutes les tâches
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_duration = (end_time - start_time) * 1000
        
        # Analyser les résultats
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        durations = [r["duration_ms"] for r in successful_results]
        
        return {
            "total_urls": len(urls),
            "successful_scrapes": len(successful_results),
            "failed_scrapes": len(failed_results),
            "concurrency": concurrency,
            "use_llm": use_llm,
            "total_duration_ms": total_duration,
            "average_duration_ms": statistics.mean(durations) if durations else 0,
            "median_duration_ms": statistics.median(durations) if durations else 0,
            "p95_duration_ms": self._percentile(durations, 95) if durations else 0,
            "p99_duration_ms": self._percentile(durations, 99) if durations else 0,
            "throughput_urls_per_second": len(successful_results) / (total_duration / 1000) if total_duration > 0 else 0,
            "success_rate": len(successful_results) / len(urls) * 100 if urls else 0,
            "detailed_results": results
        }
    
    async def benchmark_api_endpoints(self) -> Dict[str, Any]:
        """Benchmark des endpoints de l'API."""
        
        endpoints = [
            ("/health", "GET", None),
            ("/stats", "GET", None),
            ("/stats/cache", "GET", None),
            ("/stats/memory", "GET", None),
            ("/tasks", "GET", None),
            ("/performance/report", "GET", None),
            ("/performance/metrics/live", "GET", None)
        ]
        
        results = {}
        
        for endpoint, method, data in endpoints:
            durations = []
            errors = 0
            
            # Tester chaque endpoint 10 fois
            for _ in range(10):
                start_time = time.perf_counter()
                
                try:
                    if method == "GET":
                        async with self.session.get(f"{self.base_url}{endpoint}") as response:
                            success = response.status == 200
                    else:
                        async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                            success = response.status == 200
                    
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    if success:
                        durations.append(duration_ms)
                    else:
                        errors += 1
                        
                except Exception:
                    errors += 1
                
                await asyncio.sleep(0.1)  # Petit délai entre les requêtes
            
            if durations:
                results[endpoint] = {
                    "average_ms": statistics.mean(durations),
                    "median_ms": statistics.median(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "p95_ms": self._percentile(durations, 95),
                    "success_rate": len(durations) / 10 * 100,
                    "errors": errors
                }
            else:
                results[endpoint] = {
                    "average_ms": 0,
                    "errors": errors,
                    "success_rate": 0
                }
        
        return results
    
    async def benchmark_cache_performance(self) -> Dict[str, Any]:
        """Benchmark des performances du cache."""
        
        print("📦 Test des performances du cache...")
        
        # Utiliser la même URL plusieurs fois pour tester le cache
        test_url = "https://httpbin.org/json"
        
        # Premier appel (cache miss)
        first_result = await self.benchmark_single_scrape(test_url)
        
        # Attendre un peu
        await asyncio.sleep(1)
        
        # Deuxième appel (devrait être en cache)
        second_result = await self.benchmark_single_scrape(test_url)
        
        # Calculer l'amélioration
        cache_improvement = 0
        if (first_result.get("success") and second_result.get("success") and 
            first_result["duration_ms"] > 0):
            cache_improvement = (first_result["duration_ms"] - second_result["duration_ms"]) / first_result["duration_ms"] * 100
        
        return {
            "first_call_ms": first_result.get("duration_ms", 0),
            "second_call_ms": second_result.get("duration_ms", 0),
            "cache_improvement_percent": cache_improvement,
            "cache_effective": cache_improvement > 50,  # Plus de 50% d'amélioration
            "first_success": first_result.get("success", False),
            "second_success": second_result.get("success", False)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcule un percentile."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


async def run_complete_benchmark(
    base_url: str = DEFAULT_BASE_URL,
    urls: List[str] = None,
    concurrency: int = 5,
    test_llm: bool = False,
    output_file: str = None
) -> Dict[str, Any]:
    """Lance un benchmark complet."""
    
    if urls is None:
        urls = DEFAULT_URLS
    
    async with ScrapiniumBenchmark(base_url) as benchmark:
        
        # Vérifier la santé de l'API
        print("🔍 Vérification de l'API...")
        if not await benchmark.health_check():
            print("❌ L'API n'est pas accessible!")
            return {"error": "API not accessible"}
        
        print("✅ API accessible")
        
        results = {
            "timestamp": time.time(),
            "base_url": base_url,
            "test_config": {
                "urls_count": len(urls),
                "concurrency": concurrency,
                "test_llm": test_llm
            }
        }
        
        # 1. Benchmark des endpoints API
        print("\n📊 Benchmark des endpoints API...")
        results["api_endpoints"] = await benchmark.benchmark_api_endpoints()
        
        # 2. Benchmark de scraping simple
        print("\n🌐 Benchmark de scraping simple...")
        simple_results = []
        for url in urls[:3]:  # Tester seulement les 3 premiers
            result = await benchmark.benchmark_single_scrape(url, use_llm=False)
            simple_results.append(result)
            print(f"  {url}: {'✅' if result['success'] else '❌'} {result['duration_ms']:.0f}ms")
        
        results["simple_scraping"] = {
            "results": simple_results,
            "success_rate": sum(1 for r in simple_results if r["success"]) / len(simple_results) * 100,
            "average_duration_ms": statistics.mean([r["duration_ms"] for r in simple_results if r["success"]])
        }
        
        # 3. Benchmark concurrent
        print(f"\n⚡ Benchmark concurrent ({concurrency} concurrent)...")
        results["concurrent_scraping"] = await benchmark.benchmark_concurrent_scrapes(
            urls, concurrency=concurrency, use_llm=False
        )
        
        # 4. Benchmark du cache
        print("\n💾 Benchmark du cache...")
        results["cache_performance"] = await benchmark.benchmark_cache_performance()
        
        # 5. Benchmark avec LLM (optionnel)
        if test_llm:
            print("\n🧠 Benchmark avec LLM...")
            llm_result = await benchmark.benchmark_single_scrape(urls[0], use_llm=True)
            results["llm_scraping"] = llm_result
        
        # Résumé final
        print("\n" + "="*60)
        print("📈 RÉSULTATS DU BENCHMARK")
        print("="*60)
        
        print(f"📊 Endpoints API:")
        for endpoint, stats in results["api_endpoints"].items():
            print(f"  {endpoint}: {stats['average_ms']:.1f}ms (succès: {stats['success_rate']:.0f}%)")
        
        print(f"\n🌐 Scraping simple:")
        print(f"  Taux de succès: {results['simple_scraping']['success_rate']:.1f}%")
        print(f"  Durée moyenne: {results['simple_scraping']['average_duration_ms']:.0f}ms")
        
        print(f"\n⚡ Scraping concurrent:")
        concurrent = results["concurrent_scraping"]
        print(f"  URLs traitées: {concurrent['successful_scrapes']}/{concurrent['total_urls']}")
        print(f"  Taux de succès: {concurrent['success_rate']:.1f}%")
        print(f"  Throughput: {concurrent['throughput_urls_per_second']:.2f} URLs/s")
        print(f"  P95: {concurrent['p95_duration_ms']:.0f}ms")
        
        print(f"\n💾 Performance du cache:")
        cache = results["cache_performance"]
        print(f"  Premier appel: {cache['first_call_ms']:.0f}ms")
        print(f"  Second appel: {cache['second_call_ms']:.0f}ms")
        print(f"  Amélioration: {cache['cache_improvement_percent']:.1f}%")
        print(f"  Cache efficace: {'✅' if cache['cache_effective'] else '❌'}")
        
        if test_llm and "llm_scraping" in results:
            llm = results["llm_scraping"]
            print(f"\n🧠 Scraping avec LLM:")
            print(f"  Succès: {'✅' if llm['success'] else '❌'}")
            print(f"  Durée: {llm['duration_ms']:.0f}ms")
        
        # Sauvegarder les résultats
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Résultats sauvegardés dans {output_file}")
        
        return results


def main():
    """Point d'entrée principal."""
    
    parser = argparse.ArgumentParser(description="Benchmark Scrapinium")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="URL de base de l'API")
    parser.add_argument("--concurrency", type=int, default=5, help="Niveau de concurrence")
    parser.add_argument("--test-llm", action="store_true", help="Tester le LLM")
    parser.add_argument("--output", help="Fichier de sortie JSON")
    parser.add_argument("--urls", nargs="+", help="URLs personnalisées à tester")
    
    args = parser.parse_args()
    
    # Lancer le benchmark
    results = asyncio.run(run_complete_benchmark(
        base_url=args.url,
        urls=args.urls or DEFAULT_URLS,
        concurrency=args.concurrency,
        test_llm=args.test_llm,
        output_file=args.output
    ))
    
    if "error" in results:
        print(f"❌ Erreur: {results['error']}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())