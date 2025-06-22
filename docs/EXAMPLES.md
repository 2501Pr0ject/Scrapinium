# Exemples d'Intégration - Scrapinium

## 🚀 SDK et Clients Officiels

Scrapinium fournit des SDKs officiels pour faciliter l'intégration dans vos applications.

## 🐍 Python SDK

### Installation

```bash
pip install scrapinium-sdk
```

### Client Python Basique

```python
from scrapinium import ScrapiniumClient
import asyncio

# Initialisation du client
client = ScrapiniumClient(
    api_url="http://localhost:8000",
    api_key="your-api-key",  # Optionnel pour l'instant
    timeout=30
)

async def main():
    # Scraping simple
    result = await client.scrape(
        url="https://example.com",
        output_format="markdown"
    )
    
    print(f"Status: {result.status}")
    print(f"Content: {result.content}")
    print(f"Execution time: {result.metadata.execution_time_ms}ms")

# Exécution
asyncio.run(main())
```

### Client Python Avancé

```python
import asyncio
from typing import List
from scrapinium import ScrapiniumClient, ScrapingRequest, TaskStatus

class AdvancedScrapingManager:
    """Gestionnaire avancé de scraping avec retry et monitoring."""
    
    def __init__(self, api_url: str, max_concurrent: int = 10):
        self.client = ScrapiniumClient(api_url)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = {}
    
    async def scrape_with_retry(
        self, 
        url: str, 
        max_retries: int = 3,
        use_llm: bool = False,
        custom_instructions: str = ""
    ) -> dict:
        """Scraping avec retry automatique."""
        
        for attempt in range(max_retries):
            try:
                async with self.semaphore:
                    result = await self.client.scrape(
                        url=url,
                        output_format="markdown",
                        use_llm=use_llm,
                        custom_instructions=custom_instructions,
                        priority="normal" if attempt == 0 else "high"
                    )
                    
                    if result.status == TaskStatus.COMPLETED:
                        return {
                            "success": True,
                            "data": result.content,
                            "metadata": result.metadata,
                            "attempts": attempt + 1
                        }
                        
            except Exception as e:
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": attempt + 1
                    }
                
                # Backoff exponential
                await asyncio.sleep(2 ** attempt)
        
        return {"success": False, "error": "Max retries exceeded"}
    
    async def scrape_multiple_urls(
        self, 
        urls: List[str],
        use_llm: bool = False,
        progress_callback=None
    ) -> List[dict]:
        """Scraping de plusieurs URLs en parallèle."""
        
        async def scrape_single_url(url: str, index: int) -> dict:
            result = await self.scrape_with_retry(url, use_llm=use_llm)
            
            if progress_callback:
                await progress_callback(index + 1, len(urls), url, result)
            
            return {"url": url, **result}
        
        # Lancer toutes les tâches en parallèle
        tasks = [
            scrape_single_url(url, i) 
            for i, url in enumerate(urls)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def monitor_task_progress(
        self, 
        task_id: str,
        polling_interval: float = 1.0,
        timeout: float = 300.0
    ) -> dict:
        """Surveiller le progrès d'une tâche avec timeout."""
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                status = await self.client.get_task_status(task_id)
                
                if status.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    return {
                        "task_id": task_id,
                        "final_status": status.status,
                        "result": status.result if status.status == TaskStatus.COMPLETED else None,
                        "error": status.error if status.status == TaskStatus.FAILED else None,
                        "total_time": asyncio.get_event_loop().time() - start_time
                    }
                
                # Vérifier timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    return {
                        "task_id": task_id,
                        "final_status": "timeout",
                        "error": f"Task timed out after {timeout}s"
                    }
                
                await asyncio.sleep(polling_interval)
                
            except Exception as e:
                return {
                    "task_id": task_id,
                    "final_status": "error",
                    "error": str(e)
                }

# Exemple d'usage
async def example_advanced_usage():
    manager = AdvancedScrapingManager("http://localhost:8000")
    
    # Progress callback
    async def progress_callback(current, total, url, result):
        print(f"Progress: {current}/{total} - {url} - {'✅' if result['success'] else '❌'}")
    
    # Scraper plusieurs URLs
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    results = await manager.scrape_multiple_urls(
        urls, 
        use_llm=True,
        progress_callback=progress_callback
    )
    
    # Analyser les résultats
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\n📊 Résultats:")
    print(f"✅ Succès: {len(successful)}")
    print(f"❌ Échecs: {len(failed)}")
    
    return results

# Exécution
if __name__ == "__main__":
    results = asyncio.run(example_advanced_usage())
```

### Client avec Cache Local

