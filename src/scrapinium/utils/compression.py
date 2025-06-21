"""Utilitaires de compression pour optimiser le stockage."""

import gzip
import zlib
import lz4.frame
import brotli
from typing import Union, Tuple, Dict, Any
from enum import Enum
import json
import pickle

from ..config import get_logger

logger = get_logger("utils.compression")


class CompressionAlgorithm(str, Enum):
    """Algorithmes de compression disponibles."""
    GZIP = "gzip"
    ZLIB = "zlib" 
    LZ4 = "lz4"
    BROTLI = "brotli"


class CompressionResult:
    """Résultat d'une compression."""
    
    def __init__(
        self,
        compressed_data: bytes,
        original_size: int,
        compressed_size: int,
        algorithm: CompressionAlgorithm,
        metadata: Dict[str, Any] = None
    ):
        self.compressed_data = compressed_data
        self.original_size = original_size
        self.compressed_size = compressed_size
        self.algorithm = algorithm
        self.metadata = metadata or {}
    
    @property
    def compression_ratio(self) -> float:
        """Ratio de compression (plus petit = meilleure compression)."""
        return self.compressed_size / self.original_size if self.original_size > 0 else 1.0
    
    @property
    def space_saved_percent(self) -> float:
        """Pourcentage d'espace économisé."""
        return (1 - self.compression_ratio) * 100
    
    @property
    def is_effective(self) -> bool:
        """True si la compression est efficace (> 10% d'économie)."""
        return self.space_saved_percent > 10.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "compression_ratio": self.compression_ratio,
            "space_saved_percent": self.space_saved_percent,
            "algorithm": self.algorithm.value,
            "is_effective": self.is_effective,
            "metadata": self.metadata,
        }


