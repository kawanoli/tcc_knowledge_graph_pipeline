"""
modules/analyzer.py
====================
Análise semântica do grafo enriquecido.

Extrai:
  • Top entidades por centralidade (PageRank, grau, betweenness)
  • Clusters semânticos via K-Means nos vetores Word2Vec
  • Técnicas/métodos mais citados (heurística por tipo de entidade)
  • Entidades mais semanticamente similares ao tema central
  • Relatório em texto salvo em disco
"""

import numpy as np
import networkx as nx
from collections import defaultdict
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from gensim.models import Word2Vec
from gensim.utils  import simple_preprocess


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _entidades_por_tipo(grafo: nx.Graph) -> dict[str, list[str]]:
    por_tipo: dict[str, list] = defaultdict(list)
    for node, attrs in grafo.nodes(data=True):
        tipo = attrs.get("type", "UNK")
        por_tipo[tipo].append(node)
    return dict(por_tipo)


def _centralidade(grafo: nx.Graph) -> dict[str, dict]:
    """Calcula PageRank, grau e betweenness ponderados."""
    # Peso para PageRank / betweenness = combined_weight (ou weight como fallback)
    weight_attr = "combined_weight" if nx.get_edge_attributes(grafo, "combined_weight") else "weight"

    pagerank   = nx.pagerank(grafo, weight=weight_attr)
    degree     = dict(grafo.degree(weight=weight_attr))
    try:
        between = nx.betweenness_centrality(grafo, weight=weight_attr, normalized=True)
    except Exception:
        between = {n: 0.0 for n in grafo.nodes()}

    return {"pagerank": pagerank, "degree": degree, "betweenness": between}


def _clusterizar(vetores: dict[str, np.ndarray], n_clusters: int) -> dict[str, int]:
    """K-Means nos vetores das entidades. Retorna {entidade: cluster_id}."""
    if len(vetores) < n_clusters:
        # Menos entidades do que clusters pedidos: um cluster por entidade
        return {ent: i for i, ent in enumerate(vetores)}

    nomes  = list(vetores.keys())
    matriz = normalize(np.array(list(vetores.values())))  # normaliza para cosine

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = km.fit_predict(matriz)

    return {nome: int(label) for nome, label in zip(nomes, labels)}


def _vizinhos_tema(tema: str, modelo: Word2Vec, top_n: int) -> list[tuple[str, float]]:
    """Retorna as top_n palavras mais próximas do tema no espaço vetorial."""
    tokens_tema = simple_preprocess(tema, deacc=True, min_len=2)
    tokens_validos = [t for t in tokens_tema if t in modelo.wv]
    if not tokens_validos:
        return []
    vetor_tema = np.mean([modelo.wv[t] for t in tokens_validos], axis=0)
    return modelo.wv.similar_by_vector(vetor_tema, topn=top_n)


# ──────────────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────────────