```python
import hashlib
import json
import aiofiles
from pathlib import Path
from scrapinium import ScrapiniumClient

class CachedScrapiniumClient:
    """Client Scrapinium avec cache local intelligent."""
    
    def __init__(self, api_url: str, cache_dir: str = "./scrapinium_cache"):
        self.client = ScrapiniumClient(api_url)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, url: str, options: dict) -> str:
        """Générer une clé de cache unique."""
        cache_data = {
            "url": url,
            "options": sorted(options.items())
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_from_cache(self, cache_key: str) -> dict:
        """Récupérer depuis le cache local."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    content = await f.read()
                    cached_data = json.loads(content)
                    
                    # Vérifier TTL
                    import time
                    if time.time() - cached_data.get("cached_at", 0) < 3600:  # 1h TTL
                        return cached_data["result"]
            except Exception:
                pass
        
        return None
    
    async def _save_to_cache(self, cache_key: str, result: dict):
        """Sauvegarder dans le cache local."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            import time
            cache_data = {
                "result": result,
                "cached_at": time.time()
            }
            
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
        except Exception as e:
            print(f"Warning: Could not save to cache: {e}")
    
    async def scrape_with_cache(
        self, 
        url: str,
        use_cache: bool = True,
        **kwargs
    ) -> dict:
        """Scraping avec cache local."""
        
        options = {
            "output_format": kwargs.get("output_format", "markdown"),
            "use_llm": kwargs.get("use_llm", False),
            "custom_instructions": kwargs.get("custom_instructions", "")
        }
        
        cache_key = self._get_cache_key(url, options)
        
        # Vérifier le cache local
        if use_cache:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                return {
                    **cached_result,
                    "from_cache": True,
                    "cache_type": "local"
                }
        
        # Scraping via API
        result = await self.client.scrape(url=url, **kwargs)
        
        # Sauvegarder en cache si succès
        if result.status == TaskStatus.COMPLETED:
            result_dict = {
                "success": True,
                "content": result.content,
                "metadata": result.metadata.__dict__,
                "from_cache": False
            }
            
            if use_cache:
                await self._save_to_cache(cache_key, result_dict)
            
            return result_dict
        else:
            return {
                "success": False,
                "error": result.error,
                "from_cache": False
            }

# Exemple d'usage avec cache
async def example_with_cache():
    client = CachedScrapiniumClient("http://localhost:8000")
    
    # Première requête (depuis l'API)
    result1 = await client.scrape_with_cache(
        "https://example.com",
        use_llm=True,
        custom_instructions="Extract main content"
    )
    print(f"First request - From cache: {result1.get('from_cache', False)}")
    
    # Deuxième requête (depuis le cache local)
    result2 = await client.scrape_with_cache(
        "https://example.com",
        use_llm=True,
        custom_instructions="Extract main content"
    )
    print(f"Second request - From cache: {result2.get('from_cache', False)}")
```

## 🌐 JavaScript/TypeScript SDK

### Installation

```bash
npm install scrapinium-sdk
# ou
yarn add scrapinium-sdk
```

### Client JavaScript

```javascript
// client.js
import { ScrapiniumClient } from 'scrapinium-sdk';

const client = new ScrapiniumClient({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your-api-key', // Optionnel
  timeout: 30000
});

// Scraping simple
async function simpleScraping() {
  try {
    const result = await client.scrape({
      url: 'https://example.com',
      outputFormat: 'markdown',
      useLlm: false
    });
    
    console.log('✅ Scraping completed:', result.content);
    return result;
  } catch (error) {
    console.error('❌ Scraping failed:', error.message);
    throw error;
  }
}

// Scraping avec monitoring
async function scrapingWithProgress() {
  const taskId = await client.createScrapingTask({
    url: 'https://example.com',
    outputFormat: 'markdown',
    useLlm: true,
    customInstructions: 'Extract main content and create a summary'
  });
  
  console.log(`📋 Task created: ${taskId}`);
  
  // Surveiller le progrès
  const result = await client.monitorTask(taskId, {
    onProgress: (progress) => {
      console.log(`📊 Progress: ${progress.percentage}% - ${progress.message}`);
    },
    onComplete: (result) => {
      console.log('✅ Task completed!');
    },
    onError: (error) => {
      console.error('❌ Task failed:', error);
    },
    pollingInterval: 1000,
    timeout: 300000
  });
  
  return result;
}

// Scraping batch
async function batchScraping() {
  const urls = [
    'https://example.com',
    'https://httpbin.org/html',
    'https://jsonplaceholder.typicode.com/posts/1'
  ];
  
  const batchManager = client.createBatchManager({
    concurrency: 5,
    retryAttempts: 3,
    retryDelay: 1000
  });
  
  const results = await batchManager.scrapeMultiple(urls, {
    outputFormat: 'markdown',
    useLlm: false,
    onProgress: (completed, total, currentUrl) => {
      console.log(`📊 Batch progress: ${completed}/${total} - Current: ${currentUrl}`);
    }
  });
  
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  
  console.log(`📊 Batch results: ${successful.length} successful, ${failed.length} failed`);
  
  return results;
}

// Export pour utilisation
export { 
  simpleScraping, 
  scrapingWithProgress, 
  batchScraping 
};
```

### Client TypeScript Avancé

