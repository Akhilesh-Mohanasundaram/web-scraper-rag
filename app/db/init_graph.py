from neo4j import GraphDatabase
from app.core.config import settings
from app.core.graph_schema import VALID_NODES

def init_db_constraints():
    """
    Connects to Neo4j and applies uniqueness constraints for all valid node types.
    This ensures we don't have duplicate nodes (e.g. two 'Python' nodes).
    """
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

    with driver.session() as session:
        print("Initializing Graph Constraints...")
        
        for node_type in VALID_NODES:
            # Cypher query to ensure 'name' property is unique for each label
            query = f"CREATE CONSTRAINT constraint_{node_type.lower()}_id IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.id IS UNIQUE"
            try:
                session.run(query)
                print(f"✅ Constraint applied: {node_type}(id)")
            except Exception as e:
                print(f"⚠️ Failed to apply constraint for {node_type}: {e}")
        
        # Create Vector Index (Optional, but good to prep)
        # LlamaIndex usually handles this, but explicit is better.
        try:
            session.run("CREATE INDEX node_name_lookup IF NOT EXISTS FOR (n:Concept) ON (n.name)")
            print("✅ Lookup index applied.")
        except Exception as e:
            print(f"⚠️ Index error: {e}")

    driver.close()

if __name__ == "__main__":
    init_db_constraints()