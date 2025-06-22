"""
Module de performance avancée pour Scrapinium.
Profiling, optimisation automatique et benchmarking.
"""

from .profiler import (
    AdvancedProfiler,
    BenchmarkSuite,
    PerformanceMetrics,
    ProfilingReport,
    performance_profiler,
    profile,
    profile_context
)

from .optimizer import (
    PerformanceOptimizer,
    AdaptiveOptimizer,
    OptimizationRule
)

__all__ = [
    # Profiler
    'AdvancedProfiler',
    'BenchmarkSuite', 
    'PerformanceMetrics',
    'ProfilingReport',
    'performance_profiler',
    'profile',
    'profile_context',
    
    # Optimizer
    'PerformanceOptimizer',
    'AdaptiveOptimizer',
    'OptimizationRule'
]