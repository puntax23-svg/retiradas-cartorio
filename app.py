from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_from_directory
)

import sqlite3
import os

from datetime import datetime

# OCR
import fitz
import pytesseract

from PIL import Image

app = Flask(__name__)

# =====================================
# PASTA DE UPLOADS
# =====================================

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# =====================================
# CRIAR BANCO
# =====================================

conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS retiradas (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    destinatario TEXT,

    tipo_ato TEXT,

    retirado_por TEXT,

    data_retirada TEXT,

    escrevente TEXT,

    pdf TEXT

)

""")

conn.commit()
conn.close()

# =====================================
# OCR PDF
# =====================================

def ler_pdf_ocr(caminho_pdf):

    texto_total = ""

    pdf = fitz.open(caminho_pdf)

    for numero_pagina, pagina in enumerate(pdf):

        pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))

        imagem_path = f"pagina_{numero_pagina}.png"

        pix.save(imagem_path)

        imagem = Image.open(imagem_path)

        texto = pytesseract.image_to_string(
            imagem,
            lang="por"
        )

        texto_total += texto

        os.remove(imagem_path)

    return texto_total

# =====================================
# EXTRAIR DADOS OCR
# =====================================

def extrair_dados(texto):

    destinatario = ""
    tipo_ato = ""
    escrevente = ""

    linhas = texto.split("\n")

    for linha in linhas:

        linha_limpa = linha.strip()

        linha_upper = linha_limpa.upper()

        # =================================
        # DESTINATÁRIO
        # =================================

        if "DESTINAT" in linha_upper:

            if ":" in linha_limpa:

                partes = linha_limpa.split(":")

                if len(partes) > 1:

                    destinatario = partes[1].strip()

        # =================================
        # TIPO DO ATO
        # =================================

        if "ESCRITURA" in linha_upper:

            tipo_ato = linha_limpa

        # =================================
        # ESCREVENTE
        # =================================

        if "ESCREVENTE" in linha_upper:

            if ":" in linha_limpa:

                partes = linha_limpa.split(":")

                if len(partes) > 1:

                    escrevente = partes[1].strip()

    print("\n=========== TEXTO OCR ===========\n")

    print(texto)

    print("\n=========== DADOS EXTRAIDOS ===========\n")

    print("DESTINATARIO:", destinatario)

    print("ATO:", tipo_ato)

    print("ESCREVENTE:", escrevente)

    print("\n=======================================\n")

    return {
        "destinatario": destinatario,
        "tipo_ato": tipo_ato,
        "escrevente": escrevente
    }

# =====================================
# PÁGINA INICIAL
# =====================================

@app.route("/")
def inicio():

    return render_template("index.html")

# =====================================
# SALVAR RETIRADA
# =====================================

@app.route("/salvar", methods=["POST"])
def salvar():

    destinatario = request.form["destinatario"]

    tipo_ato = request.form["tipo_ato"]

    retirado_por = request.form["retirado_por"]

    data_retirada = request.form["data_retirada"]

    escrevente = request.form["escrevente"]

    arquivo = request.files["pdf"]

    nome_pdf = ""

    if arquivo:

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        nome_pdf = f"RET_{timestamp}.pdf"

        caminho = os.path.join(
            UPLOAD_FOLDER,
            nome_pdf
        )

        arquivo.save(caminho)

        # =====================================
        # OCR
        # =====================================

        texto_ocr = ler_pdf_ocr(caminho)

        dados = extrair_dados(texto_ocr)

        # =====================================
        # PREENCHIMENTO AUTOMÁTICO
        # =====================================

        if not destinatario:
            destinatario = dados["destinatario"]

        if not tipo_ato:
            tipo_ato = dados["tipo_ato"]

        if not escrevente:
            escrevente = dados["escrevente"]

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO retiradas (

        destinatario,
        tipo_ato,
        retirado_por,
        data_retirada,
        escrevente,
        pdf

    )

    VALUES (?, ?, ?, ?, ?, ?)

    """, (

        destinatario,
        tipo_ato,
        retirado_por,
        data_retirada,
        escrevente,
        nome_pdf

    ))

    conn.commit()
    conn.close()

    return redirect("/pesquisar")

# =====================================
# PESQUISAR
# =====================================

@app.route("/pesquisar")
def pesquisar():

    termo = request.args.get("termo", "")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""

    SELECT * FROM retiradas

    WHERE destinatario LIKE ?

    ORDER BY id DESC

    """, (f"%{termo}%",))

    retiradas = cursor.fetchall()

    conn.close()

    return render_template(
        "pesquisa.html",
        retiradas=retiradas
    )

# =====================================
# ABRIR PDF
# =====================================

@app.route("/pdf/<nome_pdf>")
def abrir_pdf(nome_pdf):

    return send_from_directory(
        "uploads",
        nome_pdf
    )

# =====================================
# INICIAR SERVIDOR
# =====================================

app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
)