"""
modules/extractor.py
====================
Lê PDFs da pasta alvo e retorna {nome_arquivo: texto_limpo}.
"""

import os
import re
import fitz  # PyMuPDF


def extrair_textos_da_pasta(pasta: str) -> dict:
    """Lê todos os PDFs da pasta e retorna {nome_arquivo: texto_completo}."""
    print(f"\n[1/6] Extraindo textos de '{pasta}'...")
    textos = {}

    if not os.path.exists(pasta):
        print(f"  ✗  Pasta '{pasta}' não encontrada.")
        return textos

    pdfs = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"  ✗  Nenhum PDF encontrado em '{pasta}'.")
        return textos

    for arquivo in pdfs:
        caminho = os.path.join(pasta, arquivo)
        try:
            doc = fitz.open(caminho)
            texto_bruto = " ".join(pagina.get_text() for pagina in doc)
            texto_limpo = re.sub(r'\s+', ' ', texto_bruto).strip()
            textos[arquivo] = texto_limpo
            print(f"  ✓  {arquivo}  ({len(texto_limpo):,} chars)")
        except Exception as e:
            print(f"  ✗  {arquivo}: {e}")

    print(f"  → {len(textos)} arquivos carregados.")
    return textos