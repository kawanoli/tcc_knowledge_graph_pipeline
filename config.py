"""
config.py
=========
Única fonte de verdade do pipeline.
Para mudar de tema, edite apenas este arquivo.
"""

CONFIG = {
    # ── Identidade do projeto ──────────────────────────────────────────────
    "tema": "Visão Computacional",          # Usado em títulos e logs
    "pasta_pdfs": "tccs",                        # Pasta com os PDFs

    # ── NER ───────────────────────────────────────────────────────────────
    "modelo_spacy": "pt_core_news_sm",           # Troque por 'en_core_web_sm' p/ inglês
    "labels_ner": ["PER", "ORG", "LOC"],         # Tipos de entidade a capturar
    # Para textos técnicos em inglês, adicione 'PRODUCT', 'EVENT', 'WORK_OF_ART'

    # ── Word2Vec ──────────────────────────────────────────────────────────
    "w2v_vector_size": 100,   # Dimensão dos vetores
    "w2v_window": 5,          # Tamanho da janela de contexto
    "w2v_min_count": 2,       # Frequência mínima de uma palavra para ser incluída
    "w2v_epochs": 30,         # Épocas de treinamento
    "w2v_workers": 4,         # Threads paralelas

    # ── Grafo / Co-ocorrência ─────────────────────────────────────────────
    "cooc_threshold": 2,      # Peso mínimo de co-ocorrência para manter a aresta

    # ── Enriquecimento semântico ──────────────────────────────────────────
    # Peso final da aresta = α * co-ocorrência_norm + β * similaridade_cosseno
    "alpha": 0.5,             # Peso da co-ocorrência normalizada
    "beta": 0.5,              # Peso da similaridade semântica
    "similaridade_minima": 0.20,  # Abaixo disso, aresta é removida (0 = desliga filtro)

    # ── Análise ───────────────────────────────────────────────────────────
    "top_n": 15,              # Top N entidades/tópicos a reportar
    "n_clusters": 5,          # Número de clusters semânticos

    # ── Saídas ────────────────────────────────────────────────────────────
    "saida_png":  "resultado_grafo.png",
    "saida_gexf": "grafo_tccs.gexf",
    "saida_html": "grafo_interativo.html",
    "saida_relatorio": "relatorio_analise.txt",
}