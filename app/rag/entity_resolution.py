import hashlib
from typing import Dict, Optional

class EntityResolution:
    def normalize_name(self, name: str) -> str:
        # Lowercase and strip
        norm = name.lower().strip()
        
        # Remove common suffixes that cause duplicates
        suffixes = [", inc.", " inc.", ", llc", " llc", " corp.", " corp", " ltd.", " ltd"]
        for suffix in suffixes:
            if norm.endswith(suffix):
                norm = norm[:-len(suffix)]
        
        # Remove punctuation that might be inconsistent
        import string
        norm = norm.translate(str.maketrans('', '', string.punctuation))
        return norm.strip()
        
    def generate_entity_id(self, tenant_id: str, name: str, entity_type: str) -> str:
        """
        Idempotent entity ID generation.
        """
        norm_name = self.normalize_name(name)
        base = f"{tenant_id}:{entity_type}:{norm_name}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]

entity_resolver = EntityResolution()
