"""
OGI Graph Engine
Provides graph analysis utilities: shortest path, centrality, clustering,
neighbour traversal, and MTGX import/export.
"""
from __future__ import annotations
from collections import deque, defaultdict
from typing import Any, Optional
import math
import json


class GraphEngine:
    """
    In-memory graph analysis engine.
    Operates on plain dicts (entities + edges) loaded from the DB.
    """

    def __init__(self, entities: list[dict], edges: list[dict]):
        self.entities: dict[str, dict] = {e["id"]: e for e in entities}
        self.edges: list[dict] = edges

        # Adjacency: node_id -> list of (neighbour_id, edge)
        self.adj: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for edge in edges:
            self.adj[edge["source_id"]].append((edge["target_id"], edge))
            self.adj[edge["target_id"]].append((edge["source_id"], edge))  # undirected

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def neighbours(self, entity_id: str, depth: int = 1) -> list[dict]:
        """Return all entities within `depth` hops of entity_id."""
        visited = {entity_id}
        frontier = {entity_id}
        for _ in range(depth):
            next_frontier = set()
            for node in frontier:
                for (neighbour, _) in self.adj.get(node, []):
                    if neighbour not in visited:
                        visited.add(neighbour)
                        next_frontier.add(neighbour)
            frontier = next_frontier
        visited.discard(entity_id)
        return [self.entities[n] for n in visited if n in self.entities]

    def shortest_path(self, source_id: str, target_id: str) -> Optional[list[str]]:
        """BFS shortest path. Returns list of entity IDs or None."""
        if source_id == target_id:
            return [source_id]
        prev: dict[str, Optional[str]] = {source_id: None}
        queue = deque([source_id])
        while queue:
            node = queue.popleft()
            for (neighbour, _) in self.adj.get(node, []):
                if neighbour not in prev:
                    prev[neighbour] = node
                    if neighbour == target_id:
                        # Reconstruct path
                        path = []
                        cur: Optional[str] = target_id
                        while cur is not None:
                            path.append(cur)
                            cur = prev[cur]
                        return list(reversed(path))
                    queue.append(neighbour)
        return None  # No path found

    # ------------------------------------------------------------------
    # Centrality
    # ------------------------------------------------------------------

    def degree_centrality(self) -> dict[str, float]:
        """Normalised degree centrality for each node."""
        n = len(self.entities)
        if n <= 1:
            return {k: 0.0 for k in self.entities}
        return {
            node_id: len(self.adj[node_id]) / (n - 1)
            for node_id in self.entities
        }

    def betweenness_centrality(self) -> dict[str, float]:
        """
        Approximate betweenness centrality using Brandes' algorithm.
        For large graphs consider sampling.
        """
        nodes = list(self.entities.keys())
        bc: dict[str, float] = {n: 0.0 for n in nodes}

        for s in nodes:
            stack: list[str] = []
            pred: dict[str, list[str]] = {n: [] for n in nodes}
            sigma: dict[str, int] = {n: 0 for n in nodes}
            sigma[s] = 1
            dist: dict[str, int] = {n: -1 for n in nodes}
            dist[s] = 0
            queue: deque[str] = deque([s])

            while queue:
                v = queue.popleft()
                stack.append(v)
                for (w, _) in self.adj.get(v, []):
                    if dist[w] < 0:
                        queue.append(w)
                        dist[w] = dist[v] + 1
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)

            delta: dict[str, float] = {n: 0.0 for n in nodes}
            while stack:
                w = stack.pop()
                for v in pred[w]:
                    if sigma[w] > 0:
                        delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s:
                    bc[w] += delta[w]

        # Normalise
        n = len(nodes)
        norm = (n - 1) * (n - 2) if n > 2 else 1
        return {k: v / norm for k, v in bc.items()}

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------

    def connected_components(self) -> list[list[str]]:
        """Find connected components via BFS."""
        visited: set[str] = set()
        components: list[list[str]] = []
        for node in self.entities:
            if node not in visited:
                component: list[str] = []
                queue = deque([node])
                visited.add(node)
                while queue:
                    cur = queue.popleft()
                    component.append(cur)
                    for (nb, _) in self.adj.get(cur, []):
                        if nb not in visited:
                            visited.add(nb)
                            queue.append(nb)
                components.append(component)
        return components

    def clustering_coefficient(self, node_id: str) -> float:
        """Local clustering coefficient for a single node."""
        neighbours = [nb for (nb, _) in self.adj.get(node_id, [])]
        k = len(neighbours)
        if k < 2:
            return 0.0
        nb_set = set(neighbours)
        triangles = 0
        for nb in neighbours:
            for (nb2, _) in self.adj.get(nb, []):
                if nb2 in nb_set and nb2 != node_id:
                    triangles += 1
        return triangles / (k * (k - 1))

    # ------------------------------------------------------------------
    # Layout (force-directed, simple Fruchterman-Reingold)
    # ------------------------------------------------------------------

    def compute_layout(self, iterations: int = 50, width: float = 1000, height: float = 800) -> dict[str, tuple[float, float]]:
        """
        Simple force-directed layout.
        Returns {entity_id: (x, y)}.
        """
        import random
        nodes = list(self.entities.keys())
        if not nodes:
            return {}

        # Random initial positions
        pos: dict[str, list[float]] = {
            n: [random.uniform(0, width), random.uniform(0, height)]
            for n in nodes
        }

        area = width * height
        k = math.sqrt(area / len(nodes))

        def repulse(d: float) -> float:
            return k * k / d if d > 0 else 0

        def attract(d: float) -> float:
            return d * d / k

        temp = width / 10.0
        cooling = temp / (iterations + 1)

        for _ in range(iterations):
            disp: dict[str, list[float]] = {n: [0.0, 0.0] for n in nodes}

            # Repulsion
            for i, v in enumerate(nodes):
                for u in nodes[i + 1:]:
                    dx = pos[v][0] - pos[u][0]
                    dy = pos[v][1] - pos[u][1]
                    dist = math.sqrt(dx * dx + dy * dy) or 0.001
                    f = repulse(dist)
                    disp[v][0] += (dx / dist) * f
                    disp[v][1] += (dy / dist) * f
                    disp[u][0] -= (dx / dist) * f
                    disp[u][1] -= (dy / dist) * f

            # Attraction
            for edge in self.edges:
                v, u = edge["source_id"], edge["target_id"]
                if v not in pos or u not in pos:
                    continue
                dx = pos[v][0] - pos[u][0]
                dy = pos[v][1] - pos[u][1]
                dist = math.sqrt(dx * dx + dy * dy) or 0.001
                f = attract(dist)
                disp[v][0] -= (dx / dist) * f
                disp[v][1] -= (dy / dist) * f
                disp[u][0] += (dx / dist) * f
                disp[u][1] += (dy / dist) * f

            # Apply displacement with temperature clamping
            for v in nodes:
                d = math.sqrt(disp[v][0] ** 2 + disp[v][1] ** 2) or 0.001
                pos[v][0] += (disp[v][0] / d) * min(abs(disp[v][0]), temp)
                pos[v][1] += (disp[v][1] / d) * min(abs(disp[v][1]), temp)
                pos[v][0] = max(0, min(width, pos[v][0]))
                pos[v][1] = max(0, min(height, pos[v][1]))

            temp -= cooling

        return {n: (pos[n][0], pos[n][1]) for n in nodes}

    # ------------------------------------------------------------------
    # MTGX Export / Import
    # ------------------------------------------------------------------

    def to_mtgx(self) -> dict:
        """Export graph to MTGX-style dict."""
        return {
            "version": "1.0",
            "entities": list(self.entities.values()),
            "edges": self.edges,
        }

    @staticmethod
    def from_mtgx(data: dict) -> tuple[list[dict], list[dict]]:
        """Parse MTGX-style dict into (entities, edges)."""
        entities = data.get("entities", [])
        edges = data.get("edges", [])
        return entities, edges

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        components = self.connected_components()
        degrees = [len(self.adj[n]) for n in self.entities]
        return {
            "node_count": len(self.entities),
            "edge_count": len(self.edges),
            "component_count": len(components),
            "largest_component": max((len(c) for c in components), default=0),
            "avg_degree": sum(degrees) / len(degrees) if degrees else 0,
            "max_degree": max(degrees, default=0),
            "density": (
                2 * len(self.edges) / (len(self.entities) * (len(self.entities) - 1))
                if len(self.entities) > 1 else 0
            ),
        }
