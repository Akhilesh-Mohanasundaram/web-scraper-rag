import time
from typing import Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# LlamaIndex Imports
from llama_index.core import Document, PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor, SchemaLLMPathExtractor
from llama_index.core.llms import CustomLLM, LLMMetadata, CompletionResponse, CompletionResponseGen
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core.base.embeddings.base import BaseEmbedding

# Google Imports
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError

# Config Imports
from app.core.config import settings
from app.core.graph_schema import SCHEMA_GUIDELINES, VALID_NODES, VALID_RELATIONS

# -----------------------------------------------------------------------------
# 1. Custom Sync Embedder (Fixes Event Loop Crash)
# -----------------------------------------------------------------------------
class SyncGeminiEmbedding(BaseEmbedding):
    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004", **kwargs: Any):
        super().__init__(model_name=model_name, **kwargs)
        genai.configure(api_key=api_key)

    def _get_query_embedding(self, query: str) -> List[float]:
        return genai.embed_content(model=self.model_name, content=query, task_type="retrieval_query")['embedding']

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return genai.embed_content(model=self.model_name, content=text, task_type="retrieval_document")['embedding']

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def _get_text_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._get_text_embedding(t) for t in texts]

    async def _aget_text_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        return self._get_text_embedding_batch(texts)

# -----------------------------------------------------------------------------
# 2. Custom Sync LLM (Fixes Rate Limit + Event Loop Crash)
# -----------------------------------------------------------------------------
class SyncGeminiLLM(CustomLLM):
    model_name: str = "models/gemini-2.5-flash"
    api_key: str
    
    def __init__(self, api_key: str, model_name: str = "models/gemini-2.5-flash", **kwargs):
        super().__init__(api_key=api_key, model_name=model_name, **kwargs)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name=self.model_name)

    # RETRY LOGIC: If we hit a 429 (Rate Limit), wait exponentially (min 20s, max 60s)
    @retry(
        retry=retry_if_exception_type((ResourceExhausted, InternalServerError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=20, max=60)
    )
    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        # Synchronous blocking call
        response = self._model.generate_content(prompt)
        return CompletionResponse(text=response.text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        # We don't need streaming for graph extraction, but LlamaIndex requires implementation
        response = self._model.generate_content(prompt, stream=True)
        for chunk in response:
            yield CompletionResponse(text=chunk.text, delta=chunk.text)

# -----------------------------------------------------------------------------
# 3. Graph Service
# -----------------------------------------------------------------------------
class GraphService:
    def process_document(self, text: str, source_url: str):
        if not text or len(text) < 50:
            print(f"Skipping {source_url}: Content too short.")
            return

        print(f"🔌 Connecting to Graph DB for: {source_url}")

        llm = SyncGeminiLLM(
            api_key=settings.GOOGLE_API_KEY,
            model_name="gemini-2.5-flash"
        )

        embed_model = SyncGeminiEmbedding(
            api_key=settings.GOOGLE_API_KEY,
            model_name="text-embedding-004"
        )

        # REQUIREMENT: Neo4j Database must be version 5.x+
        graph_store = Neo4jPropertyGraphStore(
            username=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
            url=settings.NEO4J_URI,
        )

        # 4. Extraction Logic (FIXED)
        # Fixes "Chunk" nodes by using SchemaLLMPathExtractor
        # Fixes Pydantic crash by using strict=False
        # Fixes deadlock by removing num_workers (running sequentially)
        extractor = SchemaLLMPathExtractor(
            llm=llm,
            possible_entities=VALID_NODES,
            possible_relations=VALID_RELATIONS,
            strict=False,
            num_workers=1
        )

        # 5. Index Wrapper
        index = PropertyGraphIndex.from_existing(
            property_graph_store=graph_store,
            embed_model=embed_model,
            kg_extractors=[extractor],
        )

        # 6. Insert
        doc = Document(text=text, metadata={"url": source_url})
        index.insert(doc)
        
        # 7. Cleanup
        graph_store._driver.close()
        
        print(f"✅ Successfully ingested: {source_url}")

# Singleton
graph_service = GraphService()