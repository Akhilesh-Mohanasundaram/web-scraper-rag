"""
This module defines the strict schema (Ontology) for the Knowledge Graph.
The LLM will be instructed to ONLY extract entities and relations matching these types.
"""

# 1. Node Labels (Entities)
VALID_NODES = [
    "Concept",      # Abstract ideas (e.g., "Generative AI", "Inflation")
    "Technology",   # Tools, software, hardware (e.g., "Python", "GPU", "React")
    "Organization", # Companies, Foundations (e.g., "OpenAI", "Google")
    "Person",       # Key figures (e.g., "Sam Altman", "Geoffrey Hinton")
    "Event",        # Specific occurrences (e.g., "CES 2024", "IPO")
    "Product"       # Specific released items (e.g., "iPhone 15", "GPT-4")
]

# 2. Relationship Types (Edges)
VALID_RELATIONS = [
    "RELATES_TO",       # Generic connection
    "IS_PART_OF",       # Hierarchy/Composition
    "USES",             # Dependency (Tech A uses Tech B)
    "PRODUCED_BY",      # Ownership/Creation (Product -> Organization)
    "AFFECTS",          # Causal (Interest Rates -> Stocks)
    "LAUNCHED",         # Event -> Product
    "WORKS_FOR"         # Person -> Organization
]

# 3. System Prompt Helper
# We inject this into LlamaIndex to enforce compliance.
SCHEMA_GUIDELINES = f"""
You are a strict Knowledge Graph extraction engine.
Extract entities and relationships that strictly adhere to the following schema.

ALLOWED NODE TYPES: {", ".join(VALID_NODES)}
ALLOWED RELATIONSHIP TYPES: {", ".join(VALID_RELATIONS)}

Rules:
1. If an entity does not fit a category, ignore it or fit it into "Concept".
2. Do not invent new Relationship Types. Use "RELATES_TO" if unsure.
3. Ensure entity names are canonical (e.g., use "Google" instead of "Google Inc.").
"""