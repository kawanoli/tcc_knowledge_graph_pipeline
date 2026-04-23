import os
import shutil
from config import CONFIG
from modules.extractor   import extrair_textos_da_pasta
from modules.vectorizer  import treinar_word2vec, vetorizar_entidades
from modules.ner_graph   import gerar_grafo_coocorrencia
from modules.enricher    import enriquecer_grafo_com_vetores
from modules.analyzer    import analisar_grafo
from modules.visualizer  import exportar_visualizacoes

# ──────────────────────────────────────────────
# EXECUÇÃO PRINCIPAL
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(f"  Pipeline TCC Knowledge Graph")
    print(f"  Tema: {CONFIG['tema']}")
    print("=" * 60)

    # 1. Extração de texto
    textos = extrair_textos_da_pasta(CONFIG["pasta_pdfs"])
    if not textos:
        print("Nenhum texto extraído. Abortando.")
        exit(1)

    # 2. Treinamento Word2Vec sobre o corpus completo
    modelo_w2v, sentencas_corpus = treinar_word2vec(textos, CONFIG)

    # 3. NER + grafo de co-ocorrência
    grafo = gerar_grafo_coocorrencia(textos, CONFIG)

    # 4. Vetorização das entidades e enriquecimento do grafo
    vetores_entidades = vetorizar_entidades(grafo, modelo_w2v)
    grafo = enriquecer_grafo_com_vetores(grafo, vetores_entidades, CONFIG)

    # 5. Análise semântica
    analisar_grafo(grafo, vetores_entidades, modelo_w2v, CONFIG)

    # 6. Exportação
    exportar_visualizacoes(grafo, CONFIG)

    # 7. Pós-processamento: Mover arquivos para a pasta 'outputs'
    print("\nMovendo saídas para a pasta 'outputs/'...")
    
    # Cria a pasta 'outputs' se ela não existir
    os.makedirs("outputs", exist_ok=True)
    
    # Lista de arquivos gerados (baseado no seu CONFIG e README)
    arquivos_gerados = [
        CONFIG["saida_png"],
        CONFIG["saida_gexf"],
        CONFIG["saida_html"],
        CONFIG["saida_relatorio"],
        "word2vec_corpus.model"  # Adicionado caso você salve o modelo também
    ]

    for arquivo in arquivos_gerados:
        if os.path.exists(arquivo):
            caminho_destino = os.path.join("outputs", arquivo)
            
            # Se o arquivo já existir no destino (de uma run anterior), removemos primeiro 
            # para evitar erros de sobrescrita no Windows/Linux
            if os.path.exists(caminho_destino):
                os.remove(caminho_destino)
                
            shutil.move(arquivo, "outputs/")
            print(f"  └─ Movido: {arquivo}")
        else:
            print(f"  └─ ⚠️  Aviso: Arquivo não encontrado: {arquivo}")

    print("\n✅  Pipeline concluído.")