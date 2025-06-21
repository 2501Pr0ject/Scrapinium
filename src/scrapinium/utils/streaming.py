"""Traitement en streaming pour optimiser la mémoire."""

import asyncio
import io
from typing import AsyncGenerator, Optional, Union, Dict, Any
from dataclasses import dataclass
import gzip
import json

from ..config import get_logger

logger = get_logger("utils.streaming")


@dataclass
class StreamChunk:
    """Chunk de données en streaming."""
    data: bytes
    size: int
    chunk_id: int
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.size == 0:
            self.size = len(self.data)


class StreamingProcessor:
    """Processeur de contenu en streaming pour éviter la surcharge mémoire."""
    
    def __init__(self, chunk_size: int = 64 * 1024):  # 64KB par défaut
        self.chunk_size = chunk_size
        self.processed_bytes = 0
        self.total_chunks = 0
    
    async def process_content_stream(
        self, 
        content: Union[str, bytes], 
        max_size: Optional[int] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Traite le contenu par chunks pour éviter la surcharge mémoire.
        
        Args:
            content: Contenu à traiter
            max_size: Taille maximale à traiter (None = illimité)
        
        Yields:
            StreamChunk: Chunks de données
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        total_size = len(content)
        
        # Limiter la taille si spécifié
        if max_size and total_size > max_size:
            logger.warning(f"Contenu tronqué: {total_size} > {max_size} bytes")
            content = content[:max_size]
            total_size = max_size
        
        chunk_id = 0
        bytes_processed = 0
        
        # Traiter par chunks
        for i in range(0, total_size, self.chunk_size):
            chunk_data = content[i:i + self.chunk_size]
            bytes_processed += len(chunk_data)
            
            is_final = bytes_processed >= total_size
            
            chunk = StreamChunk(
                data=chunk_data,
                size=len(chunk_data),
                chunk_id=chunk_id,
                is_final=is_final,
                metadata={
                    "progress": bytes_processed / total_size,
                    "total_size": total_size,
                    "bytes_processed": bytes_processed,
                }
            )
            
            self.processed_bytes += len(chunk_data)
            self.total_chunks += 1
            chunk_id += 1
            
            yield chunk
            
            # Yielder le contrôle pour éviter de bloquer
            await asyncio.sleep(0)
    
    async def extract_text_streaming(
        self, 
        html_content: str, 
        max_size: int = 10 * 1024 * 1024
    ) -> AsyncGenerator[str, None]:
        """
        Extrait le texte d'un contenu HTML en streaming.
        
        Args:
            html_content: Contenu HTML à traiter
            max_size: Taille max en bytes
            
        Yields:
            str: Portions de texte extraites
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup non disponible pour l'extraction streaming")
            return
        
        # Traiter par chunks pour éviter de charger tout en mémoire
        async for chunk in self.process_content_stream(html_content, max_size):
            chunk_html = chunk.data.decode('utf-8', errors='ignore')
            
            try:
                # Parser avec BeautifulSoup (mode partiel)
                soup = BeautifulSoup(chunk_html, 'html.parser')
                
                # Extraire le texte
                text = soup.get_text(separator=' ', strip=True)
                
                if text.strip():
                    yield text
                    
            except Exception as e:
                logger.warning(f"Erreur extraction chunk {chunk.chunk_id}: {e}")
                continue
            
            # Yielder le contrôle
            await asyncio.sleep(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du processeur."""
        return {
            "processed_bytes": self.processed_bytes,
            "total_chunks": self.total_chunks,
            "avg_chunk_size": self.processed_bytes / self.total_chunks if self.total_chunks > 0 else 0,
            "chunk_size_setting": self.chunk_size,
        }


class ContentStreamer:
    """Gestionnaire de streaming de contenu avec compression."""
    
    def __init__(self, enable_compression: bool = True):
        self.enable_compression = enable_compression
        self.processor = StreamingProcessor()
    
    async def stream_large_content(
        self, 
        content: Union[str, bytes, Dict[str, Any]],
        content_type: str = "text",
        compress: bool = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Streame un contenu volumineux avec compression optionnelle.
        
        Args:
            content: Contenu à streamer
            content_type: Type de contenu (text, json, html)
            compress: Forcer la compression (None = auto)
        
        Yields:
            bytes: Chunks de données compressées/non-compressées
        """
        # Déterminer si on doit compresser
        should_compress = compress if compress is not None else self.enable_compression
        
        # Sérialiser selon le type
        if content_type == "json" and isinstance(content, dict):
            content_bytes = json.dumps(content, ensure_ascii=False).encode('utf-8')
        elif isinstance(content, str):
            content_bytes = content.encode('utf-8')
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            content_bytes = str(content).encode('utf-8')
        
        # Compression si activée et si le contenu est assez volumineux
        if should_compress and len(content_bytes) > 1024:  # > 1KB
            content_bytes = gzip.compress(content_bytes)
            logger.debug(f"Contenu compressé: {len(content_bytes)} bytes")
        
        # Streamer par chunks
        async for chunk in self.processor.process_content_stream(content_bytes):
            yield chunk.data
            
            # Yielder le contrôle
            await asyncio.sleep(0)
    
    async def collect_stream(self, stream: AsyncGenerator[bytes, None]) -> bytes:
        """Collecte un stream complet en mémoire (utiliser avec précaution)."""
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        return b''.join(chunks)
    
    async def stream_to_file(
        self, 
        stream: AsyncGenerator[bytes, None], 
        filepath: str
    ) -> int:
        """
        Écrit un stream directement dans un fichier.
        
        Args:
            stream: Stream de données
            filepath: Chemin du fichier de sortie
            
        Returns:
            int: Nombre de bytes écrits
        """
        bytes_written = 0
        
        try:
            with open(filepath, 'wb') as f:
                async for chunk in stream:
                    f.write(chunk)
                    bytes_written += len(chunk)
                    
                    # Yielder le contrôle après chaque chunk
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"Erreur écriture fichier {filepath}: {e}")
            raise
        
        logger.info(f"Stream écrit dans {filepath}: {bytes_written} bytes")
        return bytes_written
    
    async def stream_response(
        self,
        content: Any,
        content_type: str = "application/json",
        compress: bool = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Prépare un contenu pour réponse HTTP en streaming.
        
        Args:
            content: Contenu à streamer
            content_type: Type MIME du contenu
            compress: Compresser ou non
            
        Yields:
            bytes: Chunks prêts pour réponse HTTP
        """
        # Headers de streaming
        if content_type.startswith("application/json"):
            stream_type = "json"
        elif content_type.startswith("text/html"):
            stream_type = "html"
        else:
            stream_type = "text"
        
        # Streamer le contenu
        async for chunk in self.stream_large_content(
            content, 
            content_type=stream_type, 
            compress=compress
        ):
            yield chunk


class MemoryEfficientProcessor:
    """Processeur optimisé pour la mémoire avec streaming."""
    
    def __init__(self, max_memory_mb: float = 100.0):
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.streamer = ContentStreamer()
        self.current_usage = 0
    
    async def process_large_html(
        self, 
        html_content: str,
        extract_text: bool = True,
        extract_links: bool = True,
        max_content_size: int = None
    ) -> Dict[str, Any]:
        """
        Traite un HTML volumineux de manière efficace en mémoire.
        
        Args:
            html_content: Contenu HTML
            extract_text: Extraire le texte
            extract_links: Extraire les liens
            max_content_size: Taille max à traiter
            
        Returns:
            Dict avec les données extraites
        """
        max_size = max_content_size or self.max_memory_bytes
        
        result = {
            "text_content": "",
            "links": [],
            "metadata": {
                "original_size": len(html_content),
                "processed_size": 0,
                "truncated": False,
            }
        }
        
        # Vérifier si on doit tronquer
        if len(html_content) > max_size:
            logger.warning(f"HTML tronqué: {len(html_content)} > {max_size}")
            html_content = html_content[:max_size]
            result["metadata"]["truncated"] = True
        
        result["metadata"]["processed_size"] = len(html_content)
        
        try:
            from bs4 import BeautifulSoup
            
            # Parser avec limite mémoire
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraction de texte en streaming si demandé
            if extract_text:
                text_chunks = []
                processor = StreamingProcessor(chunk_size=32 * 1024)  # 32KB chunks
                
                async for text_chunk in processor.extract_text_streaming(html_content, max_size):
                    text_chunks.append(text_chunk)
                    
                    # Vérifier la mémoire
                    current_text_size = sum(len(chunk) for chunk in text_chunks)
                    if current_text_size > max_size // 2:  # Max 50% pour le texte
                        logger.warning("Limite mémoire texte atteinte")
                        break
                
                result["text_content"] = " ".join(text_chunks)
            
            # Extraction de liens (plus efficace)
            if extract_links:
                links = []
                for link in soup.find_all('a', href=True, limit=100):  # Limiter à 100 liens
                    links.append({
                        "href": link['href'],
                        "text": link.get_text(strip=True)[:100],  # Limiter le texte
                    })
                
                result["links"] = links
                
        except Exception as e:
            logger.error(f"Erreur traitement HTML efficace: {e}")
            # Fallback simple
            result["text_content"] = html_content[:10000]  # 10KB max en fallback
        
        return result
    
    async def compress_and_store(
        self, 
        data: Any, 
        storage_key: str,
        storage_backend: str = "memory"
    ) -> Dict[str, Any]:
        """
        Compresse et stocke des données de manière efficace.
        
        Args:
            data: Données à stocker
            storage_key: Clé de stockage
            storage_backend: Backend de stockage (memory, file, cache)
            
        Returns:
            Dict avec infos de stockage
        """
        # Sérialiser
        if isinstance(data, dict):
            serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
        else:
            serialized = str(data).encode('utf-8')
        
        original_size = len(serialized)
        
        # Compresser si > 1KB
        if original_size > 1024:
            compressed = gzip.compress(serialized)
            compression_ratio = len(compressed) / original_size
        else:
            compressed = serialized
            compression_ratio = 1.0
        
        storage_info = {
            "key": storage_key,
            "original_size": original_size,
            "compressed_size": len(compressed),
            "compression_ratio": compression_ratio,
            "backend": storage_backend,
            "compressed": compression_ratio < 1.0,
        }
        
        logger.debug(
            f"Données compressées: {original_size} -> {len(compressed)} bytes "
            f"(ratio: {compression_ratio:.2f})"
        )
        
        return storage_info