```typescript
// advanced-client.ts
import { 
  ScrapiniumClient, 
  ScrapingRequest, 
  ScrapingResult, 
  TaskStatus,
  ApiError 
} from 'scrapinium-sdk';

interface ScrapingOptions {
  retryAttempts?: number;
  retryDelay?: number;
  cache?: boolean;
  timeout?: number;
}

interface BatchResult<T> {
  successful: T[];
  failed: Array<{ url: string; error: string }>;
  summary: {
    total: number;
    successRate: number;
    totalTime: number;
  };
}

class AdvancedScrapiniumClient {
  private client: ScrapiniumClient;
  private defaultOptions: ScrapingOptions;
  
  constructor(apiUrl: string, options: ScrapingOptions = {}) {
    this.client = new ScrapiniumClient({ apiUrl });
    this.defaultOptions = {
      retryAttempts: 3,
      retryDelay: 1000,
      cache: true,
      timeout: 30000,
      ...options
    };
  }
  
  async scrapeWithRetry(
    request: ScrapingRequest,
    options: ScrapingOptions = {}
  ): Promise<ScrapingResult> {
    const mergedOptions = { ...this.defaultOptions, ...options };
    let lastError: Error | null = null;
    
    for (let attempt = 1; attempt <= mergedOptions.retryAttempts!; attempt++) {
      try {
        const result = await this.client.scrape({
          ...request,
          priority: attempt > 1 ? 'high' : 'normal'
        });
        
        if (result.status === TaskStatus.COMPLETED) {
          return result;
        }
        
        if (result.status === TaskStatus.FAILED) {
          throw new Error(result.error || 'Scraping failed');
        }
        
      } catch (error) {
        lastError = error as Error;
        
        if (attempt < mergedOptions.retryAttempts!) {
          const delay = mergedOptions.retryDelay! * Math.pow(2, attempt - 1);
          console.warn(`⚠️  Attempt ${attempt} failed, retrying in ${delay}ms...`);
          await this.sleep(delay);
        }
      }
    }
    
    throw new ApiError(
      `Scraping failed after ${mergedOptions.retryAttempts} attempts: ${lastError?.message}`
    );
  }
  
  async scrapeMultipleWithProgress<T = ScrapingResult>(
    urls: string[],
    requestTemplate: Partial<ScrapingRequest> = {},
    onProgress?: (completed: number, total: number, currentUrl: string, result?: T) => void
  ): Promise<BatchResult<T>> {
    const startTime = Date.now();
    const successful: T[] = [];
    const failed: Array<{ url: string; error: string }> = [];
    
    const promises = urls.map(async (url, index) => {
      try {
        const request: ScrapingRequest = {
          url,
          outputFormat: 'markdown',
          useLlm: false,
          ...requestTemplate
        };
        
        const result = await this.scrapeWithRetry(request) as T;
        successful.push(result);
        
        if (onProgress) {
          onProgress(successful.length + failed.length, urls.length, url, result);
        }
        
        return { success: true, result };
        
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        failed.push({ url, error: errorMsg });
        
        if (onProgress) {
          onProgress(successful.length + failed.length, urls.length, url);
        }
        
        return { success: false, error: errorMsg };
      }
    });
    
    await Promise.all(promises);
    
    const totalTime = Date.now() - startTime;
    
    return {
      successful,
      failed,
      summary: {
        total: urls.length,
        successRate: (successful.length / urls.length) * 100,
        totalTime
      }
    };
  }
  
  async getPerformanceStats(): Promise<any> {
    return await this.client.getStats();
  }
  
  async getSystemHealth(): Promise<any> {
    return await this.client.healthCheck();
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Exemple d'utilisation
async function exampleAdvancedUsage() {
  const client = new AdvancedScrapiniumClient('http://localhost:8000', {
    retryAttempts: 5,
    retryDelay: 2000,
    cache: true
  });
  
  // Scraping simple avec retry
  try {
    const result = await client.scrapeWithRetry({
      url: 'https://example.com',
      outputFormat: 'markdown',
      useLlm: true,
      customInstructions: 'Extract and summarize main content'
    });
    
    console.log('✅ Scraping successful:', result.content);
  } catch (error) {
    console.error('❌ Scraping failed:', error.message);
  }
  
  // Batch scraping avec progress
  const urls = [
    'https://example.com',
    'https://httpbin.org/html',
    'https://jsonplaceholder.typicode.com/posts/1'
  ];
  
  const batchResult = await client.scrapeMultipleWithProgress(
    urls,
    { 
      outputFormat: 'json',
      useLlm: false 
    },
    (completed, total, currentUrl, result) => {
      const percentage = Math.round((completed / total) * 100);
      console.log(`📊 Progress: ${percentage}% (${completed}/${total}) - ${currentUrl}`);
      
      if (result) {
        console.log(`   ✅ Success: ${result.metadata?.executionTimeMs}ms`);
      }
    }
  );
  
  console.log(`\n📈 Batch Summary:`);
  console.log(`   Total URLs: ${batchResult.summary.total}`);
  console.log(`   Success Rate: ${batchResult.summary.successRate.toFixed(1)}%`);
  console.log(`   Total Time: ${batchResult.summary.totalTime}ms`);
  console.log(`   Failed URLs:`, batchResult.failed.map(f => f.url));
}

export { AdvancedScrapiniumClient, exampleAdvancedUsage };
```

## 🐹 Go Client