def compress_data(
    data: Union[str, bytes, dict],
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    level: int = 6
) -> CompressionResult:
    """
    Compresse des données avec l'algorithme spécifié.
    
    Args:
        data: Données à compresser
        algorithm: Algorithme de compression
        level: Niveau de compression (1-9, plus élevé = meilleure compression)
    
    Returns:
        CompressionResult: Résultat de la compression
    """
    # Préparer les données
    if isinstance(data, dict):
        original_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        data_type = "json"
    elif isinstance(data, str):
        original_data = data.encode('utf-8')
        data_type = "text"
    elif isinstance(data, bytes):
        original_data = data
        data_type = "bytes"
    else:
        # Sérialiser avec pickle pour les autres types
        original_data = pickle.dumps(data)
        data_type = "pickle"
    
    original_size = len(original_data)
    
    # Compresser selon l'algorithme
    try:
        if algorithm == CompressionAlgorithm.GZIP:
            compressed_data = gzip.compress(original_data, compresslevel=level)
        
        elif algorithm == CompressionAlgorithm.ZLIB:
            compressed_data = zlib.compress(original_data, level=level)
        
        elif algorithm == CompressionAlgorithm.LZ4:
            # LZ4 a ses propres niveaux (0-16)
            lz4_level = min(max(level - 3, 0), 16)  # Adapter le niveau
            compressed_data = lz4.frame.compress(original_data, compression_level=lz4_level)
        
        elif algorithm == CompressionAlgorithm.BROTLI:
            # Brotli niveau 0-11
            brotli_level = min(max(level - 1, 0), 11)
            compressed_data = brotli.compress(original_data, quality=brotli_level)
        
        else:
            raise ValueError(f"Algorithme non supporté: {algorithm}")
        
        compressed_size = len(compressed_data)
        
        return CompressionResult(
            compressed_data=compressed_data,
            original_size=original_size,
            compressed_size=compressed_size,
            algorithm=algorithm,
            metadata={
                "data_type": data_type,
                "compression_level": level,
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur compression {algorithm}: {e}")
        # Retourner les données non compressées en cas d'erreur
        return CompressionResult(
            compressed_data=original_data,
            original_size=original_size,
            compressed_size=original_size,
            algorithm=algorithm,
            metadata={"error": str(e), "data_type": data_type}
        )


def decompress_data(
    compressed_data: bytes,
    algorithm: CompressionAlgorithm,
    data_type: str = "bytes"
) -> Union[str, bytes, dict]:
    """
    Décompresse des données.
    
    Args:
        compressed_data: Données compressées
        algorithm: Algorithme utilisé pour la compression
        data_type: Type original des données
    
    Returns:
        Données décompressées dans leur format original
    """
    try:
        # Décompresser selon l'algorithme
        if algorithm == CompressionAlgorithm.GZIP:
            decompressed = gzip.decompress(compressed_data)
        
        elif algorithm == CompressionAlgorithm.ZLIB:
            decompressed = zlib.decompress(compressed_data)
        
        elif algorithm == CompressionAlgorithm.LZ4:
            decompressed = lz4.frame.decompress(compressed_data)
        
        elif algorithm == CompressionAlgorithm.BROTLI:
            decompressed = brotli.decompress(compressed_data)
        
        else:
            raise ValueError(f"Algorithme non supporté: {algorithm}")
        
        # Reconvertir selon le type original
        if data_type == "json":
            return json.loads(decompressed.decode('utf-8'))
        elif data_type == "text":
            return decompressed.decode('utf-8')
        elif data_type == "pickle":
            return pickle.loads(decompressed)
        else:
            return decompressed
            
    except Exception as e:
        logger.error(f"Erreur décompression {algorithm}: {e}")
        raise


def get_best_compression(
    data: Union[str, bytes, dict],
    algorithms: list[CompressionAlgorithm] = None,
    min_size_threshold: int = 1024
) -> CompressionResult:
    """
    Trouve le meilleur algorithme de compression pour des données.
    
    Args:
        data: Données à compresser
        algorithms: Liste des algorithmes à tester (None = tous)
        min_size_threshold: Taille minimum pour tenter la compression
    
    Returns:
        CompressionResult: Meilleur résultat de compression
    """
    if algorithms is None:
        algorithms = list(CompressionAlgorithm)
    
    # Vérifier si la compression vaut la peine
    data_size = len(str(data).encode('utf-8')) if not isinstance(data, bytes) else len(data)
    
    if data_size < min_size_threshold:
        logger.debug(f"Données trop petites pour compression: {data_size} < {min_size_threshold}")
        # Retourner sans compression
        original_data = data.encode('utf-8') if isinstance(data, str) else data
        return CompressionResult(
            compressed_data=original_data,
            original_size=data_size,
            compressed_size=data_size,
            algorithm=CompressionAlgorithm.GZIP,  # Par défaut
            metadata={"reason": "too_small", "threshold": min_size_threshold}
        )
    
    best_result = None
    results = []
    
    # Tester chaque algorithme
    for algorithm in algorithms:
        try:
            result = compress_data(data, algorithm)
            results.append(result)
            
            # Garder le meilleur (plus petit)
            if best_result is None or result.compressed_size < best_result.compressed_size:
                best_result = result
                
        except Exception as e:
            logger.warning(f"Échec compression {algorithm}: {e}")
            continue
    
    # Ajouter des métadonnées comparatives
    if best_result and results:
        best_result.metadata.update({
            "alternatives_tested": len(results),
            "algorithms_tested": [r.algorithm.value for r in results],
            "best_choice_reason": "smallest_size",
        })
    
    return best_result or CompressionResult(
        compressed_data=data.encode('utf-8') if isinstance(data, str) else data,
        original_size=data_size,
        compressed_size=data_size,
        algorithm=CompressionAlgorithm.GZIP,
        metadata={"error": "all_algorithms_failed"}
    )


def get_compression_ratio(original_size: int, compressed_size: int) -> float:
    """Calcule le ratio de compression."""
    return compressed_size / original_size if original_size > 0 else 1.0


def should_compress(
    data_size: int,
    min_size: int = 1024,
    max_size: int = 100 * 1024 * 1024  # 100MB
) -> bool:
    """
    Détermine si des données devraient être compressées.
    
    Args:
        data_size: Taille des données en bytes
        min_size: Taille minimum pour compression
        max_size: Taille maximum pour compression
    
    Returns:
        bool: True si la compression est recommandée
    """
    return min_size <= data_size <= max_size


class AdaptiveCompressor:
    """Compresseur adaptatif qui choisit automatiquement la meilleure stratégie."""
    
    def __init__(self):
        self.compression_stats = {
            algorithm.value: {
                "uses": 0,
                "total_original_size": 0,
                "total_compressed_size": 0,
                "avg_ratio": 1.0,
                "avg_time_ms": 0.0,
            }
            for algorithm in CompressionAlgorithm
        }
    
    def compress_adaptive(
        self,
        data: Union[str, bytes, dict],
        prefer_speed: bool = False,
        prefer_size: bool = False
    ) -> CompressionResult:
        """
        Compresse avec l'algorithme optimal selon les préférences.
        
        Args:
            data: Données à compresser
            prefer_speed: Privilégier la vitesse
            prefer_size: Privilégier la taille
        
        Returns:
            CompressionResult: Résultat optimal
        """
        import time
        
        data_size = len(str(data).encode('utf-8')) if not isinstance(data, bytes) else len(data)
        
        # Stratégie selon les préférences et la taille
        if prefer_speed or data_size > 10 * 1024 * 1024:  # > 10MB
            # Privilégier LZ4 pour la vitesse
            algorithm = CompressionAlgorithm.LZ4
            level = 3
        elif prefer_size or data_size < 100 * 1024:  # < 100KB
            # Privilégier Brotli pour la taille
            algorithm = CompressionAlgorithm.BROTLI
            level = 8
        else:
            # Équilibre avec GZIP
            algorithm = CompressionAlgorithm.GZIP
            level = 6
        
        # Compresser et mesurer le temps
        start_time = time.time()
        result = compress_data(data, algorithm, level)
        compression_time_ms = (time.time() - start_time) * 1000
        
        # Mettre à jour les statistiques
        stats = self.compression_stats[algorithm.value]
        stats["uses"] += 1
        stats["total_original_size"] += result.original_size
        stats["total_compressed_size"] += result.compressed_size
        stats["avg_ratio"] = stats["total_compressed_size"] / stats["total_original_size"]
        stats["avg_time_ms"] = (stats["avg_time_ms"] + compression_time_ms) / 2
        
        # Ajouter les métriques au résultat
        result.metadata.update({
            "compression_time_ms": compression_time_ms,
            "strategy": "speed" if prefer_speed else ("size" if prefer_size else "balanced"),
        })
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de compression."""
        return {
            "algorithms": self.compression_stats,
            "summary": {
                "total_uses": sum(stats["uses"] for stats in self.compression_stats.values()),
                "best_ratio_algorithm": min(
                    self.compression_stats.items(),
                    key=lambda x: x[1]["avg_ratio"] if x[1]["uses"] > 0 else 1.0
                )[0],
                "fastest_algorithm": min(
                    self.compression_stats.items(),
                    key=lambda x: x[1]["avg_time_ms"] if x[1]["uses"] > 0 else float('inf')
                )[0],
            }
        }


# Instance globale du compresseur adaptatif
adaptive_compressor = AdaptiveCompressor()