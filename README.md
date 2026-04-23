# Extrator de Conhecimento de TCCs

Este repositório contém um Extrator de Conhecimento de Trabalhos de Conclusão de Curso (TCCs). O objetivo é filtrar e visualizar, através de grafos, uma série de trabalhos desejados para extrair as conexões mais relevantes utilizando Reconhecimento de Entidades Nomeadas (NER).

Você pode utilizar esta ferramenta para extrair informações relevantes para a escrita do seu próprio TCC ou trabalhos (eu particularmente uso para isso 😆) ou para descobrir tendências e temas quentes em um conjunto de documentos acadêmicos.

O pipeline extrai entidades de PDFs acadêmicos, treina um modelo Word2Vec sobre o corpus gerado e cria um grafo de co-ocorrência semanticamente enriquecido. Isso permite uma análise profunda de temas, técnicas e conexões relevantes. O projeto foi construído com uma arquitetura modular, permitindo que qualquer modificação ou mudança de escopo (tema) seja feita com a maior facilidade possível.

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

## 📚 Base de Dados (TCCs Utilizados)

Por uma questão de direitos autorais, optei por não subir os arquivos originais junto com o repositório. Entretanto, você pode baixar os TCCs que utilizei como base no link abaixo:

* **[Download da base de TCCs (Google Drive)](https://drive.google.com/drive/folders/1ltCmrYt7LMXYEh6d7ywvBWVOw39ISGon?usp=sharing)**

**Atenção:** Ao baixar ou clonar este repositório, lembre-se de criar a pasta chamada `tccs` (ela é essencial para o funcionamento do pipeline) na raiz do projeto (ou com outro nome, desde que alterado no arquivo `config.py`). Coloque todos os PDFs que deseja analisar dentro desta pasta antes de rodar o pipeline (caso sejam os que foram baixados do meu link do Drive, coloque todos eles dentro da pasta criada). Não se preocupe com a pasta `outputs` do final do pipeline, pois ela será criada automaticamente.


## 🏃 Como rodar o pipeline?

Clonado o repositório, e criada e alimentada a pasta `tccs` (ou nome escolhido), podemos prosseguir para a execução de fato do pipeline.

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

> [!IMPORTANTE]
> Caso opte pela execução em container Docker e esteja em uma máquina com Windows ou macOS, lembre-se de **abrir o Docker Desktop em segundo plano**. Caso contrário, nem a criação da imagem nem a execução do pipeline funcionarão!

O grande trunfo do Container Docker aqui é limitar o consumo de RAM e evitar travamentos na sua máquina 😉.

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
Essas flags permitem que o container tenha acesso ao seu repositório local, podendo editar e criar novos arquivos sem que eles fiquem presos dentro apenas do container. As flags de `memory` servem para limitar o consumo de RAM do container.

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

## 🧠Como a vetorização melhora a análise

### O Problema com a Co-ocorrência Pura
Dois nomes podem aparecer na mesma sentença de forma acidental. Por exemplo: *"O trabalho de **Silva** foi apresentado na **UFMG**"*. Isso geraria arestas ruidosas no grafo, conectando entidades sem relação semântica forte.

### A Solução: Peso Combinado
Para resolver isso, cada aresta recebe um peso final que combina a frequência textual com a similaridade semântica:

$$peso\_final = \alpha \times cooc\_norm + \beta \times sim\_cosseno$$

* **cooc_norm:** Co-ocorrências normalizadas para o intervalo.
* **sim_cosseno:** Similaridade entre os vetores Word2Vec das duas entidades.
* $\alpha$ e $\beta$: Pesos configuráveis no arquivo `config.py`.

Entidades onde $sim\_cosseno < similaridade\_minima$ têm suas arestas sumariamente removidas, limpando o ruído do grafo.

### Clusters Semânticos
Aplicamos o algoritmo K-Means nos vetores das entidades para agrupar conceitos relacionados automaticamente (ex: um cluster de técnicas de ML, um cluster de instituições de ensino), independentemente do tema dos PDFs de entrada.

---

## ⚙️ Configurações e Ajuste Fino

Você pode adaptar completamente o comportamento do pipeline editando **apenas** o arquivo `config.py`.

### Mudando o Tema
Para analisar outro conjunto de documentos (como artigos em inglês sobre Visual Transformers), basta alterar as seguintes linhas:

```python
CONFIG = {
    "tema": "Visual Transformers",          # ← Altere para o novo tema
    "pasta_pdfs": "vits",                   # ← Altere para a nova pasta com os PDFs
    "modelo_spacy": "en_core_web_sm",       # ← Altere o idioma do modelo
    ...
}
```
*Não se esqueça de baixar o novo modelo do spaCy via terminal caso mude o idioma (`python -m spacy download en_core_web_sm`).*

### Ajustando o Comportamento do Grafo
Podemos brincar com os hiperparâmetros no `config.py` também para ver diferentes resultados:

| Parâmetro             | Efeito ao Ajustar                                   |
|-----------------------|-----------------------------------------------------|
| `w2v_vector_size`     | Vetores maiores trazem mais nuance semântica, mas exigem mais memória. |
| `w2v_window`          | Janela maior captura um contexto textual mais amplo. |
| `cooc_threshold`      | Aumentar o valor gera um grafo mais esparso e com menos ruído. |
| `similaridade_minima` | Aumentar o valor remove de forma mais agressiva as arestas "acidentais". |
| `alpha` / `beta`      | Balanceia o peso dado à co-ocorrência textual versus a semântica vetorial. |
| `n_clusters`          | Define o número de grupos temáticos esperados no agrupamento (K-Means). |