```go
// client.go
package main

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

type ScrapiniumClient struct {
    BaseURL    string
    HTTPClient *http.Client
    APIKey     string
}

type ScrapingRequest struct {
    URL                string `json:"url"`
    OutputFormat       string `json:"output_format"`
    UseLLM            bool   `json:"use_llm"`
    CustomInstructions string `json:"custom_instructions,omitempty"`
    UseCache          bool   `json:"use_cache"`
    Priority          string `json:"priority"`
}

type ScrapingResponse struct {
    Success bool `json:"success"`
    Data    struct {
        TaskID string `json:"task_id"`
        Status string `json:"status"`
    } `json:"data"`
    Message   string    `json:"message"`
    Timestamp time.Time `json:"timestamp"`
}

type TaskResult struct {
    Success bool `json:"success"`
    Data    struct {
        ID        string `json:"id"`
        URL       string `json:"url"`
        Status    string `json:"status"`
        Progress  int    `json:"progress"`
        Result    string `json:"result"`
        Metadata  struct {
            ExecutionTimeMS int     `json:"execution_time_ms"`
            TokensUsed      *int    `json:"tokens_used"`
            ContentLength   int     `json:"content_length"`
            WordCount       int     `json:"word_count"`
            CacheHit        bool    `json:"cache_hit"`
            BrowserUsed     string  `json:"browser_used"`
            LLMProvider     *string `json:"llm_provider"`
        } `json:"metadata"`
        CreatedAt   time.Time  `json:"created_at"`
        CompletedAt *time.Time `json:"completed_at"`
    } `json:"data"`
}

func NewScrapiniumClient(baseURL string) *ScrapiniumClient {
    return &ScrapiniumClient{
        BaseURL: baseURL,
        HTTPClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *ScrapiniumClient) Scrape(ctx context.Context, req ScrapingRequest) (*TaskResult, error) {
    // Créer la tâche
    taskResp, err := c.createTask(ctx, req)
    if err != nil {
        return nil, fmt.Errorf("failed to create task: %w", err)
    }
    
    // Surveiller jusqu'à completion
    return c.waitForCompletion(ctx, taskResp.Data.TaskID, 5*time.Minute)
}

func (c *ScrapiniumClient) createTask(ctx context.Context, req ScrapingRequest) (*ScrapingResponse, error) {
    jsonData, err := json.Marshal(req)
    if err != nil {
        return nil, err
    }
    
    httpReq, err := http.NewRequestWithContext(
        ctx, 
        "POST", 
        c.BaseURL+"/scrape", 
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, err
    }
    
    httpReq.Header.Set("Content-Type", "application/json")
    if c.APIKey != "" {
        httpReq.Header.Set("Authorization", "Bearer "+c.APIKey)
    }
    
    resp, err := c.HTTPClient.Do(httpReq)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var scrapingResp ScrapingResponse
    if err := json.NewDecoder(resp.Body).Decode(&scrapingResp); err != nil {
        return nil, err
    }
    
    if !scrapingResp.Success {
        return nil, fmt.Errorf("API error: %s", scrapingResp.Message)
    }
    
    return &scrapingResp, nil
}

func (c *ScrapiniumClient) waitForCompletion(ctx context.Context, taskID string, timeout time.Duration) (*TaskResult, error) {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()
    
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return nil, ctx.Err()
        case <-ticker.C:
            result, err := c.getTaskStatus(ctx, taskID)
            if err != nil {
                return nil, err
            }
            
            switch result.Data.Status {
            case "completed":
                return result, nil
            case "failed":
                return nil, fmt.Errorf("task failed")
            }
            // Continue polling for other statuses
        }
    }
}

func (c *ScrapiniumClient) getTaskStatus(ctx context.Context, taskID string) (*TaskResult, error) {
    req, err := http.NewRequestWithContext(
        ctx,
        "GET",
        c.BaseURL+"/scrape/"+taskID,
        nil,
    )
    if err != nil {
        return nil, err
    }
    
    if c.APIKey != "" {
        req.Header.Set("Authorization", "Bearer "+c.APIKey)
    }
    
    resp, err := c.HTTPClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result TaskResult
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return &result, nil
}

// Exemple d'utilisation
func main() {
    client := NewScrapiniumClient("http://localhost:8000")
    
    ctx := context.Background()
    
    result, err := client.Scrape(ctx, ScrapingRequest{
        URL:                "https://example.com",
        OutputFormat:       "markdown",
        UseLLM:            true,
        CustomInstructions: "Extract main content and create summary",
        UseCache:          true,
        Priority:          "normal",
    })
    
    if err != nil {
        fmt.Printf("❌ Scraping failed: %v\n", err)
        return
    }
    
    fmt.Printf("✅ Scraping completed!\n")
    fmt.Printf("📄 Content length: %d chars\n", result.Data.Metadata.ContentLength)
    fmt.Printf("⏱️  Execution time: %dms\n", result.Data.Metadata.ExecutionTimeMS)
    fmt.Printf("💾 Cache hit: %t\n", result.Data.Metadata.CacheHit)
    fmt.Printf("📝 Content preview: %.100s...\n", result.Data.Result)
}
```

## 🐳 Docker Integration

### Docker Compose pour Développement

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  scrapinium-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - DATABASE_URL=sqlite:///./scrapinium.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./src:/app/src
      - ./templates:/app/templates
    depends_on:
      - redis
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  # Client exemple en Python
  scraping-client:
    build: 
      context: .
      dockerfile: Dockerfile.client
    environment:
      - SCRAPINIUM_API_URL=http://scrapinium-api:8000
    volumes:
      - ./examples:/app/examples
    depends_on:
      - scrapinium-api
    command: python examples/batch_scraping.py
```

### Dockerfile pour Client

```dockerfile
# Dockerfile.client
FROM python:3.9-slim

WORKDIR /app

COPY requirements-client.txt .
RUN pip install -r requirements-client.txt

COPY examples/ ./examples/
COPY client-sdk/ ./client-sdk/

ENV PYTHONPATH=/app/client-sdk

CMD ["python", "examples/interactive_client.py"]
```

## 🌐 Exemples d'Intégration Web

### Integration React

```jsx
// ScrapiniumHook.js
import { useState, useCallback } from 'react';
import { ScrapiniumClient } from 'scrapinium-sdk';

export const useScrapinium = (apiUrl = 'http://localhost:8000') => {
  const [client] = useState(() => new ScrapiniumClient({ apiUrl }));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const scrape = useCallback(async (request) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await client.scrape(request);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [client]);
  
  const scrapeWithProgress = useCallback(async (request, onProgress) => {
    setLoading(true);
    setError(null);
    
    try {
      const taskId = await client.createScrapingTask(request);
      
      return await client.monitorTask(taskId, {
        onProgress,
        pollingInterval: 1000
      });
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [client]);
  
  return {
    scrape,
    scrapeWithProgress,
    loading,
    error,
    client
  };
};

// ScrapingForm.jsx
import React, { useState } from 'react';
import { useScrapinium } from './ScrapiniumHook';

export const ScrapingForm = () => {
  const { scrape, scrapeWithProgress, loading, error } = useScrapinium();
  const [url, setUrl] = useState('');
  const [useLlm, setUseLlm] = useState(false);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const result = await scrapeWithProgress(
        {
          url,
          outputFormat: 'markdown',
          useLlm,
          customInstructions: useLlm ? 'Extract and summarize main content' : ''
        },
        (progressData) => {
          setProgress(progressData.progress);
        }
      );
      
      setResult(result);
    } catch (err) {
      console.error('Scraping failed:', err);
    }
  };
  
  return (
    <div className="scraping-form">
      <form onSubmit={handleSubmit}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL to scrape..."
          required
        />
        
        <label>
          <input
            type="checkbox"
            checked={useLlm}
            onChange={(e) => setUseLlm(e.target.checked)}
          />
          Use LLM Processing
        </label>
        
        <button type="submit" disabled={loading}>
          {loading ? `Scraping... ${progress}%` : 'Scrape URL'}
        </button>
      </form>
      
      {error && <div className="error">Error: {error}</div>}
      {result && <div className="result">{result.structured_content}</div>}
    </div>
  );
};
```

## 🧠 Exemples Machine Learning API

### Analyse ML Complète

```python
import asyncio
import httpx
from scrapinium import ScrapiniumClient

