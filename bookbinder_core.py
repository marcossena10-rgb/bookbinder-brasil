"""
bookbinder_core.py — Núcleo do BookBinder Brasil — Livreto
Reimplementação em Python 3 do BookBinder 3.0.

Melhorias vs. original:
    - Recorte de margens brancas embutidas
    - Juntar todos os cadernos num PDF
    - Callback de progresso
    - Instruções de impressão
    - Presets de livro (A4, A5, A6, 16x23, bolso, etc.)
    - Modo "Automático": detecta o tamanho do PDF de entrada
"""

from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz


# ----------------------------------------------------------------------
# 1. Imposição
# ----------------------------------------------------------------------

def calcular_ordem_caderno(num_paginas: int) -> list[tuple[int, int, int, int]]:
    if num_paginas % 4 != 0:
        raise ValueError(f"Caderno deve ter múltiplo de 4 páginas, recebeu {num_paginas}")
    folhas = []
    for i in range(1, num_paginas // 4 + 1):
        fe = num_paginas - 2 * (i - 1)
        fd = 2 * i - 1
        ve = 2 * i
        vd = num_paginas - 2 * (i - 1) - 1
        folhas.append((fe, fd, ve, vd))
    return folhas


def dividir_em_cadernos(total_paginas: int, tam_caderno: int) -> list[list[int]]:
    if tam_caderno % 4 != 0:
        raise ValueError("Tamanho do caderno deve ser múltiplo de 4")
    cadernos = []
    for inicio in range(1, total_paginas + 1, tam_caderno):
        caderno = list(range(inicio, min(inicio + tam_caderno, total_paginas + 1)))
        while len(caderno) % 4 != 0:
            caderno.append(0)
        cadernos.append(caderno)
    return cadernos


# ----------------------------------------------------------------------
# 2. Dimensões e presets
# ----------------------------------------------------------------------

PAPEIS = {
    "a4":     (595, 842),
    "letter": (612, 792),
    "a5":     (420, 595),
    "a6":     (298, 420),
    "oficio": (612, 1008),
    "16x23":  (454, 652),
}

MODOS_LIVRO = {
    "bolso_pequeno": 0.55,
    "bolso_grande":  0.75,
    "papel_inteiro": 0.98,
}

PRESETS_LIVRO = {
    "a4_inteiro":       ("a4",     "papel_inteiro"),
    "a4_bolso_grande":  ("a4",     "bolso_grande"),
    "a4_bolso_pequeno": ("a4",     "bolso_pequeno"),
    "a5_inteiro":       ("a5",     "papel_inteiro"),
    "letter_inteiro":   ("letter", "papel_inteiro"),
    "16x23_inteiro":    ("16x23",  "papel_inteiro"),
    "a6_inteiro":       ("a6",     "papel_inteiro"),
}


def dimensoes_saida(paper: str, modo_livro: str):
    if paper not in PAPEIS:
        raise ValueError(f"Papel desconhecido: {paper}")
    if modo_livro not in MODOS_LIVRO:
        raise ValueError(f"Modo desconhecido: {modo_livro}")
    w, h = PAPEIS[paper]
    if modo_livro == "papel_inteiro":
        return h, w, "paisagem"
    return w, h, "retrato"


def resolver_preset(preset: str):
    if preset in PRESETS_LIVRO:
        return PRESETS_LIVRO[preset]
    raise ValueError(f"Preset desconhecido: {preset}")


# ----------------------------------------------------------------------
# 3. Detecção automática (modo "Automático")
# ----------------------------------------------------------------------

def detectar_melhor_preset(pdf_entrada):
    doc = fitz.open(pdf_entrada)
    if len(doc) == 0:
        doc.close()
        return "a4_inteiro"
    r = doc[0].rect
    doc.close()

    w, h = r.width, r.height
    if w > h:
        return "a4_inteiro"
    if w <= 310 and h <= 430:
        return "a6_inteiro"
    if w <= 430 and h <= 600:
        return "a5_inteiro"
    if w <= 600 and h <= 800:
        return "letter_inteiro"
    return "a4_inteiro"


# ----------------------------------------------------------------------
# 4. Colagem com recorte
# ----------------------------------------------------------------------

def _bounding_box_conteudo(pagina) -> fitz.Rect:
    retangulos = []
    for bloco in pagina.get_text("blocks"):
        if bloco[4].strip():
            retangulos.append(fitz.Rect(bloco[:4]))
    for img in pagina.get_images(full=True):
        xref = img[0]
        try:
            for r in pagina.get_image_rects(xref):
                retangulos.append(r)
        except Exception:
            pass
    try:
        for desenho in pagina.get_drawings():
            retangulos.append(desenho["rect"])
    except Exception:
        pass
    if not retangulos:
        return pagina.rect
    caixa = retangulos[0]
    for r in retangulos[1:]:
        caixa = caixa | r
    if caixa.width < 10 or caixa.height < 10:
        return pagina.rect
    return caixa


def _colar_pagina(pagina_saida, doc_entrada, num_pagina, lado, W, H, fator_livro,
                  recortar_margens=True):
    if num_pagina == 0:
        return
    pag_orig = doc_entrada[num_pagina - 1]
    fonte = _bounding_box_conteudo(pag_orig) if recortar_margens else pag_orig.rect
    r = fonte
    if r.width <= 0 or r.height <= 0:
        return
    margem = 0.02
    if lado == "esq":
        area = fitz.Rect(margem * W, margem * H, W / 2 - margem * W, H - margem * H)
    else:
        area = fitz.Rect(W / 2 + margem * W, margem * H, W - margem * W, H - margem * H)
    fator = fator_livro
    cx_area = (area.x0 + area.x1) / 2
    cy_area = (area.y0 + area.y1) / 2
    meia_l = area.width * fator / 2
    meia_a = area.height * fator / 2
    area = fitz.Rect(cx_area - meia_l, cy_area - meia_a,
                     cx_area + meia_l, cy_area + meia_a)
    escala = min(area.width / r.width, area.height / r.height)
    nl, na = r.width * escala, r.height * escala
    cx = area.x0 + (area.width - nl) / 2
    cy = area.y0 + (area.height - na) / 2
    destino = fitz.Rect(cx, cy, cx + nl, cy + na)
    pagina_saida.show_pdf_page(destino, doc_entrada, num_pagina - 1, clip=r)


# ----------------------------------------------------------------------
# 5. Geração
# ----------------------------------------------------------------------

def gerar_pdfs(pdf_entrada, pasta_saida, tam_caderno=16, duplex=True,
               paper="a4", modo_livro="papel_inteiro",
               preset=None,
               recortar_margens=True, juntar_tudo=False,
               callback_progresso=None):
    if preset == "automatico":
        preset = detectar_melhor_preset(pdf_entrada)
        print(f"[info] Modo automático: preset escolhido = {preset}")

    if preset:
        paper, modo_livro = resolver_preset(preset)

    doc = fitz.open(pdf_entrada)
    total = len(doc)
    pasta = Path(pasta_saida)
    pasta.mkdir(exist_ok=True)
    nome = Path(pdf_entrada).stem

    W, H, orient = dimensoes_saida(paper, modo_livro)
    fator = MODOS_LIVRO[modo_livro]

    print(f"[info] PDF: {total} páginas | Papel: {paper} ({W}x{H} pt, {orient}) | modo: {modo_livro}")
    print(f"[info] Recortar: {recortar_margens} | Juntar: {juntar_tudo}")

    cadernos = dividir_em_cadernos(total, tam_caderno)
    total_cadernos = len(cadernos)
    print(f"[info] Cadernos a gerar: {total_cadernos}")

    if juntar_tudo:
        saida_unica = fitz.open()
        for idx, caderno in enumerate(cadernos, start=1):
            if callback_progresso:
                callback_progresso(idx, total_cadernos)
            ordem = calcular_ordem_caderno(len(caderno))
            if duplex:
                for (fe, fd, ve, vd) in ordem:
                    p = saida_unica.new_page(width=W, height=H)
                    _colar_pagina(p, doc, caderno[fe-1] if fe else 0, "esq", W, H, fator, recortar_margens)
                    _colar_pagina(p, doc, caderno[fd-1] if fd else 0, "dir", W, H, fator, recortar_margens)
                    p = saida_unica.new_page(width=W, height=H)
                    _colar_pagina(p, doc, caderno[ve-1] if ve else 0, "esq", W, H, fator, recortar_margens)
                    _colar_pagina(p, doc, caderno[vd-1] if vd else 0, "dir", W, H, fator, recortar_margens)
            else:
                for lado, pos in [("frente", (0, 1)), ("verso", (2, 3))]:
                    for ordem_folha in ordem:
                        p = saida_unica.new_page(width=W, height=H)
                        e = ordem_folha[pos[0]]; d = ordem_folha[pos[1]]
                        _colar_pagina(p, doc, caderno[e-1] if e else 0, "esq", W, H, fator, recortar_margens)
                        _colar_pagina(p, doc, caderno[d-1] if d else 0, "dir", W, H, fator, recortar_margens)
            print(f"  - Caderno {idx} incorporado ({len(caderno)} páginas)")
        caminho = pasta / f"{nome}_todos_cadernos.pdf"
        saida_unica.save(caminho); saida_unica.close()
        print(f"OK: {caminho}")
        gerar_instrucoes(pdf_entrada, pasta_saida, cadernos, tam_caderno,
                         duplex, paper, modo_livro, juntar_tudo)
        doc.close()
        return

    for idx, caderno in enumerate(cadernos, start=1):
        if callback_progresso:
            callback_progresso(idx, total_cadernos)
        ordem = calcular_ordem_caderno(len(caderno))
        if duplex:
            saida = fitz.open()
            for (fe, fd, ve, vd) in ordem:
                p = saida.new_page(width=W, height=H)
                _colar_pagina(p, doc, caderno[fe-1] if fe else 0, "esq", W, H, fator, recortar_margens)
                _colar_pagina(p, doc, caderno[fd-1] if fd else 0, "dir", W, H, fator, recortar_margens)
                p = saida.new_page(width=W, height=H)
                _colar_pagina(p, doc, caderno[ve-1] if ve else 0, "esq", W, H, fator, recortar_margens)
                _colar_pagina(p, doc, caderno[vd-1] if vd else 0, "dir", W, H, fator, recortar_margens)
            caminho = pasta / f"{nome}_caderno{idx:02d}_duplex.pdf"
            saida.save(caminho); saida.close()
            print(f"OK: {caminho}")
        else:
            for lado, pos in [("frente", (0, 1)), ("verso", (2, 3))]:
                saida = fitz.open()
                for ordem_folha in ordem:
                    p = saida.new_page(width=W, height=H)
                    e = ordem_folha[pos[0]]; d = ordem_folha[pos[1]]
                    _colar_pagina(p, doc, caderno[e-1] if e else 0, "esq", W, H, fator, recortar_margens)
                    _colar_pagina(p, doc, caderno[d-1] if d else 0, "dir", W, H, fator, recortar_margens)
                caminho = pasta / f"{nome}_caderno{idx:02d}_{lado}.pdf"
                saida.save(caminho); saida.close()
                print(f"OK: {caminho}")
    gerar_instrucoes(pdf_entrada, pasta_saida, cadernos, tam_caderno,
                     duplex, paper, modo_livro, juntar_tudo)
    doc.close()


# ----------------------------------------------------------------------
# 6. Instruções
# ----------------------------------------------------------------------

def gerar_instrucoes(pdf_entrada, pasta_saida, cadernos, tam_caderno,
                     duplex, paper, modo_livro, juntar_tudo):
    pasta = Path(pasta_saida)
    pasta.mkdir(exist_ok=True)
    nome = Path(pdf_entrada).stem
    total_cadernos = len(cadernos)
    total_paginas = sum(len(c) for c in cadernos)

    linhas = []
    linhas.append("=" * 60)
    linhas.append("  INSTRUÇÕES DE IMPRESSÃO — BookBinder Brasil — Livreto")
    linhas.append("=" * 60)
    linhas.append("")
    linhas.append(f"PDF original:          {pdf_entrada}")
    linhas.append(f"Total de páginas:      {total_paginas}")
    linhas.append(f"Páginas por caderno:   {tam_caderno}")
    linhas.append(f"Total de cadernos:     {total_cadernos}")
    linhas.append(f"Modo do livro:         {modo_livro}")
    linhas.append(f"Tamanho do papel:      {paper.upper()}")
    linhas.append(f"Impressora duplex:     {'SIM' if duplex else 'NÃO (simples-face)'}")
    linhas.append(f"Modo de saída:         {'PDF único' if juntar_tudo else 'Um PDF por caderno'}")
    linhas.append("")
    linhas.append("-" * 60)
    linhas.append("  PASSO A PASSO")
    linhas.append("-" * 60)
    linhas.append("")

    if juntar_tudo:
        linhas.append("1. Abra o arquivo:")
        linhas.append(f"   {nome}_todos_cadernos.pdf")
        linhas.append("")
        if duplex:
            linhas.append("2. Imprima em duplex (frente e verso), SEM escala.")
            linhas.append("   IMPORTANTE: escolha 'virar na borda curta' (short-edge).")
        else:
            linhas.append("2. Imprima as páginas ÍMPARES (frentes).")
            linhas.append("3. Recoloque as folhas na bandeja e imprima as PARES (versos).")
        linhas.append("")
        linhas.append("4. Dobre cada folha ao meio (formando um caderno).")
        linhas.append("5. Empilhe os cadernos na ordem em que aparecem no PDF.")
        linhas.append("6. Grampeie ou costure a lombada.")
        linhas.append("")
    else:
        linhas.append("1. Para cada caderno, abra o arquivo correspondente:")
        linhas.append("")
        for i, caderno in enumerate(cadernos, start=1):
            paginas = len(caderno)
            if duplex:
                arquivo = f"{nome}_caderno{i:02d}_duplex.pdf"
            else:
                arquivo = f"{nome}_caderno{i:02d}_frente.pdf + _verso.pdf"
            linhas.append(f"   Caderno {i:02d} ({paginas} páginas): {arquivo}")
        linhas.append("")
        if duplex:
            linhas.append("2. Para cada caderno, imprima em duplex, SEM escala,")
            linhas.append("   com opção 'virar na borda curta'.")
        else:
            linhas.append("2. Para cada caderno: imprima _frente.pdf, recoloque folhas")
            linhas.append("   e imprima _verso.pdf.")
        linhas.append("")
        linhas.append("3. Dobre cada folha ao meio.")
        linhas.append("4. Empilhe os cadernos NA ORDEM (1, 2, 3, ...).")
        linhas.append("5. Grampeie ou costure a lombada de cada caderno.")
        linhas.append("")
        linhas.append("-" * 60)
        linhas.append("  DICA: 'saddle stitch' — abra o caderno no meio,")
        linhas.append("  grampeie na dobra e dobre de volta.")
        linhas.append("-" * 60)
        linhas.append("")

    linhas.append("")
    linhas.append("Bom trabalho! 📚")

    caminho = pasta / "instrucoes_impressao.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"OK: {caminho}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="BookBinder Brasil — Livreto (CLI)")
    ap.add_argument("entrada")
    ap.add_argument("--saida", default=".")
    ap.add_argument("--caderno", type=int, default=16)
    ap.add_argument("--simples-face", action="store_true")
    ap.add_argument("--paper", default="a4", choices=list(PAPEIS.keys()))
    ap.add_argument("--modo-livro", default="papel_inteiro", choices=list(MODOS_LIVRO.keys()))
    ap.add_argument("--preset", default=None,
                    choices=list(PRESETS_LIVRO.keys()) + ["automatico"])
    ap.add_argument("--sem-recorte", action="store_true")
    ap.add_argument("--juntar-tudo", action="store_true")
    a = ap.parse_args()
    gerar_pdfs(a.entrada, a.saida, tam_caderno=a.caderno,
               duplex=not a.simples_face, paper=a.paper, modo_livro=a.modo_livro,
               preset=a.preset,
               recortar_margens=not a.sem_recorte, juntar_tudo=a.juntar_tudo)
    print("Concluido.")