def analisar_grafo(
    grafo: nx.Graph,
    vetores: dict[str, np.ndarray],
    modelo: Word2Vec,
    config: dict,
) -> None:
    """
    Executa análise completa e imprime + salva relatório.
    """
    print("\n[6a/6] Analisando grafo...")

    top_n     = config["top_n"]
    n_clusters = config["n_clusters"]
    tema       = config["tema"]
    arquivo_relatorio = config["saida_relatorio"]

    linhas = []

    def log(txt=""):
        print(txt)
        linhas.append(txt)

    # ── Estatísticas gerais ──────────────────────────────────────────────
    log("=" * 60)
    log(f"  RELATÓRIO DE ANÁLISE — Tema: {tema}")
    log("=" * 60)
    log(f"\n  Vértices : {grafo.number_of_nodes()}")
    log(f"  Arestas  : {grafo.number_of_edges()}")

    # ── Distribuição por tipo ────────────────────────────────────────────
    por_tipo = _entidades_por_tipo(grafo)
    log("\n─── Entidades por Tipo ───────────────────────────────────────")
    for tipo, ents in sorted(por_tipo.items()):
        log(f"  {tipo:6s}: {len(ents):4d}  ex.: {', '.join(ents[:4])}")

    # ── Centralidade ────────────────────────────────────────────────────
    cent = _centralidade(grafo)

    log(f"\n─── Top {top_n} por PageRank (influência geral) ───────────────")
    top_pr = sorted(cent["pagerank"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    for rank, (ent, score) in enumerate(top_pr, 1):
        tipo = grafo.nodes[ent].get("type", "?")
        log(f"  {rank:2d}. [{tipo}] {ent:<35s}  PR={score:.4f}")

    log(f"\n─── Top {top_n} por Grau Ponderado (conectividade bruta) ──────")
    top_deg = sorted(cent["degree"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    for rank, (ent, score) in enumerate(top_deg, 1):
        tipo = grafo.nodes[ent].get("type", "?")
        log(f"  {rank:2d}. [{tipo}] {ent:<35s}  Grau={score:.2f}")

    log(f"\n─── Top {top_n} por Betweenness (pontes/intermediários) ───────")
    top_bt = sorted(cent["betweenness"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    for rank, (ent, score) in enumerate(top_bt, 1):
        tipo = grafo.nodes[ent].get("type", "?")
        log(f"  {rank:2d}. [{tipo}] {ent:<35s}  BW={score:.4f}")

    # ── Clusters semânticos ──────────────────────────────────────────────
    if vetores:
        clusters = _clusterizar(vetores, n_clusters)

        # Armazena cluster como atributo de nó (útil na visualização)
        for node in grafo.nodes():
            grafo.nodes[node]["cluster"] = clusters.get(node, -1)

        log(f"\n─── {n_clusters} Clusters Semânticos (K-Means / Word2Vec) ───────")
        grupos: dict[int, list] = defaultdict(list)
        for ent, cid in clusters.items():
            grupos[cid].append(ent)

        for cid in sorted(grupos):
            membros = grupos[cid]
            # Representa o cluster pela entidade de maior PageRank dentro dele
            rep = max(membros, key=lambda e: cent["pagerank"].get(e, 0))
            log(f"\n  Cluster {cid}  ({len(membros)} entidades)  — representante: '{rep}'")
            for m in sorted(membros, key=lambda e: cent["pagerank"].get(e, 0), reverse=True)[:8]:
                tipo = grafo.nodes[m].get("type", "?")
                log(f"    · [{tipo}] {m}")
            if len(membros) > 8:
                log(f"    ... e mais {len(membros) - 8}")

    # ── Palavras próximas ao tema no espaço vetorial ─────────────────────
    vizinhos = _vizinhos_tema(tema, modelo, top_n)
    if vizinhos:
        log(f"\n─── Top {top_n} Conceitos Próximos de '{tema}' (W2V) ────────")
        for palavra, sim in vizinhos:
            log(f"  {palavra:<35s}  cos={sim:.4f}")

    # ── Arestas mais fortes (relações mais relevantes) ───────────────────
    log(f"\n─── Top {top_n} Relações por Peso Combinado ─────────────────")
    arestas_ord = sorted(
        grafo.edges(data=True),
        key=lambda e: e[2].get("combined_weight", e[2].get("weight", 0)),
        reverse=True,
    )[:top_n]
    for u, v, d in arestas_ord:
        cw  = d.get("combined_weight", "—")
        sim = d.get("semantic_similarity", "—")
        cooc = d.get("weight", "—")
        log(f"  {u} ↔ {v}")
        log(f"     combined={cw}  cos={sim}  co-oc={cooc}")

    log("\n" + "=" * 60)

    # ── Salva relatório ──────────────────────────────────────────────────
    with open(arquivo_relatorio, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"\n  ✓  Relatório salvo em '{arquivo_relatorio}'")