#!/usr/bin/env python3
"""
Moniteur de performance en temps réel pour Scrapinium.
Surveille et alerte sur les performances du système.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import argparse
from pathlib import Path

import aiohttp
import psutil


class PerformanceMonitor:
    """Moniteur de performance en temps réel."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        alert_thresholds: Dict[str, float] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.running = False
        self.metrics_history: List[Dict[str, Any]] = []
        
        # Seuils d'alerte par défaut
        self.alert_thresholds = alert_thresholds or {
            "response_time_ms": 5000,     # Temps de réponse > 5s
            "memory_usage_mb": 1024,       # Mémoire > 1GB
            "cpu_usage_percent": 80,       # CPU > 80%
            "cache_hit_rate": 0.7,         # Cache hit rate < 70%
            "error_rate_percent": 10,      # Taux d'erreur > 10%
            "queue_length": 10             # File d'attente > 10
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collecte les métriques du système."""
        
        timestamp = datetime.now()
        metrics = {
            "timestamp": timestamp.isoformat(),
            "system": {},
            "api": {},
            "scrapinium": {}
        }
        
        try:
            # Métriques système
            process = psutil.Process()
            metrics["system"] = {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "connections": len(process.connections()),
                "uptime_seconds": time.time() - process.create_time()
            }
            
            # Métriques API de base
            try:
                async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                    if response.status == 200:
                        metrics["api"]["health"] = "ok"
                        metrics["api"]["response_time_ms"] = response.headers.get("x-response-time", 0)
                    else:
                        metrics["api"]["health"] = f"error_{response.status}"
            except asyncio.TimeoutError:
                metrics["api"]["health"] = "timeout"
            except Exception as e:
                metrics["api"]["health"] = f"error_{str(e)}"
            
            # Métriques Scrapinium spécifiques
            await self._collect_scrapinium_metrics(metrics)
            
        except Exception as e:
            print(f"❌ Erreur collecte métriques: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    async def _collect_scrapinium_metrics(self, metrics: Dict[str, Any]):
        """Collecte les métriques spécifiques à Scrapinium."""
        
        scrapinium_metrics = {}
        
        # Statistiques générales
        try:
            async with self.session.get(f"{self.base_url}/stats", timeout=5) as response:
                if response.status == 200:
                    stats = await response.json()
                    scrapinium_metrics["general"] = stats.get("data", {})
        except Exception as e:
            scrapinium_metrics["general_error"] = str(e)
        
        # Métriques de performance
        try:
            async with self.session.get(f"{self.base_url}/performance/metrics/live", timeout=5) as response:
                if response.status == 200:
                    perf_data = await response.json()
                    scrapinium_metrics["performance"] = perf_data.get("data", {})
        except Exception as e:
            scrapinium_metrics["performance_error"] = str(e)
        
        # Métriques du cache
        try:
            async with self.session.get(f"{self.base_url}/stats/cache", timeout=5) as response:
                if response.status == 200:
                    cache_data = await response.json()
                    scrapinium_metrics["cache"] = cache_data.get("data", {})
        except Exception as e:
            scrapinium_metrics["cache_error"] = str(e)
        
        # Métriques mémoire
        try:
            async with self.session.get(f"{self.base_url}/stats/memory", timeout=5) as response:
                if response.status == 200:
                    memory_data = await response.json()
                    scrapinium_metrics["memory"] = memory_data.get("data", {})
        except Exception as e:
            scrapinium_metrics["memory_error"] = str(e)
        
        # Métriques du pool de navigateurs
        try:
            async with self.session.get(f"{self.base_url}/stats/browser", timeout=5) as response:
                if response.status == 200:
                    browser_data = await response.json()
                    scrapinium_metrics["browser_pool"] = browser_data.get("data", {})
        except Exception as e:
            scrapinium_metrics["browser_error"] = str(e)
        
        metrics["scrapinium"] = scrapinium_metrics
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie les seuils d'alerte et retourne les alertes actives."""
        
        alerts = []
        
        # Alerte temps de réponse
        response_time = metrics.get("api", {}).get("response_time_ms", 0)
        if isinstance(response_time, (int, float)) and response_time > self.alert_thresholds["response_time_ms"]:
            alerts.append({
                "type": "response_time",
                "severity": "warning",
                "message": f"Temps de réponse élevé: {response_time}ms",
                "threshold": self.alert_thresholds["response_time_ms"],
                "current_value": response_time
            })
        
        # Alerte mémoire
        memory_mb = metrics.get("system", {}).get("memory_mb", 0)
        if memory_mb > self.alert_thresholds["memory_usage_mb"]:
            alerts.append({
                "type": "memory_usage",
                "severity": "warning" if memory_mb < self.alert_thresholds["memory_usage_mb"] * 1.5 else "critical",
                "message": f"Consommation mémoire élevée: {memory_mb:.0f}MB",
                "threshold": self.alert_thresholds["memory_usage_mb"],
                "current_value": memory_mb
            })
        
        # Alerte CPU
        cpu_percent = metrics.get("system", {}).get("cpu_percent", 0)
        if cpu_percent > self.alert_thresholds["cpu_usage_percent"]:
            alerts.append({
                "type": "cpu_usage",
                "severity": "warning",
                "message": f"Utilisation CPU élevée: {cpu_percent:.1f}%",
                "threshold": self.alert_thresholds["cpu_usage_percent"],
                "current_value": cpu_percent
            })
        
        # Alerte cache hit rate
        cache_stats = metrics.get("scrapinium", {}).get("cache", {})
        if cache_stats and "hit_rate" in cache_stats:
            hit_rate = cache_stats["hit_rate"]
            if hit_rate < self.alert_thresholds["cache_hit_rate"]:
                alerts.append({
                    "type": "cache_hit_rate",
                    "severity": "info",
                    "message": f"Taux de hit cache faible: {hit_rate:.1%}",
                    "threshold": self.alert_thresholds["cache_hit_rate"],
                    "current_value": hit_rate
                })
        
        # Alerte taux d'erreur
        general_stats = metrics.get("scrapinium", {}).get("general", {})
        if general_stats and "failed_tasks" in general_stats and "total_tasks" in general_stats:
            total = general_stats["total_tasks"]
            failed = general_stats["failed_tasks"]
            if total > 0:
                error_rate = (failed / total) * 100
                if error_rate > self.alert_thresholds["error_rate_percent"]:
                    alerts.append({
                        "type": "error_rate",
                        "severity": "warning",
                        "message": f"Taux d'erreur élevé: {error_rate:.1f}%",
                        "threshold": self.alert_thresholds["error_rate_percent"],
                        "current_value": error_rate
                    })
        
        # Alerte file d'attente
        browser_pool = metrics.get("scrapinium", {}).get("browser_pool", {})
        if browser_pool and "queue_length" in browser_pool:
            queue_length = browser_pool["queue_length"]
            if queue_length > self.alert_thresholds["queue_length"]:
                alerts.append({
                    "type": "queue_length",
                    "severity": "warning",
                    "message": f"File d'attente longue: {queue_length} tâches",
                    "threshold": self.alert_thresholds["queue_length"],
                    "current_value": queue_length
                })
        
        return alerts
    
    def print_dashboard(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]):
        """Affiche un dashboard en temps réel."""
        
        # Effacer l'écran
        print("\033[2J\033[H", end="")
        
        # En-tête
        print("=" * 80)
        print(f"📊 SCRAPINIUM PERFORMANCE DASHBOARD - {metrics['timestamp']}")
        print("=" * 80)
        
        # Statut général
        api_health = metrics.get("api", {}).get("health", "unknown")
        health_icon = "✅" if api_health == "ok" else "❌"
        print(f"\n🔍 STATUT GÉNÉRAL: {health_icon} API {api_health.upper()}")
        
        # Métriques système
        system = metrics.get("system", {})
        print(f"\n🖥️  SYSTÈME:")
        print(f"   CPU: {system.get('cpu_percent', 0):.1f}%")
        print(f"   Mémoire: {system.get('memory_mb', 0):.0f} MB ({system.get('memory_percent', 0):.1f}%)")
        print(f"   Threads: {system.get('threads', 0)}")
        print(f"   Connexions: {system.get('connections', 0)}")
        
        # Métriques Scrapinium
        scrap = metrics.get("scrapinium", {})
        
        # Statistiques générales
        general = scrap.get("general", {})
        if general:
            print(f"\n📈 TÂCHES:")
            print(f"   Total: {general.get('total_tasks', 0)}")
            print(f"   Actives: {general.get('active_tasks', 0)}")
            print(f"   Terminées: {general.get('completed_tasks', 0)}")
            print(f"   Échouées: {general.get('failed_tasks', 0)}")
            print(f"   Taux de succès: {general.get('success_rate', 0):.1f}%")
        
        # Cache
        cache = scrap.get("cache", {})
        if cache:
            print(f"\n💾 CACHE:")
            print(f"   Hit rate: {cache.get('hit_rate', 0):.1%}")
            print(f"   Entrées: {cache.get('total_entries', 0)}")
            print(f"   Mémoire: {cache.get('memory_usage_mb', 0):.0f} MB")
        
        # Pool de navigateurs
        browser = scrap.get("browser_pool", {})
        if browser:
            print(f"\n🌐 NAVIGATEURS:")
            print(f"   Actifs: {browser.get('active_browsers', 0)}")
            print(f"   Disponibles: {browser.get('available_browsers', 0)}")
            print(f"   File d'attente: {browser.get('queue_length', 0)}")
        
        # Performance
        perf = scrap.get("performance", {})
        if perf:
            current_metrics = perf.get("current_metrics", {})
            summary = perf.get("performance_summary", {})
            
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Opérations totales: {summary.get('total_operations', 0)}")
            print(f"   Durée moyenne: {summary.get('average_duration_ms', 0):.0f} ms")
            print(f"   P95: {summary.get('p95_duration_ms', 0):.0f} ms")
            print(f"   Goulots d'étranglement: {summary.get('active_bottlenecks', 0)}")
        
        # Alertes
        if alerts:
            print(f"\n🚨 ALERTES ({len(alerts)}):")
            for alert in alerts:
                severity_icon = {
                    "info": "ℹ️",
                    "warning": "⚠️", 
                    "critical": "🔥"
                }.get(alert["severity"], "❓")
                print(f"   {severity_icon} {alert['message']}")
        else:
            print(f"\n✅ Aucune alerte active")
        
        # Pied de page
        print("\n" + "=" * 80)
        print("Appuyez sur Ctrl+C pour arrêter")
    
    def save_metrics_history(self, filepath: str):
        """Sauvegarde l'historique des métriques."""
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
            print(f"💾 Historique sauvegardé: {filepath}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyse les tendances des métriques."""
        
        if len(self.metrics_history) < 2:
            return {"error": "Pas assez de données pour l'analyse"}
        
        recent = self.metrics_history[-10:]  # 10 dernières mesures
        
        analysis = {
            "memory_trend": self._calculate_trend([m.get("system", {}).get("memory_mb", 0) for m in recent]),
            "cpu_trend": self._calculate_trend([m.get("system", {}).get("cpu_percent", 0) for m in recent]),
            "response_time_trend": self._calculate_trend([
                m.get("api", {}).get("response_time_ms", 0) for m in recent
            ]),
            "total_measurements": len(self.metrics_history),
            "time_span_minutes": (datetime.fromisoformat(recent[-1]["timestamp"]) - 
                                datetime.fromisoformat(recent[0]["timestamp"])).total_seconds() / 60
        }
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcule la tendance d'une série de valeurs."""
        
        if len(values) < 2:
            return "stable"
        
        # Calcul de la pente
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Classification de la tendance
        if abs(slope) < 0.1:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    async def run_monitoring(
        self, 
        interval_seconds: int = 30,
        save_interval_minutes: int = 10,
        output_file: str = None
    ):
        """Lance le monitoring en temps réel."""
        
        self.running = True
        last_save = time.time()
        
        print(f"🚀 Démarrage du monitoring (intervalle: {interval_seconds}s)")
        
        try:
            while self.running:
                # Collecte des métriques
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Vérification des alertes
                alerts = self.check_alerts(metrics)
                
                # Affichage du dashboard
                self.print_dashboard(metrics, alerts)
                
                # Sauvegarde périodique
                if output_file and (time.time() - last_save) > (save_interval_minutes * 60):
                    self.save_metrics_history(output_file)
                    last_save = time.time()
                
                # Limiter l'historique en mémoire
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-500:]  # Garder les 500 dernières
                
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt du monitoring...")
            self.running = False
            
            if output_file:
                self.save_metrics_history(output_file)
            
            # Analyse finale
            analysis = self.analyze_trends()
            if "error" not in analysis:
                print("\n📊 ANALYSE DES TENDANCES:")
                print(f"   Mémoire: {analysis['memory_trend']}")
                print(f"   CPU: {analysis['cpu_trend']}")
                print(f"   Temps de réponse: {analysis['response_time_trend']}")
                print(f"   Durée de monitoring: {analysis['time_span_minutes']:.1f} minutes")