async def example_ml_analysis():
    """Exemple d'utilisation complète du pipeline ML."""
    
    client = ScrapiniumClient("http://localhost:8000")
    
    # Scraper une page et obtenir l'analyse ML automatique
    result = await client.scrape(
        url="https://techblog.example.com/ai-article",
        output_format="markdown",
        use_llm=True
    )
    
    # Les métadonnées contiennent l'analyse ML automatique
    ml_data = result.metadata.get('ml_analysis')
    if ml_data:
        print("🧠 Analyse ML automatique:")
        print(f"   Type: {ml_data['classification']['page_type']}")
        print(f"   Qualité: {ml_data['classification']['quality']}")
        print(f"   Langue: {ml_data['classification']['language']}")
        print(f"   Défis anti-bot: {len(ml_data['bot_detection']['challenges'])}")
        print(f"   Mots: {ml_data['content_metrics']['word_count']}")
        print(f"   Lisibilité: {ml_data['content_metrics']['readability_score']}")
    
    # Analyse ML séparée pour plus de détails
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            "http://localhost:8000/ml/analyze",
            json={
                "html": result.raw_html,  # HTML complet
                "url": result.url,
                "headers": result.response_headers,
                "metadata": {"source": "manual_analysis"}
            }
        )
        
        detailed_ml = response.json()["data"]
        
        print("\n🔍 Analyse ML détaillée:")
        print(f"   Confiance globale: {detailed_ml['metrics']['confidence_score']:.3f}")
        print(f"   Temps traitement: {detailed_ml['metrics']['processing_time']:.3f}s")
        print(f"   Topics: {detailed_ml['content_analysis']['topics']}")
        print(f"   Keywords: {detailed_ml['content_analysis']['keywords'][:5]}")
        
        if detailed_ml['bot_detection']['challenges']:
            print(f"   ⚠️ Défis détectés: {detailed_ml['bot_detection']['challenges']}")
            print(f"   📋 Recommandations: {detailed_ml['recommendations']}")

# Exécuter l'exemple
asyncio.run(example_ml_analysis())
```

### Classification de Contenu

```python
async def classify_multiple_urls():
    """Classifier plusieurs URLs pour analyser un site web."""
    
    urls = [
        "https://shop.example.com/products/laptop",
        "https://shop.example.com/blog/tech-review", 
        "https://shop.example.com/support/documentation",
        "https://shop.example.com/about-us"
    ]
    
    classifications = []
    
    async with httpx.AsyncClient() as client:
        for url in urls:
            # Obtenir le HTML (simulation)
            html_response = await client.get(url)
            
            # Classifier le contenu
            ml_response = await client.post(
                "http://localhost:8000/ml/classify",
                json={
                    "html": html_response.text,
                    "url": url
                }
            )
            
            classification = ml_response.json()["data"]
            classifications.append({
                "url": url,
                "type": classification["page_type"],
                "quality": classification["quality"],
                "confidence": classification["confidence"],
                "language": classification["language"]
            })
    
    # Analyser les résultats
    print("📊 Classification du site web:")
    for item in classifications:
        print(f"   {item['type'].upper():12} | {item['quality']:6} | {item['confidence']:.2f} | {item['url']}")
    
    # Statistiques du site
    page_types = [item['type'] for item in classifications]
    print(f"\n📈 Distribution des types de pages:")
    from collections import Counter
    for page_type, count in Counter(page_types).items():
        print(f"   {page_type}: {count}")

asyncio.run(classify_multiple_urls())
```

### Détection Anti-Bot et Stratégies

```python
async def analyze_antibot_protection():
    """Analyser les protections anti-bot d'un site."""
    
    target_urls = [
        "https://protected-site.example.com",
        "https://ecommerce-with-cloudflare.com", 
        "https://news-site-with-captcha.com"
    ]
    
    async with httpx.AsyncClient() as client:
        for url in target_urls:
            try:
                # Requête initiale
                response = await client.get(url)
                
                # Analyser les défis anti-bot
                bot_analysis = await client.post(
                    "http://localhost:8000/ml/detect-bot",
                    json={
                        "html": response.text,
                        "url": url,
                        "headers": dict(response.headers),
                        "response_time": response.elapsed.total_seconds()
                    }
                )
                
                bot_data = bot_analysis.json()["data"]
                
                print(f"\n🛡️ Analyse de {url}:")
                print(f"   Défis détectés: {bot_data['challenges']}")
                print(f"   Confiance: {bot_data['confidence']:.2f}")
                print(f"   Stratégies recommandées: {bot_data['strategies']}")
                
                if bot_data['warnings']:
                    print(f"   ⚠️ Alertes: {bot_data['warnings']}")
                
                # Configuration furtive recommandée
                stealth = bot_data['stealth_config']
                print(f"   🥷 User-Agent recommandé: {stealth['user_agent'][:50]}...")
                print(f"   ⏱️ Délai recommandé: {stealth['delays']['base_delay']}s")
                
                # Délais spécialisés
                delays = bot_data['recommended_delays']
                print(f"   📚 Délais lecture: {delays['reading'][0]:.1f}-{delays['reading'][1]:.1f}s")
                print(f"   🖱️ Délais clic: {delays['clicking'][0]:.1f}-{delays['clicking'][1]:.1f}s")
                
            except Exception as e:
                print(f"❌ Erreur pour {url}: {e}")

