from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from .config import settings
from .context_budget import ContextBudgetManager
from .utils import cap_query
from .zep_common import prime_eval_thread, render_graph_search


class StudentMemory:
    """Only this file needs to be edited by students."""

    def __init__(self, client: Any):
        self.client = client
        self.budget = ContextBudgetManager(settings.context_tokens)

    # NOTE: Zep rejects graph.search queries longer than 400 characters. Some
    # eval queries are longer than that, so wrap every query with
    # `cap_query(query)` (see src/utils.py) before passing it to graph.search.

    def retrieve_long_term(self, user_id: str, thread_id: str, query: str) -> str:
        # LAB TODO 1/4
        # 1) prime_eval_thread(...) has already been provided as scaffolding.
        # 2) call thread.get_user_context(thread_id=...)
        # 3) return the .context string.
        # Bonus: append graph.search(scope="edges", limit>=20) facts with
        #        validity ranges (a low limit can miss deadline/open-loop facts).
        prime_eval_thread(self.client, user_id, thread_id, query)
        context = self.client.thread.get_user_context(thread_id=thread_id)
        evidence = self.client.graph.search(
            user_id=user_id,
            query=cap_query(query),
            scope="episodes",
            limit=10,
        )
        episodes = [
            episode
            for episode in (getattr(evidence, "episodes", None) or [])
            if getattr(episode, "role", "") != "Evaluation User"
        ]
        direct_evidence = render_graph_search(
            self._replace_episodes(evidence, episodes), episode_char_cap=400
        )
        context_block = context.context or ""
        if direct_evidence:
            return f"<DIRECT_EVIDENCE>\n{direct_evidence}\n</DIRECT_EVIDENCE>\n{context_block}"
        return context_block

    def retrieve_episodic(self, user_id: str, query: str) -> str:
        # LAB TODO 2/4
        # Use client.graph.search(user_id=..., query=cap_query(query),
        #     scope="episodes", limit=...) then render_graph_search(...).
        # Tip: verbose session episodes can crowd out concise, marker-bearing
        # reflections under the tight episodic budget — render_graph_search
        # accepts an `episode_char_cap` to keep more distinct episodes.
        results = self.client.graph.search(
            user_id=user_id,
            query=cap_query(query),
            scope="episodes",
            limit=10,
        )
        # Evaluation threads are retrieval scaffolding, not user memories. Zep
        # may index them asynchronously despite ignore_roles, so exclude them
        # by their explicit role/provenance before rendering.
        episodes = [
            episode
            for episode in (getattr(results, "episodes", None) or [])
            if getattr(episode, "role", "") != "Evaluation User"
        ]
        filtered = self._replace_episodes(results, episodes)
        return render_graph_search(filtered, episode_char_cap=600)

    def retrieve_semantic(self, graph_id: str, query: str) -> str:
        # LAB TODO 3/4
        # Search the standalone graph (graph_id, NOT user_id).
        # Recommended: scope="episodes" — it returns raw document text that keeps
        # literal markers (e.g. PAYMENT-RULE-3). The "auto" scope returns
        # extracted facts that DROP those literal codes, so avoid it here.
        # Fallback: scope="nodes".
        results = self.client.graph.search(
            graph_id=graph_id,
            query=cap_query(query),
            scope="episodes",
            limit=8,
        )
        episodes = list(getattr(results, "episodes", None) or [])
        # The KB is seeded as JSON plus plain text. Keep the shorter member of
        # each duplicate pair, then put Zep's highest-scored evidence first so
        # multi-topic queries survive the semantic token budget.
        compact: list[Any] = []
        for episode in episodes:
            content = str(getattr(episode, "content", "") or "")
            duplicate_of_shorter = any(
                other is not episode
                and len(str(getattr(other, "content", "") or "")) < len(content)
                and str(getattr(other, "content", "") or "") in content
                for other in episodes
            )
            if not duplicate_of_shorter:
                compact.append(episode)
        compact.sort(key=lambda item: float(getattr(item, "score", 0) or 0), reverse=True)
        rendered = render_graph_search(self._replace_episodes(results, compact))
        if rendered.strip():
            return rendered

        fallback = self.client.graph.search(
            graph_id=graph_id,
            query=cap_query(query),
            scope="nodes",
            limit=8,
        )
        return render_graph_search(fallback)

    def assemble_context(self, layers: dict[str, str]) -> tuple[str, dict[str, dict[str, int]]]:
        # LAB TODO 4/4
        # Use ContextBudgetManager to enforce 10/4/3/3 budget and priority order.
        # Mixed queries can place the second requested fact near the tail of a
        # Context Block/search result. Preserve both ends before the budget
        # manager applies its final limits, instead of losing that evidence by
        # keeping only the head.
        evidence_aware: dict[str, str] = {}
        separator = "\n[...trimmed...]\n"
        for layer, text in layers.items():
            raw = text or ""
            max_chars = self.budget.layer_limit(layer) * 4
            if layer != "long_term" or len(raw) <= max_chars:
                evidence_aware[layer] = raw
                continue

            available = max_chars - len(separator)
            head_chars = int(available * 0.60)
            tail_chars = available - head_chars
            evidence_aware[layer] = raw[:head_chars] + separator + raw[-tail_chars:]

        return self.budget.assemble(evidence_aware)

    @staticmethod
    def _replace_episodes(results: Any, episodes: list[Any]) -> Any:
        """Return a renderer-compatible view with a curated episode list."""
        return SimpleNamespace(
            context=getattr(results, "context", None),
            edges=getattr(results, "edges", None),
            episodes=episodes,
            nodes=getattr(results, "nodes", None),
            observations=getattr(results, "observations", None),
            thread_summaries=getattr(results, "thread_summaries", None),
        )
