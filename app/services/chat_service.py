import logging
from llama_index.core import PropertyGraphIndex, Settings
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from app.core.config import settings
from app.core.llm import SyncGeminiLLM, SyncGeminiEmbedding

logger = logging.getLogger("chat_service")

class ChatService:
    def __init__(self):
        self._engine = None

    def _initialize_engine(self):
        if self._engine:
            return
        try:
            logger.info("🔌 Connecting Chat Engine to Knowledge Graph...")
            
            # 1. Setup Models
            llm = SyncGeminiLLM(api_key=settings.GOOGLE_API_KEY)
            embed_model = SyncGeminiEmbedding(api_key=settings.GOOGLE_API_KEY)
            
            Settings.llm = llm
            Settings.embed_model = embed_model
            Settings.chunk_size = 512 # optimize for context window

            # 2. Connect to Neo4j
            graph_store = Neo4jPropertyGraphStore(
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
                url=settings.NEO4J_URI,
            )

            # 3. Load Index
            index = PropertyGraphIndex.from_existing(
                property_graph_store=graph_store,
                embed_model=embed_model,
                llm=llm
            )

            # 4. Create Chat Engine (Switching to 'context' mode for reliability)
            # This forces it to retrieve nodes first, then answer.
            # We explicitly tell it to include text (chunks) in the search.
            self._engine = index.as_chat_engine(
                chat_mode="context", 
                llm=llm,
                verbose=True,
                similarity_top_k=5  # Retrieve top 5 matching chunks
            )
            logger.info("✅ Chat Engine Ready.")

        except Exception as e:
            logger.error(f"❌ Failed to init Chat Engine: {e}")
            raise e

    def stream_chat(self, message: str):
        self._initialize_engine()
        
        logger.info(f"💬 Querying Chat Engine: {message}")
        
        # Stream Response
        response = self._engine.stream_chat(message)
        
        # Yield tokens and log the first one to confirm flow
        first = True
        for token in response.response_gen:
            if first:
                logger.info(f"⚡ Stream started! First token: '{token}'")
                first = False
            yield token

chat_service = ChatService()