asyncio.run(analyze_antibot_protection())
```

### Monitoring Pipeline ML

```python
async def monitor_ml_pipeline():
    """Monitorer les performances du pipeline ML."""
    
    async with httpx.AsyncClient() as client:
        # Statistiques générales
        stats_response = await client.get("http://localhost:8000/ml/stats")
        stats = stats_response.json()["data"]
        
        print("📊 Statistiques Pipeline ML:")
        print(f"   Total analyses: {stats['total_analyses']}")
        print(f"   Temps moyen: {stats['avg_processing_time']:.3f}s")
        print(f"   Taux de succès: {stats['success_rate']:.1%}")
        print(f"   Score confiance moyen: {stats['avg_confidence_score']:.3f}")
        
        # Distribution des types de pages
        print(f"\n📈 Types de pages analysées:")
        for page_type, count in stats['page_types_distribution'].items():
            print(f"   {page_type}: {count}")
        
        # Fréquence détection anti-bot
        bot_freq = stats['bot_detection_frequency']
        print(f"\n🛡️ Détection anti-bot:")
        print(f"   Pages avec défis: {bot_freq['pages_with_challenges']}")
        print(f"   Défis moyens/page: {bot_freq['avg_challenges_per_page']:.1f}")
        
        # Statistiques du cache
        cache_response = await client.get("http://localhost:8000/ml/cache/stats")
        cache = cache_response.json()["data"]
        
        print(f"\n💾 Cache ML:")
        print(f"   Entrées actives: {cache['total_entries']}")
        print(f"   Hit rate: {cache['hit_rate_percent']:.1f}%")
        print(f"   Entrées expirées: {cache['expired_entries']}")
        
        # Optimiser le cache si nécessaire
        if cache['expired_entries'] > 50:
            optimize_response = await client.post("http://localhost:8000/ml/cache/optimize")
            optimize_data = optimize_response.json()["data"]
            print(f"   🧹 Cache optimisé: {optimize_data['removed_entries']} entrées supprimées")

asyncio.run(monitor_ml_pipeline())
```

### Intégration Workflow Personnalisé

```python
class IntelligentScraper:
    """Scraper intelligent utilisant le pipeline ML pour s'adapter."""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.session = httpx.AsyncClient()
    
    async def smart_scrape(self, url: str, adaptive=True):
        """Scraping intelligent avec adaptation basée sur l'analyse ML."""
        
        # 1. Analyse préliminaire ML
        if adaptive:
            preliminary_response = await self.session.get(url)
            
            ml_analysis = await self.session.post(
                f"{self.api_url}/ml/analyze",
                json={
                    "html": preliminary_response.text[:5000],  # Preview
                    "url": url,
                    "headers": dict(preliminary_response.headers)
                }
            )
            
            ml_data = ml_analysis.json()["data"]
            
            print(f"🧠 Page détectée comme: {ml_data['classification']['page_type']}")
            print(f"   Qualité: {ml_data['classification']['quality']}")
            print(f"   Défis anti-bot: {len(ml_data['bot_detection']['challenges'])}")
            
            # Adapter la stratégie selon l'analyse ML
            scraping_config = ml_data['scraping_config']
            
            # Configuration adaptative
            use_stealth = len(ml_data['bot_detection']['challenges']) > 0
            delay_factor = 1.0
            
            if use_stealth:
                delay_factor = scraping_config['performance_settings']['request_delay']
                print(f"   🥷 Mode furtif activé avec délai {delay_factor}s")
            
            # Stratégie d'extraction adaptée
            extraction_strategy = scraping_config['extraction_strategy']
            print(f"   🎯 Stratégie: {extraction_strategy}")
        
        # 2. Scraping principal adaptatif
        scraping_request = {
            "url": url,
            "output_format": "markdown",
            "use_llm": True,
            "custom_instructions": self._get_adaptive_instructions(ml_data if adaptive else None)
        }
        
        if adaptive and use_stealth:
            await asyncio.sleep(delay_factor)  # Délai adaptatif
        
        scrape_response = await self.session.post(
            f"{self.api_url}/scrape",
            json=scraping_request
        )
        
        task_data = scrape_response.json()["data"]
        task_id = task_data["task_id"]
        
        # 3. Monitoring avec progression
        result = await self._monitor_task(task_id)
        
        # 4. Post-traitement basé sur l'analyse ML
        if adaptive and result and result.metadata.get('ml_analysis'):
            ml_metadata = result.metadata['ml_analysis']
            print(f"   ✅ Scraping terminé - Qualité finale: {ml_metadata['classification']['quality']}")
            print(f"   📊 {ml_metadata['content_metrics']['word_count']} mots extraits")
        
        return result
    
    def _get_adaptive_instructions(self, ml_data):
        """Instructions LLM adaptées selon le type de contenu détecté."""
        if not ml_data:
            return "Extract main content and structure it clearly"
        
        page_type = ml_data['classification']['page_type']
        
        instructions = {
            'article': "Extract title, author, date, main content and key points. Summarize in structured format.",
            'ecommerce': "Extract product name, price, description, specifications and reviews. Structure as product sheet.",
            'blog': "Extract blog post title, author, date, content and tags. Include related posts if available.",
            'news': "Extract headline, author, publication date, article content and category.",
            'documentation': "Extract documentation structure, code examples, and technical details in organized format.",
            'forum': "Extract discussion title, participants, main topics and key responses."
        }
        
        return instructions.get(page_type, "Extract and structure the main content appropriately")
    
    async def _monitor_task(self, task_id):
        """Monitoring de tâche avec progression."""
        while True:
            status_response = await self.session.get(f"{self.api_url}/scrape/{task_id}")
            status_data = status_response.json()["data"]
            
            print(f"   📊 {status_data['status']}: {status_data['progress']}% - {status_data['message']}")
            
            if status_data['status'] in ['completed', 'failed']:
                if status_data['status'] == 'completed':
                    return status_data
                else:
                    raise Exception(f"Scraping failed: {status_data.get('error', 'Unknown error')}")
            
            await asyncio.sleep(2)

