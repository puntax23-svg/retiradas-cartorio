from flask import Flask, render_template, request, redirect
import sqlite3
import os
import fitz
import pytesseract
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# =========================
# CRIAR BANCO
# =========================

conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS retiradas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    ato TEXT,
    retirado_por TEXT,
    data_retirada TEXT,
    escrevente TEXT,
    arquivo TEXT,
    ocr TEXT
)
""")

conn.commit()
conn.close()

# =========================
# OCR PDF
# =========================

def ler_pdf_ocr(caminho):

    texto_total = ""

    pdf = fitz.open(caminho)

    for pagina in pdf:

        pix = pagina.get_pixmap()

        imagem_path = "temp.png"

        pix.save(imagem_path)

        texto = pytesseract.image_to_string(Image.open(imagem_path))

        texto_total += texto

    return texto_total

# =========================
# HOME
# =========================

@app.route("/")
def home():
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

    arquivo = request.files["arquivo"]

    nome_arquivo = arquivo.filename

    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)

    arquivo.save(caminho)

    texto_ocr = ler_pdf_ocr(caminho)

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO retiradas (
        nome,
        ato,
        retirado_por,
        data_retirada,
        escrevente,
        arquivo,
        ocr
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nome,
        ato,
        retirado_por,
        data_retirada,
        escrevente,
        nome_arquivo,
        texto_ocr
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

    resultados = []

    if termo != "":

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT nome, arquivo
        FROM retiradas
        WHERE nome LIKE ?
        """, ('%' + termo + '%',))

        resultados = cursor.fetchall()

        conn.close()

    html = """
    <html>
    <head>
    <title>Pesquisa</title>

    <style>

    body{
        font-family: Arial;
        background:#f4f4f4;
    }

    .container{
        width:800px;
        margin:auto;
        margin-top:50px;
    }

    input{
        width:80%;
        padding:15px;
    }

    button{
        padding:15px;
    }

    .item{
        background:white;
        padding:20px;
        margin-top:20px;
        border-radius:10px;
    }

    </style>

    </head>
    <body>

    <div class='container'>

    <h1>PESQUISA DE RETIRADAS</h1>

    <form>

    <input
        type='text'
        name='termo'
        placeholder='Pesquisar destinatário'
    >

    <button type='submit'>
        Pesquisar
    </button>

    </form>
    """

    for r in resultados:

        html += f"""
        <div class='item'>
            <b>{r[0]}</b><br><br>

            <a href='/uploads/{r[1]}' target='_blank'>
                Abrir PDF
            </a>
        </div>
        """

    html += "</div></body></html>"

    return html

# =========================
# SERVIR UPLOADS
# =========================

from flask import send_from_directory

@app.route('/uploads/<path:nome>')
def uploads(nome):
    return send_from_directory(UPLOAD_FOLDER, nome)

# =========================
# START
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
