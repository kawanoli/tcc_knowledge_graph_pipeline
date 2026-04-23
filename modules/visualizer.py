"""
modules/visualizer.py
======================
Exporta as três visualizações: PNG (matplotlib), GEXF (Gephi), HTML (pyvis).
O tamanho dos nós e a espessura das arestas usam combined_weight quando disponível.
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from pyvis.network import Network


# Paleta de cores por tipo de entidade
CORES_TIPO = {
    "PER": "#ff6b6b",   # vermelho — pessoas
    "ORG": "#4ecdc4",   # teal    — organizações
    "LOC": "#ffe66d",   # amarelo — locais
    "UNK": "#aaaaaa",   # cinza   — desconhecido
}

# Paleta para clusters (usada no Pyvis quando cluster está disponível)
_CLUSTER_PALETTE = [
    "#e63946", "#457b9d", "#2a9d8f", "#e9c46a",
    "#f4a261", "#a8dadc", "#6d6875", "#b5838d",
    "#e76f51", "#264653",
]


def _peso_aresta(data: dict) -> float:
    return data.get("combined_weight", data.get("weight", 1))


# ──────────────────────────────────────────────────────────────────────────────
# PNG
# ──────────────────────────────────────────────────────────────────────────────

def _exportar_png(grafo: nx.Graph, caminho: str) -> None:
    print(f"  → Gerando PNG...")

    fig, ax = plt.subplots(figsize=(16, 16))
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    pos = nx.spring_layout(grafo, k=0.6, iterations=80, seed=42)

    # Tamanho de nó por grau
    graus = dict(grafo.degree())
    max_grau = max(graus.values()) if graus else 1
    node_sizes = [300 + 2000 * (graus[n] / max_grau) for n in grafo.nodes()]

    # Cor por tipo
    node_colors = [
        CORES_TIPO.get(grafo.nodes[n].get("type", "UNK"), CORES_TIPO["UNK"])
        for n in grafo.nodes()
    ]

    # Espessura por peso
    edge_widths = [max(0.5, _peso_aresta(d) * 3) for _, _, d in grafo.edges(data=True)]

    nx.draw_networkx_edges(grafo, pos, ax=ax,
                           width=edge_widths, edge_color="#ffffff", alpha=0.25)
    nx.draw_networkx_nodes(grafo, pos, ax=ax,
                           node_size=node_sizes, node_color=node_colors, alpha=0.95)
    nx.draw_networkx_labels(grafo, pos, ax=ax,
                            font_size=7, font_color="white", font_weight="bold")

    # Legenda de tipos
    handles = [
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor=cor, markersize=10, label=tipo)
        for tipo, cor in CORES_TIPO.items() if tipo != "UNK"
    ]
    ax.legend(handles=handles, loc="upper left",
              facecolor="#1a1a2e", labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.savefig(caminho, dpi=300, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  ✓  PNG salvo em '{caminho}'")


# ──────────────────────────────────────────────────────────────────────────────
# GEXF (Gephi)
# ──────────────────────────────────────────────────────────────────────────────

def _exportar_gexf(grafo: nx.Graph, caminho: str) -> None:
    print(f"  → Exportando GEXF...")
    try:
        nx.write_gexf(grafo, caminho)
        print(f"  ✓  GEXF salvo em '{caminho}'")
    except Exception as e:
        print(f"  ✗  Erro ao exportar GEXF: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# HTML interativo (Pyvis)
# ──────────────────────────────────────────────────────────────────────────────

def _exportar_html(grafo: nx.Graph, caminho: str) -> None:
    print(f"  → Gerando HTML interativo...")

    net = Network(
        height="800px", width="100%",
        bgcolor="#0d1117", font_color="white",
        select_menu=True, filter_menu=True,
        cdn_resources="remote" # 👈 A MÁGICA ACONTECE AQUI
    )

    tem_cluster = any("cluster" in d for _, d in grafo.nodes(data=True))
    graus = dict(grafo.degree())
    max_grau = max(graus.values()) if graus else 1

    for node, attrs in grafo.nodes(data=True):
        tipo    = attrs.get("type", "UNK")
        cluster = attrs.get("cluster", -1)

        # Cor: cluster > tipo
        if tem_cluster and cluster >= 0:
            cor = _CLUSTER_PALETTE[cluster % len(_CLUSTER_PALETTE)]
        else:
            cor = CORES_TIPO.get(tipo, CORES_TIPO["UNK"])

        tamanho = 10 + 40 * (graus[node] / max_grau)

        tooltip = (
            f"<b>{node}</b><br>"
            f"Tipo: {tipo}<br>"
            f"Grau: {graus[node]}<br>"
            + (f"Cluster: {cluster}" if tem_cluster else "")
        )

        net.add_node(node, label=node, color=cor, size=tamanho, title=tooltip)

    for u, v, data in grafo.edges(data=True):
        cw   = data.get("combined_weight", data.get("weight", 1))
        sim  = data.get("semantic_similarity", "—")
        cooc = data.get("weight", "—")
        tooltip = (
            f"<b>{u} ↔ {v}</b><br>"
            f"Peso combinado: {cw}<br>"
            f"Similaridade semântica: {sim}<br>"
            f"Co-ocorrências: {cooc}"
        )
        net.add_edge(u, v, value=float(cw) * 5, title=tooltip,
                     color={"color": "#ffffff", "opacity": 0.4})

    net.force_atlas_2based(gravity=-50, central_gravity=0.01,
                           spring_length=200, spring_strength=0.08,
                           damping=0.4, overlap=0)

    try:
        net.save_graph(caminho)
        print(f"  ✓  HTML salvo em '{caminho}'")
    except Exception as e:
        print(f"  ✗  Erro ao salvar HTML: {e}")

def exportar_visualizacoes(grafo: nx.Graph, config: dict) -> None:
    print("\n[6b/6] Exportando visualizações...")
    _exportar_png(grafo,  config["saida_png"])
    _exportar_gexf(grafo, config["saida_gexf"])
    _exportar_html(grafo, config["saida_html"])