def main():
    """Point d'entrée principal."""
    
    parser = argparse.ArgumentParser(description="Moniteur de performance Scrapinium")
    parser.add_argument("--url", default="http://localhost:8000", help="URL de base de l'API")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle de collecte (secondes)")
    parser.add_argument("--output", help="Fichier de sortie pour l'historique")
    parser.add_argument("--save-interval", type=int, default=10, help="Intervalle de sauvegarde (minutes)")
    
    # Seuils d'alerte personnalisés
    parser.add_argument("--memory-threshold", type=float, default=1024, help="Seuil mémoire (MB)")
    parser.add_argument("--cpu-threshold", type=float, default=80, help="Seuil CPU (%)")
    parser.add_argument("--response-threshold", type=float, default=5000, help="Seuil temps réponse (ms)")
    
    args = parser.parse_args()
    
    # Configuration des seuils
    thresholds = {
        "memory_usage_mb": args.memory_threshold,
        "cpu_usage_percent": args.cpu_threshold,
        "response_time_ms": args.response_threshold,
        "cache_hit_rate": 0.7,
        "error_rate_percent": 10,
        "queue_length": 10
    }
    
    async def run():
        async with PerformanceMonitor(args.url, thresholds) as monitor:
            await monitor.run_monitoring(
                interval_seconds=args.interval,
                save_interval_minutes=args.save_interval,
                output_file=args.output
            )
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
        return 0
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1


if __name__ == "__main__":
    exit(main())