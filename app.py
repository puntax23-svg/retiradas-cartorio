from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
import fitz
import pytesseract
from PIL import Image

app = Flask(__name__)

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

    pdf = fitz.open(caminho_pdf)

    for pagina in pdf:

        pix = pagina.get_pixmap()

        imagem_path = "pagina_temp.png"

        pix.save(imagem_path)

        imagem = Image.open(imagem_path)

        texto = pytesseract.image_to_string(
            imagem,
            lang="por"
        )

        texto_total += texto + "\n"

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

        if len(linha) > 5 and nome == "":
            nome = linha.upper()

        if "ESCRITURA" in linha.upper():
            ato = linha

        elif "PROCURAÇÃO" in linha.upper():
            ato = linha

        elif "ATA" in linha.upper():
            ato = linha

        elif "RECONHECIMENTO" in linha.upper():
            ato = linha

    return nome, ato


# =========================
# HOME
# =========================

@app.route("/")
def index():

    return render_template("index.html")


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
    INSERT INTO retiradas
    (
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

    return redirect("/pesquisa")


# =========================
# PESQUISA
# =========================

@app.route("/pesquisa")
def pesquisa():

    termo = request.args.get("termo", "")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    if termo:

        cursor.execute("""
        SELECT * FROM retiradas
        WHERE nome LIKE ?
        ORDER BY id DESC
        """, ('%' + termo + '%',))

    else:

        cursor.execute("""
        SELECT * FROM retiradas
        ORDER BY id DESC
        """)

    dados = cursor.fetchall()

    conn.close()

    return render_template(
        "pesquisa.html",
        dados=dados,
        termo=termo
    )


# =========================
# DOWNLOAD PDF
# =========================

@app.route("/uploads/<arquivo>")
def uploads(arquivo):

    return send_from_directory(
        UPLOAD_FOLDER,
        arquivo
    )