# Exemple d'utilisation
async def demo_intelligent_scraper():
    scraper = IntelligentScraper()
    
    urls = [
        "https://techcrunch.com/latest-ai-news",  # News
        "https://amazon.com/product/laptop",       # E-commerce
        "https://dev.to/python-tutorial",         # Article/Blog
        "https://docs.python.org/asyncio"         # Documentation
    ]
    
    for url in urls:
        print(f"\n🔍 Scraping intelligent de: {url}")
        try:
            result = await scraper.smart_scrape(url, adaptive=True)
            print(f"   ✅ Succès - {len(result.structured_content)} caractères extraits")
        except Exception as e:
            print(f"   ❌ Échec: {e}")

asyncio.run(demo_intelligent_scraper())
          setProgress(progressData.percentage);
        }
      );
      
      setResult(result);
      setProgress(100);
    } catch (err) {
      console.error('Scraping failed:', err);
    }
  };
  
  return (
    <div className="scraping-form">
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="url">URL to scrape:</label>
          <input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            placeholder="https://example.com"
          />
        </div>
        
        <div>
          <label>
            <input
              type="checkbox"
              checked={useLlm}
              onChange={(e) => setUseLlm(e.target.checked)}
            />
            Use LLM for content processing
          </label>
        </div>
        
        <button type="submit" disabled={loading || !url}>
          {loading ? 'Scraping...' : 'Start Scraping'}
        </button>
      </form>
      
      {loading && (
        <div className="progress">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
          <span>{progress}%</span>
        </div>
      )}
      
      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}
      
      {result && (
        <div className="result">
          <h3>Result:</h3>
          <pre>{result.content}</pre>
          <div className="metadata">
            <p>Execution time: {result.metadata.executionTimeMs}ms</p>
            <p>Word count: {result.metadata.wordCount}</p>
            <p>Cache hit: {result.metadata.cacheHit ? 'Yes' : 'No'}</p>
          </div>
        </div>
      )}
    </div>
  );
};
```

### Integration Vue.js

```vue
<!-- ScrapingComponent.vue -->
<template>
  <div class="scraping-component">
    <form @submit.prevent="handleScrape">
      <div class="form-group">
        <label for="url">URL:</label>
        <input
          id="url"
          v-model="form.url"
          type="url"
          required
          placeholder="https://example.com"
          :disabled="loading"
        />
      </div>
      
      <div class="form-group">
        <label>
          <input
            v-model="form.useLlm"
            type="checkbox"
            :disabled="loading"
          />
          Use LLM processing
        </label>
      </div>
      
      <div class="form-group" v-if="form.useLlm">
        <label for="instructions">Custom Instructions:</label>
        <textarea
          id="instructions"
          v-model="form.customInstructions"
          placeholder="Extract main content and create a summary"
          :disabled="loading"
        />
      </div>
      
      <button type="submit" :disabled="loading || !form.url">
        {{ loading ? 'Scraping...' : 'Start Scraping' }}
      </button>
    </form>
    
    <div v-if="loading" class="progress-section">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: progress + '%' }"
        />
      </div>
      <p>{{ progressMessage }}</p>
    </div>
    
    <div v-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-if="result" class="result">
      <h3>Scraping Result</h3>
      <div class="result-content">
        <pre>{{ result.content }}</pre>
      </div>
      <div class="result-metadata">
        <h4>Metadata</h4>
        <ul>
          <li>Execution time: {{ result.metadata.executionTimeMs }}ms</li>
          <li>Word count: {{ result.metadata.wordCount }}</li>
          <li>Cache hit: {{ result.metadata.cacheHit ? 'Yes' : 'No' }}</li>
          <li>Browser: {{ result.metadata.browserUsed }}</li>
          <li v-if="result.metadata.llmProvider">
            LLM Provider: {{ result.metadata.llmProvider }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ScrapiniumClient } from 'scrapinium-sdk';

