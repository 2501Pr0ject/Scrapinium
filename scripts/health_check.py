#!/usr/bin/env python3
"""
Script de health check pour Scrapinium.
Vérifie que tous les services sont opérationnels.
"""

import asyncio
import aiohttp
import argparse
import json
import sys
from typing import Dict, List, Any


class HealthChecker:
    """Vérificateur de santé pour Scrapinium."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_api_health(self) -> Dict[str, Any]:
        """Vérifie la santé de l'API."""
        try:
            async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "response_time_ms": response.headers.get("x-response-time", "unknown"),
                        "data": data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_database(self) -> Dict[str, Any]:
        """Vérifie la connexion à la base de données."""
        try:
            async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    db_status = data.get("database", "unknown")
                    return {
                        "status": "healthy" if db_status == "healthy" else "unhealthy",
                        "details": db_status
                    }
                else:
                    return {"status": "error", "error": "API unreachable"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_cache(self) -> Dict[str, Any]:
        """Vérifie le système de cache."""
        try:
            async with self.session.get(f"{self.base_url}/stats/cache", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    cache_data = data.get("data", {})
                    return {
                        "status": "healthy",
                        "hit_rate": cache_data.get("hit_rate", 0),
                        "entries": cache_data.get("total_entries", 0)
                    }
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_browser_pool(self) -> Dict[str, Any]:
        """Vérifie le pool de navigateurs."""
        try:
            async with self.session.get(f"{self.base_url}/stats/browser", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    browser_data = data.get("data", {})
                    pool_status = browser_data.get("pool_status", {})
                    return {
                        "status": "healthy",
                        "active_browsers": pool_status.get("active_browsers", 0),
                        "available_browsers": pool_status.get("available_browsers", 0)
                    }
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_memory(self) -> Dict[str, Any]:
        """Vérifie l'utilisation mémoire."""
        try:
            async with self.session.get(f"{self.base_url}/stats/memory", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    memory_data = data.get("data", {})
                    current_usage = memory_data.get("current_usage", {})
                    memory_mb = current_usage.get("process_memory_mb", 0)
                    
                    # Seuil d'alerte à 1GB
                    status = "healthy" if memory_mb < 1024 else "warning"
                    
                    return {
                        "status": status,
                        "memory_mb": memory_mb,
                        "warning_threshold": 1024
                    }
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_security(self) -> Dict[str, Any]:
        """Vérifie les fonctionnalités de sécurité."""
        try:
            async with self.session.get(f"{self.base_url}/security/compliance/check", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    security_data = data.get("data", {})
                    overall_score = security_data.get("overall_score", 0)
                    
                    if overall_score > 90:
                        status = "excellent"
                    elif overall_score > 80:
                        status = "good"
                    elif overall_score > 70:
                        status = "fair"
                    else:
                        status = "poor"
                    
                    return {
                        "status": status,
                        "score": overall_score,
                        "details": security_data
                    }
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Lance tous les checks de santé."""
        
        checks = {
            "api": self.check_api_health(),
            "database": self.check_database(),
            "cache": self.check_cache(),
            "browser_pool": self.check_browser_pool(),
            "memory": self.check_memory(),
            "security": self.check_security()
        }
        
        results = {}
        for name, check_coro in checks.items():
            try:
                results[name] = await check_coro
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        
        # Calcul du statut global
        statuses = [result.get("status") for result in results.values()]
        if "error" in statuses:
            overall_status = "critical"
        elif "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results.values() if r.get("status") == "healthy"),
                "unhealthy": sum(1 for r in results.values() if r.get("status") in ["unhealthy", "error"]),
                "warnings": sum(1 for r in results.values() if r.get("status") == "warning")
            }
        }


def print_results(results: Dict[str, Any], verbose: bool = False):
    """Affiche les résultats de manière lisible."""
    
    overall = results["overall_status"]
    summary = results["summary"]
    
    # Icônes pour les statuts
    status_icons = {
        "healthy": "✅",
        "excellent": "🌟",
        "good": "✅",
        "fair": "⚠️",
        "warning": "⚠️",
        "unhealthy": "❌",
        "error": "💥",
        "critical": "🔥",
        "poor": "❌"
    }
    
    print(f"\n{status_icons.get(overall, '❓')} **Statut Global: {overall.upper()}**")
    print(f"📊 Résumé: {summary['healthy']} OK, {summary['unhealthy']} KO, {summary['warnings']} warnings")
    
    print("\n📋 **Détails des vérifications:**")
    for check_name, check_result in results["checks"].items():
        status = check_result.get("status", "unknown")
        icon = status_icons.get(status, "❓")
        print(f"  {icon} {check_name.replace('_', ' ').title()}: {status}")
        
        if verbose and check_result.get("error"):
            print(f"    ❌ Erreur: {check_result['error']}")
        
        # Affichage des détails spécifiques
        if verbose:
            if check_name == "cache" and "hit_rate" in check_result:
                print(f"    📊 Hit rate: {check_result['hit_rate']:.1%}")
            elif check_name == "memory" and "memory_mb" in check_result:
                print(f"    🧠 Mémoire: {check_result['memory_mb']:.1f} MB")
            elif check_name == "security" and "score" in check_result:
                print(f"    🛡️ Score sécurité: {check_result['score']:.1f}/100")


async def main():
    """Point d'entrée principal."""
    
    parser = argparse.ArgumentParser(description="Health check pour Scrapinium")
    parser.add_argument("--url", default="http://localhost:8000", help="URL de base de l'API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Affichage verbeux")
    parser.add_argument("--json", action="store_true", help="Sortie en format JSON")
    parser.add_argument("--fail-on-error", action="store_true", help="Sortir avec code d'erreur si problème")
    
    args = parser.parse_args()
    
    async with HealthChecker(args.url) as checker:
        print(f"🔍 Health check de Scrapinium ({args.url})")
        print("=" * 50)
        
        results = await checker.run_all_checks()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_results(results, args.verbose)
        
        # Code de sortie
        if args.fail_on_error and results["overall_status"] in ["critical", "unhealthy"]:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())