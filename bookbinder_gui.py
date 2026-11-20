"""
bookbinder_gui.py — Interface do BookBinder Brasil — Livreto
Versão 2.0 — Opções de numeração removidas, entrada manual em caderno.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QComboBox, QCheckBox,
    QLineEdit, QFileDialog, QTextEdit, QProgressBar, QGroupBox,
    QMessageBox
)

try:
    import bookbinder_core as core
except ImportError:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Erro",
        "Arquivo bookbinder_core.py não encontrado na pasta do projeto.")
    sys.exit(1)


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BookBinder Brasil — Livreto")
        self.setMinimumSize(640, 820)

        icone_path = Path(__file__).parent / "icone_livreto.svg"
        if icone_path.exists():
            self.setWindowIcon(QIcon(str(icone_path)))

        self.pdf_selecionado = None
        self.settings = QSettings("BookBinderBrasil", "Livreto")

        self._construir_interface()
        self._carregar_configuracoes()
        self.setAcceptDrops(True)

    def _construir_interface(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout = QVBoxLayout(widget_central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        titulo = QLabel("BookBinder Brasil — Livreto")
        f = QFont(); f.setPointSize(16); f.setBold(True)
        titulo.setFont(f)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        sub = QLabel("Transforma um PDF em cadernos prontos para encadernação")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #666; margin-bottom: 8px;")
        layout.addWidget(sub)

        grupo_pdf = QGroupBox("PDF de entrada")
        layout_pdf = QHBoxLayout(grupo_pdf)

        self.botao_abrir = QPushButton("📂  Abrir PDF...")
        self.botao_abrir.setMinimumHeight(36)
        self.botao_abrir.clicked.connect(self._abrir_pdf)
        layout_pdf.addWidget(self.botao_abrir)

        self.label_pdf = QLabel("Nenhum PDF selecionado\n(ou arraste um PDF para cá)")
        self.label_pdf.setStyleSheet("color: #888; font-style: italic;")
        self.label_pdf.setWordWrap(True)
        layout_pdf.addWidget(self.label_pdf, stretch=1)
        layout.addWidget(grupo_pdf)

        grupo_opcoes = QGroupBox("Opções de encadernação")
        layout_opcoes = QVBoxLayout(grupo_opcoes)

        linha0 = QHBoxLayout()
        linha0.addWidget(QLabel("Tamanho do livro:"))
        self.combo_preset = QComboBox()
        self.combo_preset.addItem("Automático (detectar do PDF)", "automatico")
        self.combo_preset.addItem("A4 dobrado → A5 (recomendado)", "a4_inteiro")
        self.combo_preset.addItem("A4 — bolso grande", "a4_bolso_grande")
        self.combo_preset.addItem("A4 — bolso pequeno", "a4_bolso_pequeno")
        self.combo_preset.addItem("A5 dobrado → A6", "a5_inteiro")
        self.combo_preset.addItem("A6 dobrado → mini", "a6_inteiro")
        self.combo_preset.addItem("Carta dobrado → Half Letter", "letter_inteiro")
        self.combo_preset.addItem("Livro 16×23 cm", "16x23_inteiro")
        self.combo_preset.addItem("Personalizado", "personalizado")
        self.combo_preset.currentIndexChanged.connect(self._ao_mudar_preset)
        linha0.addWidget(self.combo_preset, stretch=1)
        layout_opcoes.addLayout(linha0)

        linha1 = QHBoxLayout()
        linha1.addWidget(QLabel("Páginas por caderno:"))
        self.spin_caderno = QSpinBox()
        self.spin_caderno.setRange(4, 128)
        self.spin_caderno.setSingleStep(4)
        self.spin_caderno.setValue(16)
        self.spin_caderno.setSuffix(" páginas")
        self.spin_caderno.setKeyboardTracking(True)
        self.spin_caderno.setToolTip("Digite um número ou use as setas. O valor será ajustado para o múltiplo de 4 mais próximo.")
        linha1.addWidget(self.spin_caderno)
        self.label_ajuda_caderno = QLabel("(digite ou use as setas)")
        self.label_ajuda_caderno.setStyleSheet("color: #888; font-size: 10px;")
        linha1.addWidget(self.label_ajuda_caderno)
        linha1.addStretch()
        layout_opcoes.addLayout(linha1)

        linha2 = QHBoxLayout()
        linha2.addWidget(QLabel("Modo (manual):"))
        self.combo_modo = QComboBox()
        self.combo_modo.addItem("Papel inteiro", "papel_inteiro")
        self.combo_modo.addItem("Bolso grande", "bolso_grande")
        self.combo_modo.addItem("Bolso pequeno", "bolso_pequeno")
        linha2.addWidget(self.combo_modo, stretch=1)
        layout_opcoes.addLayout(linha2)

        linha3 = QHBoxLayout()
        linha3.addWidget(QLabel("Papel (manual):"))
        self.combo_papel = QComboBox()
        self.combo_papel.addItem("A4 (210×297 mm)", "a4")
        self.combo_papel.addItem("Carta / Letter (8,5×11 pol)", "letter")
        self.combo_papel.addItem("A5 (148×210 mm)", "a5")
        self.combo_papel.addItem("A6 (105×148 mm)", "a6")
        self.combo_papel.addItem("Ofício (8,5×14 pol)", "oficio")
        self.combo_papel.addItem("Livro 16×23 cm", "16x23")
        linha3.addWidget(self.combo_papel, stretch=1)
        layout_opcoes.addLayout(linha3)

        self.check_duplex = QCheckBox("Impressora duplex (frente e verso automáticos)")
        self.check_duplex.setChecked(True)
        layout_opcoes.addWidget(self.check_duplex)

        self.check_juntar = QCheckBox("Juntar todos os cadernos num único PDF")
        self.check_juntar.setChecked(True)
        layout_opcoes.addWidget(self.check_juntar)

        self.check_recortar = QCheckBox("Recortar margens brancas do PDF original")
        self.check_recortar.setChecked(True)
        layout_opcoes.addWidget(self.check_recortar)

        layout.addWidget(grupo_opcoes)

        grupo_saida = QGroupBox("Pasta de saída")
        layout_saida = QHBoxLayout(grupo_saida)
        self.campo_saida = QLineEdit("out")
        layout_saida.addWidget(self.campo_saida, stretch=1)
        self.botao_pasta = QPushButton("📁  Escolher...")
        self.botao_pasta.clicked.connect(self._escolher_pasta)
        layout_saida.addWidget(self.botao_pasta)
        layout.addWidget(grupo_saida)

        self.botao_gerar = QPushButton("🎯  Gerar cadernos")
        self.botao_gerar.setMinimumHeight(48)
        self.botao_gerar.setStyleSheet("""
            QPushButton {
                background-color: #2C5F8A; color: white;
                font-size: 15px; font-weight: bold;
                border-radius: 6px; padding: 8px;
            }
            QPushButton:hover { background-color: #3A7BAE; }
            QPushButton:pressed { background-color: #1A3D5C; }
            QPushButton:disabled { background-color: #AAA; }
        """)
        self.botao_gerar.setEnabled(False)
        self.botao_gerar.clicked.connect(self._gerar_cadernos)
        layout.addWidget(self.botao_gerar)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(160)
        self.log.setStyleSheet("""
            QTextEdit {
                background-color: #2B2B2B; color: #E0E0E0;
                border: 1px solid #555; font-family: monospace;
                font-size: 11px; padding: 4px;
            }
        """)
        self.log.setHtml('<span style="color:#E0E0E0;">Pronto. Selecione um PDF para começar.</span>')
        layout.addWidget(self.log)

        self.barra = QProgressBar()
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setTextVisible(True)
        layout.addWidget(self.barra)

        self._ao_mudar_preset()

    def _ao_mudar_preset(self):
        personalizado = self.combo_preset.currentData() == "personalizado"
        self.combo_modo.setEnabled(personalizado)
        self.combo_papel.setEnabled(personalizado)

    def _carregar_configuracoes(self):
        pasta = self.settings.value("pasta_saida", "out")
        if pasta:
            self.campo_saida.setText(pasta)

        preset = self.settings.value("preset", "automatico")
        for i in range(self.combo_preset.count()):
            if self.combo_preset.itemData(i) == preset:
                self.combo_preset.setCurrentIndex(i)
                break

        modo = self.settings.value("modo_livro", "papel_inteiro")
        for i in range(self.combo_modo.count()):
            if self.combo_modo.itemData(i) == modo:
                self.combo_modo.setCurrentIndex(i)
                break

        papel = self.settings.value("papel", "a4")
        for i in range(self.combo_papel.count()):
            if self.combo_papel.itemData(i) == papel:
                self.combo_papel.setCurrentIndex(i)
                break

        caderno = int(self.settings.value("caderno", 16))
        self.spin_caderno.setValue(caderno)

        self.check_duplex.setChecked(self.settings.value("duplex", "true") == "true")
        self.check_juntar.setChecked(self.settings.value("juntar", "true") == "true")
        self.check_recortar.setChecked(self.settings.value("recortar", "true") == "true")

    def _salvar_configuracoes(self):
        self.settings.setValue("pasta_saida", self.campo_saida.text())
        self.settings.setValue("preset", self.combo_preset.currentData())
        self.settings.setValue("modo_livro", self.combo_modo.currentData())
        self.settings.setValue("papel", self.combo_papel.currentData())
        self.settings.setValue("caderno", self.spin_caderno.value())
        self.settings.setValue("duplex", "true" if self.check_duplex.isChecked() else "false")
        self.settings.setValue("juntar", "true" if self.check_juntar.isChecked() else "false")
        self.settings.setValue("recortar", "true" if self.check_recortar.isChecked() else "false")

    def closeEvent(self, event):
        self._salvar_configuracoes()
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                caminho = url.toLocalFile()
                if caminho.lower().endswith(".pdf"):
                    self._carregar_pdf(caminho)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def _abrir_pdf(self):
        ultima = self.settings.value("ultima_pasta_pdf", str(Path.home()))
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar PDF de entrada", ultima,
            "Arquivos PDF (*.pdf)"
        )
        if not caminho:
            return
        self._carregar_pdf(caminho)

    def _carregar_pdf(self, caminho: str):
        try:
            import pymupdf
            doc = pymupdf.open(caminho)
            num_paginas = len(doc)
            doc.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao abrir PDF",
                f"Não foi possível abrir o arquivo:\n{caminho}\n\nDetalhes: {e}")
            return
        if num_paginas == 0:
            QMessageBox.warning(self, "PDF vazio",
                "O PDF selecionado não tem páginas.")
            return
        self.pdf_selecionado = caminho
        nome = Path(caminho).name
        self.label_pdf.setText(f"{nome}  ({num_paginas} páginas)")
        self.label_pdf.setStyleSheet("color: #2C5F8A; font-weight: bold;")
        self.botao_gerar.setEnabled(True)
        self._log("")
        self._log(f"PDF carregado: {caminho}", "destaque")
        self._log(f"Total de páginas: {num_paginas}")
        self.settings.setValue("ultima_pasta_pdf", str(Path(caminho).parent))

    def _escolher_pasta(self):
        ultima = self.settings.value("pasta_saida", str(Path.home()))
        caminho = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta de saída", ultima)
        if caminho:
            self.campo_saida.setText(caminho)
            self._log(f"Pasta de saída: {caminho}", "destaque")

    def _gerar_cadernos(self):
        if not self.pdf_selecionado:
            QMessageBox.warning(self, "Nenhum PDF",
                "Selecione um PDF de entrada primeiro.")
            return

        caderno = self.spin_caderno.value()
        if caderno % 4 != 0:
            ajustado = round(caderno / 4) * 4
            if ajustado < 4:
                ajustado = 4
            self._log(f"Ajustando caderno de {caderno} para {ajustado} (múltiplo de 4).", "info")
            self.spin_caderno.setValue(ajustado)
            caderno = ajustado

        preset = self.combo_preset.currentData()
        modo = self.combo_modo.currentData()
        papel = self.combo_papel.currentData()
        duplex = self.check_duplex.isChecked()
        juntar = self.check_juntar.isChecked()
        recortar = self.check_recortar.isChecked()
        pasta_saida = self.campo_saida.text().strip() or "out"

        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setFormat("Aguardando...")
        self.botao_gerar.setEnabled(False)
        QApplication.processEvents()

        self._log("")
        self._log("=== Iniciando geração ===", "destaque")
        self._log(f"PDF: {self.pdf_selecionado}")
        self._log(f"Preset: {preset} | Caderno: {caderno}")
        self._log(f"Duplex: {duplex} | Juntar: {juntar} | Recortar: {recortar}")
        self._log(f"Pasta de saída: {pasta_saida}")

        import contextlib, io

        class _LogWriter(io.TextIOBase):
            def __init__(self, gui): self.gui = gui
            def write(self, texto):
                if texto.strip():
                    t = texto.rstrip()
                    if "OK:" in t:
                        self.gui._log(t, "sucesso")
                    elif "ERRO" in t or "error" in t.lower():
                        self.gui._log(t, "erro")
                    elif t.startswith("[info]"):
                        self.gui._log(t, "destaque")
                    else:
                        self.gui._log(t)
                return len(texto)

        def _atualizar_progresso(idx_atual, total_cadernos):
            pct = int((idx_atual / total_cadernos) * 100)
            self.barra.setRange(0, 100)
            self.barra.setValue(pct)
            self.barra.setFormat(f"Caderno {idx_atual} de {total_cadernos} (%p%)")
            QApplication.processEvents()

        try:
            with contextlib.redirect_stdout(_LogWriter(self)):
                core.gerar_pdfs(
                    self.pdf_selecionado, pasta_saida,
                    tam_caderno=caderno, duplex=duplex,
                    paper=papel, modo_livro=modo,
                    preset=None if preset == "personalizado" else preset,
                    recortar_margens=recortar, juntar_tudo=juntar,
                    callback_progresso=_atualizar_progresso,
                )
            self.barra.setRange(0, 100)
            self.barra.setValue(100)
            self.barra.setFormat("Concluído (%p%)")
            self._log("=== Geração concluída com sucesso ===", "sucesso")
            QMessageBox.information(self, "Pronto",
                f"Cadernos gerados em:\n{pasta_saida}")
        except Exception as e:
            self.barra.setRange(0, 100)
            self.barra.setValue(0)
            self.barra.setFormat("Erro")
            self._log(f"ERRO: {e}", "erro")
            QMessageBox.critical(self, "Erro na geração",
                f"Ocorreu um erro:\n\n{e}")
        finally:
            self.botao_gerar.setEnabled(True)

    def _log(self, mensagem: str, tipo: str = "info"):
        cores = {
            "info":     "#E0E0E0",
            "sucesso":  "#4EC9B0",
            "erro":     "#F48771",
            "destaque": "#569CD6",
        }
        cor = cores.get(tipo, cores["info"])
        self.log.append(f'<span style="color:{cor};">{mensagem}</span>')


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BookBinder Brasil — Livreto")
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
