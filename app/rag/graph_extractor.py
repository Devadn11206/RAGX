import json
import logging
from typing import Optional
from app.llm.orchestrator import llm_orchestrator
from app.schemas.graph import ExtractionResult, VALID_ENTITY_TYPES, VALID_RELATION_TYPES

logger = logging.getLogger(__name__)

GRAPH_EXTRACTION_PROMPT = """
You are an expert knowledge graph extractor. 
Your task is to extract entities and relationships from the provided text snippet.
The output MUST be a valid JSON object matching this schema:
{{
  "entities": [{{"name": "string", "type": "string"}}],
  "relations": [{{"source": "string", "relation_type": "string", "target": "string", "evidence": "string"}}]
}}

Rules for Entities:
- Only extract important factual entities.
- "type" MUST be exactly one of: PERSON, ORGANIZATION, COMPANY, PRODUCT, LOCATION, EVENT, DATE, TECHNOLOGY, PROJECT, CONCEPT

Rules for Relations:
- "relation_type" MUST be exactly one of: WORKS_FOR, FOUNDED, CREATED, DEVELOPED, LOCATED_IN, PART_OF, USES, OWNS, ACQUIRED, MANAGES, PARTICIPATED_IN, RELATED_TO, DEPENDS_ON, OCCURRED_IN
- Both "source" and "target" must exactly match a "name" from the "entities" list.
- "evidence" MUST be a short verbatim quote from the text that proves the relationship.

Do not include markdown blocks like ```json. Just output the raw JSON object.

Text:
{text}
"""

class GraphExtractor:
    def extract(self, text: str) -> Optional[ExtractionResult]:
        prompt = GRAPH_EXTRACTION_PROMPT.format(text=text)
        
        # Use large model for extraction tasks to ensure JSON adherence and better reasoning
        from app.core.config import settings
        response = llm_orchestrator.generate(prompt, model_name=settings.ROUTER_LARGE_MODEL)
        
        if not response or response.provider == "none":
            return None
            
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            result = ExtractionResult(**data)
            
            # Filter out invalid entities and relations
            valid_entities = []
            for e in result.entities:
                if e.type in VALID_ENTITY_TYPES:
                    valid_entities.append(e)
            
            valid_entity_names = {e.name for e in valid_entities}
            
            valid_relations = []
            for r in result.relations:
                if r.relation_type in VALID_RELATION_TYPES and \
                   r.source in valid_entity_names and \
                   r.target in valid_entity_names:
                    valid_relations.append(r)
                    
            result.entities = valid_entities
            result.relations = valid_relations
            return result
        except Exception as e:
            logger.error(f"Failed to parse graph extraction response: {e}")
            return None

graph_extractor = GraphExtractor()
