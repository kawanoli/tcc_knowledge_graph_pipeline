"""
modules/enricher.py
====================
Enriquece o grafo de co-ocorrência com similaridade semântica (Word2Vec).

Por que enriquecer?
───────────────────
  Co-ocorrência sozinha é ruidosa: dois nomes podem aparecer juntos numa
  frase por acaso (ex.: "O trabalho de Silva foi apresentado na UFMG").
  Ao combinar co-ocorrência com similaridade cossenoidal entre os vetores
  Word2Vec das entidades, obtemos um peso de aresta mais robusto:

      peso_final = α * cooc_norm + β * sim_cosseno

  onde cooc_norm é a co-ocorrência normalizada para [0, 1] e
  sim_cosseno é a similaridade entre os vetores das duas entidades.
  α e β são ajustáveis em config.py.

  Arestas onde sim_cosseno < similaridade_minima são removidas, pois
  indicam entidades semanticamente não relacionadas no corpus.
"""

import numpy as np
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _cosine(v1: np.ndarray, v2: np.ndarray) -> float:
    """Similaridade cossenoidal entre dois vetores 1D."""
    return float(cosine_similarity(v1.reshape(1, -1), v2.reshape(1, -1))[0][0])


def _normalizar_pesos(grafo: nx.Graph) -> dict:
    """Normaliza os pesos de co-ocorrência para [0, 1]."""
    pesos = {(u, v): d["weight"] for u, v, d in grafo.edges(data=True)}
    max_peso = max(pesos.values()) if pesos else 1
    return {k: v / max_peso for k, v in pesos.items()}

def enriquecer_grafo_com_vetores(
    grafo: nx.Graph,
    vetores: dict[str, np.ndarray],
    config: dict,
) -> nx.Graph:
    """
    Para cada aresta do grafo:
      1. Calcula sim_cosseno entre os vetores das entidades (se disponíveis).
      2. Calcula peso_final = α * cooc_norm + β * sim_cosseno.
      3. Remove arestas abaixo do limiar de similaridade mínima.
      4. Adiciona 'semantic_similarity' e 'combined_weight' como atributos de aresta.

    Retorna o grafo enriquecido (mesmo objeto, modificado in-place).
    """
    print("\n[5/6] Enriquecendo grafo com similaridade semântica...")

    alpha = config["alpha"]
    beta  = config["beta"]
    sim_min = config["similaridade_minima"]

    cooc_norm = _normalizar_pesos(grafo)

    arestas_remover = []
    sem_vetor_count = 0

    for u, v, data in grafo.edges(data=True):
        cooc = cooc_norm.get((u, v), cooc_norm.get((v, u), 0.0))

        # Calcula similaridade semântica se ambas as entidades têm vetor
        if u in vetores and v in vetores:
            sim = _cosine(vetores[u], vetores[v])
        else:
            # Fallback: usa só co-ocorrência quando falta vetor
            sim = 0.0
            sem_vetor_count += 1

        combined = alpha * cooc + beta * sim

        # Filtra arestas semanticamente fracas
        if sim < sim_min and sim > 0:
            arestas_remover.append((u, v))
            continue

        # Persiste os novos atributos na aresta
        data["semantic_similarity"] = round(sim, 4)
        data["combined_weight"]     = round(combined, 4)
        data["cooc_norm"]           = round(cooc, 4)

    grafo.remove_edges_from(arestas_remover)
    grafo.remove_nodes_from(list(nx.isolates(grafo)))

    print(f"  ✓  {len(arestas_remover)} arestas removidas por baixa similaridade semântica "
          f"(limiar={sim_min})")
    if sem_vetor_count:
        print(f"  ⚠  {sem_vetor_count} arestas sem vetor em pelo menos um nó "
              f"(usaram apenas co-ocorrência).")
    print(f"  ✓  Grafo final: {grafo.number_of_nodes()} nós, "
          f"{grafo.number_of_edges()} arestas")

    return grafo