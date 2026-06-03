"""Research Bundle example.

Demonstrates the research assistant bundle:
  - Paper ingestion: source → Paper + Author + Venue
  - Claim extraction: Paper → observations
  - Idea atom distillation: Paper → IdeaAtom objects
  - Hypothesis generation: IdeaAtom → ResearchDirection
  - Experiment creation via tool

Run with:
    python bundles/examples/research_example.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packs.research import ResearchSettings
from packs.memory_gateway import MemoryGatewaySettings
from bundles.research_bundle import build_research_assistant


def main():
    print("=" * 60)
    print("Research Bundle — demo")
    print("=" * 60)

    rt = build_research_assistant(
        research_settings=ResearchSettings(
            min_coherence_for_hypothesis=0.45,
            max_ideas_per_paper=5,
            min_atoms_for_synthesis=2,
        ),
        memory_gateway_settings=MemoryGatewaySettings(
            acceptance_threshold=0.65,
        ),
    )

    graph = rt.graph
    loaded = [p.name for p in rt.loaded_packs()]
    print(f"\nPacks loaded ({len(loaded)}): {loaded}")

    # Ingest two related papers
    from packs.research.tools import ingest_research_paper_fn, create_experiment_fn

    print("\n[1] Ingesting paper 1: Attention Is All You Need…")
    ingest_research_paper_fn(
        graph,
        title="Attention Is All You Need",
        abstract=(
            "We propose the Transformer, a model architecture eschewing recurrence "
            "and instead relying entirely on an attention mechanism to draw global "
            "dependencies between input and output. The Transformer allows for more "
            "parallelization and achieves a new state of the art in translation."
        ),
        authors="Vaswani, Shazeer, Parmar, Uszkoreit",
        venue="NeurIPS 2017",
        year=2017,
        keywords=["attention", "transformer", "translation", "parallelization"],
    )
    rt.run_until_idle()

    print("[2] Ingesting paper 2: BERT…")
    ingest_research_paper_fn(
        graph,
        title="BERT: Pre-training of Deep Bidirectional Transformers",
        abstract=(
            "We introduce BERT, a new language representation model which stands for "
            "Bidirectional Encoder Representations from Transformers. BERT is designed "
            "to pre-train deep bidirectional representations from unlabeled text by "
            "jointly conditioning on both left and right context in all layers. "
            "Fine-tuned BERT achieves state-of-the-art results on NLP benchmarks."
        ),
        authors="Devlin, Chang, Lee, Toutanova",
        venue="NAACL 2019",
        year=2019,
        keywords=["bert", "pretraining", "transformers", "language", "bidirectional"],
    )
    rt.run_until_idle()

    papers = [o for o in graph.objects() if o.type == "paper"]
    authors = [o for o in graph.objects() if o.type == "author"]
    venues = [o for o in graph.objects() if o.type == "venue"]
    claims = [o for o in graph.objects() if o.type == "observation"]
    idea_atoms = [o for o in graph.objects() if o.type == "idea_atom"]
    directions = [o for o in graph.objects() if o.type == "research_direction"]

    print(f"\nAfter two papers:")
    print(f"  papers:              {len(papers)}")
    print(f"  authors:             {len(authors)}")
    print(f"  venues:              {len(venues)}")
    print(f"  observations:        {len(claims)}")
    print(f"  idea_atoms:          {len(idea_atoms)}")
    print(f"  research_directions: {len(directions)}")
    for d in directions:
        dd = d.data or {}
        print(f"    [{d.id[:8]}] {dd.get('title', '')[:60]!r} conf={dd.get('confidence')}")

    # Create an experiment for the first direction
    if directions:
        dir_id = directions[0].id
        print(f"\n[3] Creating experiment for direction {dir_id[:8]}…")
        create_experiment_fn(
            graph,
            title="Evaluate transformer pretraining on low-resource NLP tasks",
            hypothesis=(
                "BERT-style bidirectional pretraining outperforms GPT-style "
                "autoregressive pretraining on low-resource NLP benchmarks."
            ),
            direction_id=dir_id,
        )
        rt.run_until_idle()

        experiments = [o for o in graph.objects() if o.type == "experiment"]
        print(f"  experiments: {len(experiments)}")
        for e in experiments:
            d = e.data or {}
            print(f"    [{e.id[:8]}] status={d.get('status')} {d.get('title', '')[:50]!r}")

    print("\nDone.")


if __name__ == "__main__":
    main()
