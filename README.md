# 📚 BookBinder Brasil — Livreto

Transforma um arquivo PDF comum em cadernos prontos para encadernação artesanal (livreto).

Este é um aplicativo desktop moderno, escrito em Python, com interface gráfica, que funciona **sem precisar de Java ou terminal**. É uma reimplementação do clássico *BookBinder 3.0* (originalmente feito em Java/Jython).

## ✨ Funcionalidades

- **Interface em Português (PT-BR)**: Simples e intuitiva.
- **Multiplataforma**: Executáveis prontos para Windows (`.exe`) e Linux (binário).
- **Detecção Automática**: Identifica o tamanho do PDF e sugere o melhor formato de livro.
- **Presets de Livro**: A4 dobrado para A5, A5 para A6, Livro 16x23 cm, Bolso, etc.
- **Impressão Duplex**: Organiza as páginas para impressão frente e verso automática.
- **Instruções de Montagem**: Gera um arquivo de texto explicando como dobrar e grampear os cadernos.
- **Recorte de Margens**: Remove espaços brancos desnecessários do PDF original.
- **Numeração de Cadernos**: Opcional, ajuda a não errar a ordem na hora de montar.

## 🚀 Como usar

1. Baixe o executável na seção [Releases](https://github.com/marcossena10-rgb/bookbinder-brasil/releases).
   - **Windows**: Baixe e execute `bookbinder-brasil.exe`.
   - **Linux**: Baixe o binário, dê permissão de execução (`chmod +x bookbinder-brasil`) e execute.
2. Abra o programa e clique em **"Abrir PDF..."** (ou arraste o PDF para a janela).
3. Escolha o **Tamanho do livro** e as **Páginas por caderno** (o padrão 16 é recomendado).
4. Clique em **"Gerar cadernos"**.
5. Na pasta de saída, você encontrará os PDFs prontos para impressão e um arquivo `instrucoes_impressao.txt` com o passo a passo.

## 🛠️ Tecnologias

- Python 3
- PyMuPDF (Manipulação de PDF)
- PySide6 (Interface Gráfica Qt)
- PyInstaller (Empacotamento)

## 📄 Licença

Este projeto é uma reimplementação de código aberto, inspirada no BookBinder 3.0 original. Sinta-se livre para usar, modificar e compartilhar.
