import json
import logging
from typing import List, Literal, Optional
from pydantic import BaseModel
from app.llm.orchestrator import llm_orchestrator
from app.core.config import settings

logger = logging.getLogger(__name__)

class QueryAnalysis(BaseModel):
    is_multi_hop: bool
    entities: List[str]
    intent: str # SINGLE_HOP, MULTI_HOP, COMPARISON, RELATIONAL, TEMPORAL, UNKNOWN
    retrieval_methods: List[str] = ["vector", "lexical"]

QUERY_ANALYSIS_PROMPT = """
You are an expert query analyzer. 
Classify the following query into one of these intents:
SINGLE_HOP, MULTI_HOP, COMPARISON, RELATIONAL, TEMPORAL, UNKNOWN.
If the query requires jumping between multiple entities to find an answer (e.g., "What products did the company founded by Steve Jobs develop?"), it is MULTI_HOP.
Also, extract the core entities (names of people, companies, places, etc.) from the query that we should look up in our knowledge graph.
Finally, select the best retrieval methods from ["vector", "lexical", "graph"]. 
- Use "lexical" for exact product IDs, error codes, SKUs, or exact terminology.
- Use "vector" for general semantic searches.
- Use "graph" for multi-hop or relationship questions.

Output MUST be a valid JSON object matching this schema:
{{
  "is_multi_hop": boolean,
  "entities": ["string"],
  "intent": "string",
  "retrieval_methods": ["string"]
}}

Query:
{query}
"""

class QueryAnalyzer:
    def analyze(self, query: str) -> QueryAnalysis:
        prompt = QUERY_ANALYSIS_PROMPT.format(query=query)
        response = llm_orchestrator.generate(prompt, model_name=settings.ROUTER_SMALL_MODEL)
        
        default_analysis = QueryAnalysis(is_multi_hop=False, entities=[], intent="UNKNOWN", retrieval_methods=["vector", "lexical"])
        
        if not response or response.provider == "none":
            return default_analysis
            
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            # Basic validation of intent
            intent = data.get("intent", "UNKNOWN")
            if intent not in ["SINGLE_HOP", "MULTI_HOP", "COMPARISON", "RELATIONAL", "TEMPORAL", "UNKNOWN"]:
                intent = "UNKNOWN"
            data["intent"] = intent
                
            return QueryAnalysis(**data)
        except Exception as e:
            logger.error(f"Failed to parse query analysis: {e}")
            return default_analysis

query_analyzer = QueryAnalyzer()
