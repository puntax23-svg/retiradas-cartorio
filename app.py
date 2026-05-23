from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
import fitz
import pytesseract
from PIL import Image

app = Flask(__name__)

# =========================
# PASTAS
# =========================

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB = "banco.db"

# =========================
# CRIAR BANCO
# =========================

def criar_banco():

    conn = sqlite3.connect(DB)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retiradas (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT,

        ato TEXT,

        retirado_por TEXT,

        data_retirada TEXT,

        escrevente TEXT,

        arquivo TEXT
    )
    """)

    conn.commit()

    conn.close()

criar_banco()

# =========================
# OCR PDF
# =========================

def ler_pdf_ocr(caminho_pdf):

    texto_total = ""

    try:

        pdf = fitz.open(caminho_pdf)

        for pagina in pdf:

            texto = pagina.get_text()

            texto_total += texto + "\n"

        pdf.close()

    except Exception as erro:

        print("ERRO OCR:", erro)

    return texto_total

# =========================
# EXTRAIR DADOS
# =========================

def extrair_dados(texto):

    linhas = texto.split("\n")

    nome = ""

    ato = ""

    for linha in linhas:

        linha = linha.strip()

        if len(linha) > 10 and nome == "":

            nome = linha.upper()

        if "VENDA" in linha.upper():

            ato = "Venda e Compra"

        elif "PROCURA" in linha.upper():

            ato = "Procuração"

        elif "ATA" in linha.upper():

            ato = "Ata"

        elif "RECONHECIMENTO" in linha.upper():

            ato = "Reconhecimento"

    return nome, ato

# =========================
# HOME
# =========================

@app.route("/")
def index():

    termo = request.args.get("termo", "")

    conn = sqlite3.connect(DB)

    cursor = conn.cursor()

    if termo:

        cursor.execute("""
        SELECT * FROM retiradas
        WHERE

        nome LIKE ?

        OR retirado_por LIKE ?

        OR data_retirada LIKE ?

        OR ato LIKE ?

        OR escrevente LIKE ?

        ORDER BY id DESC
        """, (

            '%' + termo + '%',

            '%' + termo + '%',

            '%' + termo + '%',

            '%' + termo + '%',

            '%' + termo + '%'
        ))

    else:

        cursor.execute("""
        SELECT * FROM retiradas
        ORDER BY id DESC
        """)

    dados = cursor.fetchall()

    conn.close()

    return render_template(

        "index.html",

        dados=dados,

        termo=termo
    )

# =========================
# SALVAR
# =========================

@app.route("/salvar", methods=["POST"])
def salvar():

    nome = request.form.get("nome")

    ato = request.form.get("ato")

    retirado_por = request.form.get("retirado_por")

    data_retirada = request.form.get("data_retirada")

    escrevente = request.form.get("escrevente")

    arquivo = request.files.get("arquivo")

    nome_arquivo = ""

    if arquivo and arquivo.filename != "":

        nome_arquivo = secure_filename(arquivo.filename)

        caminho = os.path.join(

            UPLOAD_FOLDER,

            nome_arquivo
        )

        arquivo.save(caminho)

        try:

            texto_ocr = ler_pdf_ocr(caminho)

            nome_extraido, ato_extraido = extrair_dados(texto_ocr)

            if not nome:

                nome = nome_extraido

            if not ato:

                ato = ato_extraido

        except Exception as erro:

            print("ERRO OCR:", erro)

    conn = sqlite3.connect(DB)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO retiradas (

        nome,

        ato,

        retirado_por,

        data_retirada,

        escrevente,

        arquivo

    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (

        nome,

        ato,

        retirado_por,

        data_retirada,

        escrevente,

        nome_arquivo
    ))

    conn.commit()

    conn.close()

    return redirect("/")

# =========================
# DOWNLOAD PDF
# =========================

@app.route("/uploads/<arquivo>")
def uploads(arquivo):

    return send_from_directory(

        UPLOAD_FOLDER,

        arquivo
    )

# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
