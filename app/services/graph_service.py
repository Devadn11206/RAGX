import logging
from typing import List, Dict, Any
from app.infrastructure.neo4j import neo4j_client
from app.rag.graph_extractor import graph_extractor
from app.rag.entity_resolution import entity_resolver
from app.core.config import settings
import hashlib

logger = logging.getLogger(__name__)

class GraphService:
    async def initialize_schema(self):
        if not neo4j_client.driver:
            return
            
        async with neo4j_client.driver.session() as session:
            # Create constraints for deduplication/fast lookups
            queries = [
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE INDEX entity_tenant IF NOT EXISTS FOR (e:Entity) ON (e.tenant_id)",
                "CREATE INDEX entity_norm_name IF NOT EXISTS FOR (e:Entity) ON (e.normalized_name)"
            ]
            for query in queries:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning(f"Neo4j constraint creation failed (might already exist): {e}")

    async def ingest_chunk(self, tenant_id: str, document_id: str, chunk_id: str, text: str):
        if not neo4j_client.driver:
            return
            
        # 1. Extract Entities & Relations
        extraction = graph_extractor.extract(text)
        if not extraction or (not extraction.entities and not extraction.relations):
            return

        # 2. Prepare nodes & edges
        entities_params = []
        for e in extraction.entities:
            e_id = entity_resolver.generate_entity_id(tenant_id, e.name, e.type)
            entities_params.append({
                "id": e_id,
                "name": e.name,
                "normalized_name": entity_resolver.normalize_name(e.name),
                "type": e.type,
                "tenant_id": tenant_id
            })

        relations_params = []
        for r in extraction.relations:
            # Re-resolve the source/target IDs based on the extracted entities
            s_type = next((e.type for e in extraction.entities if e.name == r.source), None)
            t_type = next((e.type for e in extraction.entities if e.name == r.target), None)
            
            if not s_type or not t_type:
                continue
                
            s_id = entity_resolver.generate_entity_id(tenant_id, r.source, s_type)
            t_id = entity_resolver.generate_entity_id(tenant_id, r.target, t_type)
            
            # Stable relationship ID to avoid duplicates
            base_rel = f"{tenant_id}:{s_id}:{r.relation_type}:{t_id}:{chunk_id}"
            rel_id = hashlib.sha256(base_rel.encode()).hexdigest()[:16]
            
            relations_params.append({
                "id": rel_id,
                "source_id": s_id,
                "target_id": t_id,
                "type": r.relation_type,
                "evidence": r.evidence,
                "chunk_id": chunk_id,
                "tenant_id": tenant_id
            })

        # 3. Neo4j Cypher Merge
        cypher = """
        // Ensure Document exists
        MERGE (d:Document {id: $document_id})
        ON CREATE SET d.tenant_id = $tenant_id
        
        // Ensure Chunk exists
        MERGE (c:Chunk {id: $chunk_id})
        ON CREATE SET c.document_id = $document_id, c.tenant_id = $tenant_id, c.text = $text
        
        // Link Document -> Chunk
        MERGE (d)-[:CONTAINS]->(c)
        
        WITH c
        
        // Create Entities
        UNWIND $entities AS ent
        MERGE (e:Entity {id: ent.id})
        ON CREATE SET e.name = ent.name, e.normalized_name = ent.normalized_name, 
                      e.type = ent.type, e.tenant_id = ent.tenant_id
        
        // Link Chunk -> Entity (Mentions)
        MERGE (c)-[:MENTIONS]->(e)
        
        WITH c
        
        // Create Relationships
        UNWIND $relations AS rel
        MATCH (s:Entity {id: rel.source_id, tenant_id: $tenant_id})
        MATCH (t:Entity {id: rel.target_id, tenant_id: $tenant_id})
        
        // We use a generic :RELATED_TO edge with a `relation_type` property
        MERGE (s)-[r:RELATED_TO {id: rel.id}]->(t)
        ON CREATE SET r.relation_type = rel.type, r.evidence = rel.evidence, 
                      r.chunk_id = rel.chunk_id, r.tenant_id = rel.tenant_id
        """
        
        try:
            async with neo4j_client.driver.session() as session:
                await session.run(
                    cypher, 
                    document_id=document_id, 
                    chunk_id=chunk_id, 
                    tenant_id=tenant_id,
                    text=text,
                    entities=entities_params,
                    relations=relations_params
                )
        except Exception as e:
            logger.error(f"Graph ingestion failed for chunk {chunk_id}: {e}")

    async def hybrid_search(self, tenant_id: str, entities: List[str]) -> List[Dict[str, Any]]:
        """
        1-2 hop graph traversal bounded by tenant_id.
        Returns list of connected facts/chunks.
        """
        if not neo4j_client.driver or not entities:
            return []
            
        normalized_names = [entity_resolver.normalize_name(e) for e in entities]
        
        cypher = """
        MATCH (e:Entity {tenant_id: $tenant_id})
        WHERE e.normalized_name IN $names
        
        // Traverse 1-2 hops. 
        // We use exactly our :RELATED_TO relationships
        MATCH path=(e)-[r:RELATED_TO*1..2]-(neighbor:Entity)
        WHERE ALL(n IN nodes(path) WHERE n.tenant_id = $tenant_id)
        
        // Collect relationships and their source chunks
        UNWIND relationships(path) AS rel
        MATCH (c:Chunk {id: rel.chunk_id, tenant_id: $tenant_id})
        
        RETURN DISTINCT rel.relation_type AS rel_type, 
                        rel.evidence AS evidence, 
                        c.id AS chunk_id, 
                        c.text AS text,
                        startNode(rel).name AS source_name,
                        endNode(rel).name AS target_name
        LIMIT $max_chunks
        """
        
        results = []
        try:
            async with neo4j_client.driver.session() as session:
                cursor = await session.run(
                    cypher,
                    tenant_id=tenant_id,
                    names=normalized_names,
                    max_chunks=settings.GRAPH_MAX_CHUNKS
                )
                async for record in cursor:
                    results.append({
                        "rel_type": record["rel_type"],
                        "evidence": record["evidence"],
                        "chunk_id": record["chunk_id"],
                        "text": record["text"],
                        "source": record["source_name"],
                        "target": record["target_name"]
                    })
        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            
        return results

graph_service = GraphService()
