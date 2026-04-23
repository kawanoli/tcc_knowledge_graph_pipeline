# TCC Knowledge Graph Pipeline

Extrai entidades de PDFs acadêmicos, treina Word2Vec sobre o corpus e gera
um grafo de co-ocorrência semanticamente enriquecido para análise de temas,
técnicas e conexões relevantes.

---

## Estrutura

```
tcc_graph/
├── main.py               ← Ponto de entrada
├── config.py             ← ⚙️  EDITE AQUI para mudar de tema
├── requirements.txt
└── modules/
    ├── extractor.py      ← [1] Lê PDFs → texto limpo
    ├── vectorizer.py     ← [2/4] Treina Word2Vec + vetoriza entidades
    ├── ner_graph.py      ← [3] NER (spaCy) + grafo de co-ocorrência
    ├── enricher.py       ← [5] Combina co-ocorrência + similaridade cosseno
    ├── analyzer.py       ← [6a] Centralidade, clusters K-Means, relatório
    └── visualizer.py     ← [6b] PNG, GEXF (Gephi), HTML interativo
```

---

## Instalação

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm   # ou en_core_web_sm para inglês
```

---

## Uso

1. Coloque seus PDFs na pasta `tccs/` (ou altere `pasta_pdfs` em `config.py`).
2. Execute:

```bash
python main.py
```

### Saídas geradas
| Arquivo                  | Descrição                              |
|--------------------------|----------------------------------------|
| `resultado_grafo.png`    | Grafo estático de alta resolução       |
| `grafo_tccs.gexf`        | Importar no Gephi para análise visual  |
| `grafo_interativo.html`  | Abrir no browser — nós clicáveis       |
| `relatorio_analise.txt`  | Rankings, clusters, conceitos próximos |
| `word2vec_corpus.model`  | Modelo Word2Vec treinado               |

---

## Mudando de tema

Edite **apenas** `config.py`:

```python
CONFIG = {
    "tema": "Saúde Mental",          # ← novo tema
    "pasta_pdfs": "artigos_saude",   # ← nova pasta
    "modelo_spacy": "pt_core_news_sm",
    ...
}
```

Para inglês, troque `modelo_spacy` por `"en_core_web_sm"` e baixe o modelo:
```bash
python -m spacy download en_core_web_sm
```

---

## Como a vetorização melhora a análise

### Problema com co-ocorrência pura
Dois nomes podem aparecer na mesma sentença por acidente ("O trabalho de **Silva**
foi apresentado na **UFMG**"), gerando arestas ruidosas no grafo.

### Solução: peso combinado
Cada aresta recebe um peso calculado como:

```
peso_final = α × cooc_norm + β × sim_cosseno
```

Onde:
- `cooc_norm` = co-ocorrências normalizadas para [0, 1]
- `sim_cosseno` = similaridade entre vetores Word2Vec das entidades
- `α`, `β` = configuráveis em `config.py` (padrão: 0.5 / 0.5)

Entidades com `sim_cosseno < similaridade_minima` têm suas arestas removidas.

### Clusters semânticos
K-Means aplicado nos vetores das entidades agrupa automaticamente conceitos
relacionados (ex.: cluster de técnicas de ML, cluster de instituições, etc.),
independente do tema — basta trocar os PDFs.

---

## Ajuste fino

| Parâmetro           | Efeito                                              |
|---------------------|-----------------------------------------------------|
| `w2v_vector_size`   | Vetores maiores = mais nuance, mais memória         |
| `w2v_window`        | Janela maior = contexto mais amplo                  |
| `cooc_threshold`    | Aumentar = grafo mais esparso, menos ruído          |
| `similaridade_minima` | Aumentar = remove mais arestas "acidentais"       |
| `alpha` / `beta`    | Balancear co-ocorrência vs. semântica               |
| `n_clusters`        | Número de grupos temáticos esperados                |

```bash
docker build -t tcc-graph-pipeline .   
```

```bash
docker run --rm \                                                  
  --memory="4g" \
  --memory-swap="4g" \
  -v "$(pwd):/app" \
  tcc-graph-pipeline     

```