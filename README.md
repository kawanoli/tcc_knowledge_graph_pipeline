# TCC Knowledge Graph Pipeline

Este repositório é um projeto de "Extrator de conhecimento" de TCCs; serve para que você consiga filtrar (e visualizar com grafos) uma série de N TCCs desejada, para se extrair as conexões mais relevantes (utilizando NER). Pode-se utilizar para extrair informações relevantes para o seu TCC (bem, eu particularmente uso para isso 😆), ou extrair informações relevantes sobre escolha de temas e etc.

Extrai entidades de PDFs acadêmicos, treina Word2Vec sobre o corpus e gera
um grafo de co-ocorrência semanticamente enriquecido para análise de temas,
técnicas e conexões relevantes.

Este projeto foi construído propositalmente com uma arquitetura modular, para que se permita qualquer modificação de forma fácil, permitindo que todo o escopo do tema escolhido para se analisar os TCCs seja mudado com a maior facilidade possível.

---

## Estrutura

```
tcc_knowledge_graph_pipeline/
├── main.py               ← Ponto de entrada
├── config.py             ← EDITE AQUI as configurações para mudar tema e etc
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

## 🏃 Como rodar o pipeline?

Para rodar nosso pipeline de processamento dos dados, temos duas opções de caminhos para seguir:

### 🏠 Opção A: Execução Local
O mais prático e simples. Roda na máquina local.

1. Recomenda-se o uso de um `venv` para evitar conflitos de bibliotecas.
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # ou: venv\Scripts\activate  # Windows
   ```
2. Instale as dependências listadas no `requirements.txt`.
   ```bash
   # Na raíz do projeto, digite:
   pip install -r requirements.txt
   ```

3. Vamos prosseguir agora para a instalação do modelo do spacy em português:
   ```bash
   python -m spacy download pt_core_news_sm   # ou en_core_web_sm para inglês

   ```

4. Podemos agora rodar o nosso pipeline direto do terminal (na raíz do repositório, mesmo nível desse arquivo), com o comando:
    ```bash
   python main.py
    ```


### 🐳 Opção B: Container Docker (Recomendado para Testes mais Exigentes)

Caso esteja usando Windows ou MacOS, precisaremos que o Docker Desktop esteja aberto.

Dentro desse repositório, já temos um dockerfile de construção da imagem, então podemos prosseguir direto com a criação da mesma:

```bash
docker build -t tcc-graph-pipeline .   
```

Criada a imagem, executamos o comando `docker run` com as seguintes flags:

```bash
docker run --rm \                                                  
  --memory="4g" \
  --memory-swap="4g" \
  -v "$(pwd):/app" \
  tcc-graph-pipeline     

```
Essas flags permitem que o container tenha acesso ao seu repositório local, podendo editar e criar novos arquivos sem que eles fiquem presos dentro apenas do container. As flags de `memory` servem para limitar o consumo de RAM do container, que é o grande trunfo do uso do mesmo (evitar uma tela azul misteriosa no seu pc 😆).

---

## Uso do pipeline

1. Coloque seus PDFs na pasta `tccs/` (caso a pasta não exista, crie ela; ou altere `pasta_pdfs` em `config.py` e crie a pasta com o nome desejado).
2. Execute:

```bash
python main.py
```

### Saídas geradas
Dentro da pasta `outputs`, vamos encontrar os "produtos" gerados da execução do pipeline:
| Arquivo                  | Descrição                              |
|--------------------------|----------------------------------------|
| `resultado_grafo.png`    | Grafo estático de alta resolução       |
| `grafo_tccs.gexf`        | Importar no Gephi para análise visual  |
| `grafo_interativo.html`  | Abrir no browser — nós clicáveis       |
| `relatorio_analise.txt`  | Rankings, clusters, conceitos próximos |
| `word2vec_corpus.model`  | Modelo Word2Vec treinado               |

---

## Como mudar de tema?

Edite **apenas** `config.py`:

```python
CONFIG = {
    "tema": "Visual Transformers",          # ← novo tema
    "pasta_pdfs": "vits",   # ← nova pasta
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

Esses mesmos ajustes podem ser mexidos em `config.py`, caso queira "brincar" com algumas modificações de comportamento do pipeline, e ver o que irá resultar.

| Parâmetro           | Efeito                                              |
|---------------------|-----------------------------------------------------|
| `w2v_vector_size`   | Vetores maiores = mais nuance, mais memória         |
| `w2v_window`        | Janela maior = contexto mais amplo                  |
| `cooc_threshold`    | Aumentar = grafo mais esparso, menos ruído          |
| `similaridade_minima` | Aumentar = remove mais arestas "acidentais"       |
| `alpha` / `beta`    | Balancear co-ocorrência vs. semântica               |
| `n_clusters`        | Número de grupos temáticos esperados                |

