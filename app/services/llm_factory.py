from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings
from app.core.config import settings
import google.generativeai as genai

class LLMFactory:
    @staticmethod
    def setup():
        """
        Configures the global LlamaIndex settings to use Google Gemini (Free Tier).
        """
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in .env")

        # Configure the low-level library directly to avoid warnings (optional but good practice)
        genai.configure(api_key=settings.GOOGLE_API_KEY)

        # 1. LLM: Gemini 1.5 Flash (Specific Version)
        # We use the specific '001' version to avoid 404 errors with aliases
        Settings.llm = Gemini(
            model="models/gemini-2.5-flash", 
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.0,
        )

        # 2. Embeddings: Google Text Embedding 004
        Settings.embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004",
            api_key=settings.GOOGLE_API_KEY
        )
        
        return Settings

# Initialize on import
llm_setup = LLMFactory.setup()