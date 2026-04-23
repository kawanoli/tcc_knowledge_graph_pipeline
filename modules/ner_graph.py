"""
modules/ner_graph.py
=====================
Extrai entidades nomeadas (NER) e monta o grafo de co-ocorrência.
Idêntico ao original, porém modularizado e orientado ao CONFIG.
"""

import networkx as nx
import spacy
from itertools import combinations


def gerar_grafo_coocorrencia(textos_dict: dict, config: dict) -> nx.Graph:
    """
    Processa os textos com spaCy NER e constrói o grafo de co-ocorrência.

    Nós  : entidades reconhecidas (PER / ORG / LOC conforme config)
    Arestas: par de entidades na mesma sentença; peso = número de co-ocorrências
    """
    print(f"\n[3/6] NER + grafo de co-ocorrência...")
    print(f"  → Carregando modelo '{config['modelo_spacy']}'...")

    nlp = spacy.load(config["modelo_spacy"])
    nlp.max_length = 3_000_000

    labels_alvo = set(config["labels_ner"])
    G = nx.Graph()

    for nome_arquivo, texto in textos_dict.items():
        print(f"  → Analisando: {nome_arquivo}")
        doc = nlp(texto)

        for sentenca in doc.sents:
            entidades_frase: set[str] = set()

            for ent in sentenca.ents:
                if ent.label_ not in labels_alvo:
                    continue
                texto_ent = ent.text.strip().title()
                if len(texto_ent) <= 2:
                    continue

                entidades_frase.add(texto_ent)

                # Garante que o nó existe com atributos
                if texto_ent not in G:
                    G.add_node(texto_ent, label=texto_ent, type=ent.label_)

            # Arestas entre todas as entidades da mesma sentença
            if len(entidades_frase) > 1:
                for e1, e2 in combinations(entidades_frase, 2):
                    if G.has_edge(e1, e2):
                        G[e1][e2]["weight"] += 1
                    else:
                        G.add_edge(e1, e2, weight=1)

    # Filtro de co-ocorrência
    threshold = config["cooc_threshold"]
    arestas_fracas = [
        (u, v) for u, v, d in G.edges(data=True)
        if d["weight"] < threshold
    ]
    G.remove_edges_from(arestas_fracas)
    G.remove_nodes_from(list(nx.isolates(G)))

    print(f"  ✓  Grafo inicial: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas "
          f"(threshold co-ocorrência ≥ {threshold})")
    return G