export default {
  name: 'ScrapingComponent',
  
  data() {
    return {
      client: new ScrapiniumClient({
        apiUrl: process.env.VUE_APP_SCRAPINIUM_API_URL || 'http://localhost:8000'
      }),
      form: {
        url: '',
        useLlm: false,
        customInstructions: ''
      },
      loading: false,
      progress: 0,
      progressMessage: '',
      error: null,
      result: null
    };
  },
  
  methods: {
    async handleScrape() {
      this.loading = true;
      this.error = null;
      this.result = null;
      this.progress = 0;
      
      try {
        const taskId = await this.client.createScrapingTask({
          url: this.form.url,
          outputFormat: 'markdown',
          useLlm: this.form.useLlm,
          customInstructions: this.form.customInstructions
        });
        
        const result = await this.client.monitorTask(taskId, {
          onProgress: (progressData) => {
            this.progress = progressData.percentage;
            this.progressMessage = progressData.message;
          },
          pollingInterval: 1000,
          timeout: 300000
        });
        
        this.result = result;
        this.progress = 100;
        this.progressMessage = 'Completed successfully!';
        
      } catch (err) {
        this.error = err.message;
        console.error('Scraping failed:', err);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.scraping-component {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input[type="url"],
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group textarea {
  height: 80px;
  resize: vertical;
}

button {
  background-color: #007bff;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.progress-section {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #28a745;
  transition: width 0.3s ease;
}

.error {
  color: #dc3545;
  background-color: #f8d7da;
  padding: 10px;
  border-radius: 4px;
  margin: 20px 0;
}

.result {
  margin-top: 20px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 20px;
}

.result-content pre {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
}

.result-metadata ul {
  list-style-type: none;
  padding: 0;
}

.result-metadata li {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}
</style>
```

## ⚡ Exemples Performance

### Client avec Pool de Connexions

```python
# high_performance_client.py
import asyncio
import aiohttp
from typing import List, Dict, Any
from dataclasses import dataclass
import time

@dataclass
class PerformanceMetrics:
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    throughput_per_second: float

class HighPerformanceScrapiniumClient:
    """Client haute performance avec pool de connexions."""
    
    def __init__(
        self, 
        api_url: str,
        max_connections: int = 100,
        max_connections_per_host: int = 30,
        timeout: float = 30.0
    ):
        self.api_url = api_url.rstrip('/')
        
        # Configuration du connecteur pour haute performance
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ttl_dns_cache=300,
        )
        
        # Timeout configuration
        timeout_config = aiohttp.ClientTimeout(
            total=timeout,
            connect=10,
            sock_read=timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Scrapinium-HighPerf-Client/1.0'
            }
        )
        
        self.metrics = {
            'requests': [],
            'start_time': time.time()
        }
    
    async def scrape_batch_optimized(
        self,
        urls: List[str],
        max_concurrent: int = 50,
        request_template: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Scraping batch optimisé avec limitation de concurrence."""
        
        if request_template is None:
            request_template = {
                'output_format': 'markdown',
                'use_llm': False,
                'use_cache': True
            }
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def scrape_single_url(url: str) -> Dict[str, Any]:
            async with semaphore:
                start_time = time.time()
                
                try:
                    # Créer la tâche
                    task_response = await self._create_task({
                        'url': url,
                        **request_template
                    })
                    
                    if not task_response.get('success'):
                        raise Exception(f"Failed to create task: {task_response.get('message')}")
                    
                    task_id = task_response['data']['task_id']
                    
                    # Attendre la completion avec polling optimisé
                    result = await self._wait_for_completion_optimized(task_id)
                    
                    response_time = time.time() - start_time
                    self.metrics['requests'].append({
                        'url': url,
                        'success': True,
                        'response_time': response_time
                    })
                    
                    return {
                        'url': url,
                        'success': True,
                        'result': result,
                        'response_time': response_time
                    }
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    self.metrics['requests'].append({
                        'url': url,
                        'success': False,
                        'response_time': response_time
                    })
                    
                    return {
                        'url': url,
                        'success': False,
                        'error': str(e),
                        'response_time': response_time
                    }
        
        # Exécuter toutes les tâches en parallèle
        tasks = [scrape_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'response_time': 0
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _create_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer une tâche de scraping."""
        async with self.session.post(
            f'{self.api_url}/scrape',
            json=request_data
        ) as response:
            return await response.json()
    
    async def _wait_for_completion_optimized(
        self, 
        task_id: str,
        initial_delay: float = 0.5,
        max_delay: float = 5.0,
        max_wait: float = 300.0
    ) -> Dict[str, Any]:
        """Attendre la completion avec backoff adaptatif."""
        
        start_time = time.time()
        delay = initial_delay
        
        while time.time() - start_time < max_wait:
            async with self.session.get(f'{self.api_url}/scrape/{task_id}') as response:
                result = await response.json()
                
                if not result.get('success'):
                    raise Exception(f"API error: {result.get('message')}")
                
                task_data = result['data']
                status = task_data['status']
                
                if status == 'completed':
                    return task_data
                elif status == 'failed':
                    raise Exception(f"Task failed: {task_data.get('error', 'Unknown error')}")
                
                # Backoff adaptatif basé sur le progrès
                progress = task_data.get('progress', 0)
                if progress > 50:
                    delay = min(delay * 0.8, max_delay)  # Réduire le délai si progrès
                else:
                    delay = min(delay * 1.2, max_delay)  # Augmenter le délai si lent
                
                await asyncio.sleep(delay)
        
        raise Exception(f"Task {task_id} timed out after {max_wait}s")
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Obtenir les métriques de performance."""
        requests = self.metrics['requests']
        
        if not requests:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0)
        
        successful = [r for r in requests if r['success']]
        failed = [r for r in requests if not r['success']]
        response_times = [r['response_time'] for r in requests]
        
        total_time = time.time() - self.metrics['start_time']
        
        return PerformanceMetrics(
            total_requests=len(requests),
            successful_requests=len(successful),
            failed_requests=len(failed),
            average_response_time=sum(response_times) / len(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            throughput_per_second=len(requests) / total_time
        )
    
    async def close(self):
        """Fermer la session."""
        await self.session.close()

# Exemple d'usage haute performance
async def performance_benchmark():
    client = HighPerformanceScrapiniumClient(
        'http://localhost:8000',
        max_connections=200,
        max_connections_per_host=50
    )
    
    try:
        # Générer des URLs de test
        test_urls = [
            f'https://httpbin.org/html?test={i}' 
            for i in range(100)
        ]
        
        print(f"🚀 Starting benchmark with {len(test_urls)} URLs...")
        start_time = time.time()
        
        # Scraping batch haute performance
        results = await client.scrape_batch_optimized(
            test_urls,
            max_concurrent=30,
            request_template={
                'output_format': 'text',
                'use_llm': False,
                'use_cache': True
            }
        )
        
        total_time = time.time() - start_time
        metrics = client.get_performance_metrics()
        
        # Afficher les résultats
        print(f"\n📊 Performance Results:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Total requests: {metrics.total_requests}")
        print(f"   Successful: {metrics.successful_requests}")
        print(f"   Failed: {metrics.failed_requests}")
        print(f"   Success rate: {(metrics.successful_requests/metrics.total_requests)*100:.1f}%")
        print(f"   Average response time: {metrics.average_response_time:.2f}s")
        print(f"   Min response time: {metrics.min_response_time:.2f}s")
        print(f"   Max response time: {metrics.max_response_time:.2f}s")
        print(f"   Throughput: {metrics.throughput_per_second:.1f} req/s")
        
        return results, metrics
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(performance_benchmark())
```

---

**Version**: 2.0.0  
**Dernière mise à jour**: 2024-12-21  
**SDKs Supportés**: Python, JavaScript/TypeScript, Go  
**Support**: sdk-support@scrapinium.com