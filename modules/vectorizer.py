"""
modules/vectorizer.py
======================
Treina um modelo Word2Vec sobre o corpus de PDFs e vetoriza as entidades NER.

Por que Word2Vec aqui?
  - Co-ocorrência pura não distingue "Rede Neural" (técnica) de "UFMG" (instituição)
    se ambas aparecem juntas com a mesma frequência.
  - Com vetores semânticos, a aresta entre duas entidades ganha um segundo sinal:
    quão semanticamente próximas elas são no corpus, independente de onde aparecem.
  - Isso permite filtrar ruído (entidades que co-ocorrem por acaso) e destacar
    relações genuinamente relevantes para o tema.
"""

import re
import numpy as np
from gensim.models import Word2Vec
from gensim.utils  import simple_preprocess


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _tokenizar_corpus(textos_dict: dict) -> list[list[str]]:
    """
    Converte o dicionário de textos em lista de sentenças tokenizadas.
    Cada "sentença" é uma lista de tokens minúsculos sem pontuação.
    gensim.simple_preprocess faz lowercase + remove acentos + remove tokens < 2 chars.
    """
    sentencas = []
    for texto in textos_dict.values():
        # Divide em frases aproximadas pelo ponto-e-vírgula, ponto ou newline
        frases = re.split(r'[.;!\?\n]+', texto)
        for frase in frases:
            tokens = simple_preprocess(frase, deacc=True, min_len=2)
            if tokens:
                sentencas.append(tokens)
    return sentencas


def _vetor_entidade(entidade: str, modelo: Word2Vec) -> np.ndarray | None:
    """
    Vetoriza uma entidade multi-token calculando a média dos vetores dos seus tokens.
    Retorna None se nenhum token estiver no vocabulário.

    Exemplo: "Rede Neural Convolucional" → mean([v("rede"), v("neural"), v("convolucional")])
    """
    tokens = simple_preprocess(entidade, deacc=True, min_len=2)
    vetores = [
        modelo.wv[t]
        for t in tokens
        if t in modelo.wv
    ]
    if not vetores:
        return None
    return np.mean(vetores, axis=0)

def treinar_word2vec(textos_dict: dict, config: dict) -> tuple[Word2Vec, list]:
    """
    Treina o Word2Vec sobre o corpus completo.

    Retorna
    -------
    modelo_w2v : Word2Vec treinado
    sentencas  : corpus tokenizado (útil para debug / re-treino incremental)
    """
    print("\n[2/6] Treinando Word2Vec sobre o corpus...")

    sentencas = _tokenizar_corpus(textos_dict)
    print(f"  → {len(sentencas):,} sentenças preparadas para treinamento.")

    modelo = Word2Vec(
        sentences   = sentencas,
        vector_size = config["w2v_vector_size"],
        window      = config["w2v_window"],
        min_count   = config["w2v_min_count"],
        epochs      = config["w2v_epochs"],
        workers     = config["w2v_workers"],
        sg          = 1,   # Skip-gram: melhor para corpus menores/especializados
    )

    vocab_size = len(modelo.wv)
    print(f"  ✓  Vocabulário: {vocab_size:,} tokens  |  "
          f"Vetores: {config['w2v_vector_size']}d  |  "
          f"Épocas: {config['w2v_epochs']}")

    # Salva para reuso sem re-treinar
    modelo.save("word2vec_corpus.model")
    print("  ✓  Modelo salvo em 'word2vec_corpus.model'")

    return modelo, sentencas


def vetorizar_entidades(grafo, modelo: Word2Vec) -> dict[str, np.ndarray]:
    """
    Para cada nó do grafo, gera um vetor semântico.

    Retorna
    -------
    vetores : {nome_entidade: np.ndarray} — apenas entidades com vetor válido
    """
    print("\n[4/6] Vetorizando entidades...")
    vetores = {}
    sem_vetor = []

    for node in grafo.nodes():
        v = _vetor_entidade(node, modelo)
        if v is not None:
            vetores[node] = v
        else:
            sem_vetor.append(node)

    cobertura = len(vetores) / max(len(grafo.nodes()), 1) * 100
    print(f"  ✓  {len(vetores)} entidades vetorizadas  "
          f"({cobertura:.1f}% de cobertura)")
    if sem_vetor:
        print(f"  ⚠  {len(sem_vetor)} entidades sem vetor "
              f"(fora do vocabulário): {sem_vetor[:5]}{'...' if len(sem_vetor) > 5 else ''}")

    return vetores