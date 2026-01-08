import time
import logging
from typing import Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# LlamaIndex Imports
from llama_index.core.llms import CustomLLM, LLMMetadata, CompletionResponse, CompletionResponseGen
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core.base.embeddings.base import BaseEmbedding

# Google Imports
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, NotFound

logger = logging.getLogger("llm_core")

def log_retry_attempt(retry_state):
    logger.warning(f"⚠️ Rate Limit hit. Sleeping {retry_state.next_action.sleep}s...")

# -----------------------------------------------------------------------------
# 1. Custom Sync Embedder (Shared)
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
        embeddings = []
        for t in texts:
            time.sleep(1.0) 
            embeddings.append(self._get_text_embedding(t))
        return embeddings

    async def _aget_text_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        return self._get_text_embedding_batch(texts)

# -----------------------------------------------------------------------------
# 2. Custom Sync LLM (Shared & Streaming Enabled)
# -----------------------------------------------------------------------------
class SyncGeminiLLM(CustomLLM):
    # Use 'gemini-flash-latest' or 'gemini-2.5-flash'
    model_name: str = "models/gemini-2.5-flash"
    api_key: str
    
    def __init__(self, api_key: str, model_name: str = "models/gemini-2.5-flash", **kwargs):
        super().__init__(api_key=api_key, model_name=model_name, **kwargs)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name=self.model_name)

    @retry(
        retry=retry_if_exception_type((ResourceExhausted, InternalServerError, ServiceUnavailable)),
        stop=stop_after_attempt(10), 
        wait=wait_exponential(multiplier=2, min=5, max=60),
        before_sleep=log_retry_attempt
    )
    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        time.sleep(4.0) 
        response = self._model.generate_content(prompt)
        return CompletionResponse(text=response.text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        time.sleep(4.0)
        try:
            response = self._model.generate_content(prompt, stream=True)
            for chunk in response:
                # --- FIX: SAFE TEXT EXTRACTION ---
                # Check if the chunk actually contains text before accessing .text
                # to prevent ValueError on empty/safety-blocked chunks.
                if chunk.parts: 
                    try:
                        chunk_text = chunk.text
                        if chunk_text:
                            yield CompletionResponse(text=chunk_text, delta=chunk_text)
                    except ValueError:
                        pass # Skip chunks blocked by safety filters
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield CompletionResponse(text=f"[Error: {str(e)}]")