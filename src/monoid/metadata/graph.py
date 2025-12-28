import networkx as nx
from typing import List, Dict, Any
from monoid.core.storage import storage
from monoid.core.domain import Note

class GraphManager:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._dirty = True

    def build_graph(self) -> nx.DiGraph:
        """Build graph from notes."""
        self.graph.clear()
        notes = storage.list_notes()
        
        # Add nodes
        for note in notes:
            self.graph.add_node(
                note.metadata.id, 
                title=note.metadata.title, 
                type=note.metadata.type.value,
                tags=note.metadata.tags
            )

        # Add edges
        for note in notes:
            # 1. Explicit outgoing links
            # (Note: we need to extract wiki links [[id]] if not already in metadata)
            # For now, rely on metadata.links which presumably are populated?
            # Actually, we need to extract them. Let's do a simple regex here for now.
            import re
            links = re.findall(r'\[\[(\d+)\]\]', note.content)
            for target_id in links:
                if self.graph.has_node(target_id):
                    self.graph.add_edge(note.metadata.id, target_id, type="explicit")

        # 2. Tag Overlap
        # Weighted by shared tags
        for i, n1 in enumerate(notes):
            tags1 = set(t.name for t in n1.metadata.tags)
            if not tags1: continue
            for n2 in notes[i+1:]:
                tags2 = set(t.name for t in n2.metadata.tags)
                intersection = tags1.intersection(tags2)
                if intersection:
                    weight = len(intersection) / len(tags1.union(tags2))
                    if weight > 0.3: # Threshold
                        self.graph.add_edge(n1.metadata.id, n2.metadata.id, type="related", weight=weight)
                        self.graph.add_edge(n2.metadata.id, n1.metadata.id, type="related", weight=weight)

        # 3. Provenance
        for note in notes:
            if note.metadata.provenance:
                if self.graph.has_node(note.metadata.provenance):
                    self.graph.add_edge(note.metadata.provenance, note.metadata.id, type="derivative")

        # 4. Semantic Similarity
        try:
            from monoid.metadata.db import db
            import json
            import numpy as np

            conn = db.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT note_id, vector FROM embeddings")
            rows = cur.fetchall()
            
            vecs = {}
            for row in rows:
                if row['vector']:
                    vecs[row['note_id']] = np.array(json.loads(row['vector']))
            
            ids = list(vecs.keys())
            for i, id1 in enumerate(ids):
                v1 = vecs[id1]
                norm1 = np.linalg.norm(v1)
                if norm1 == 0: continue
                
                for id2 in ids[i+1:]:
                    v2 = vecs[id2]
                    norm2 = np.linalg.norm(v2)
                    if norm2 == 0: continue
                    
                    sim = np.dot(v1, v2) / (norm1 * norm2)
                    if sim > 0.8: # Semantic threshold
                        self.graph.add_edge(id1, id2, type="semantic", weight=float(sim))
                        self.graph.add_edge(id2, id1, type="semantic", weight=float(sim))

        except Exception as e:
            print(f"Graph semantic build error: {e}")

        self._dirty = False
        return self.graph

    def get_stats(self) -> Dict[str, Any]:
        if self._dirty:
            self.build_graph()
        
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "components": nx.number_weakly_connected_components(self.graph)
        }
    
    def get_related(self, note_id: str) -> List[str]:
        """Get related notes (neighbors)."""
        if self._dirty:
            self.build_graph()
        if not self.graph.has_node(note_id):
            return []
        
        # Neighbors: predecessors and successors
        preds = list(self.graph.predecessors(note_id))
        succs = list(self.graph.successors(note_id))
        return list(set(preds + succs))

graph_manager = GraphManager()
