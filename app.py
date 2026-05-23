<!DOCTYPE html>
<html lang="pt-br">
<head>

<meta charset="UTF-8">

<title>Fabio Contreras - Retiradas</title>

<style>

body{
    font-family: Arial;
    background:#f4f4f4;
}

.container{
    width:700px;
    margin:auto;
    margin-top:40px;
    background:white;
    padding:30px;
    border-radius:10px;
}

h1{
    text-align:center;
    margin-bottom:40px;
}

input{
    width:100%;
    padding:15px;
    margin-bottom:20px;
    border:1px solid #ccc;
    border-radius:5px;
    box-sizing:border-box;
}

button{
    width:100%;
    padding:15px;
    background:#2952d1;
    color:white;
    border:none;
    border-radius:5px;
    font-size:18px;
    cursor:pointer;
}

button:hover{
    background:#1d3ea3;
}

</style>

</head>

<body>

<div class="container">

<h1>FABIO CONTRERAS - RETIRADAS</h1>

<form id="formulario" enctype="multipart/form-data">

    <input
        type="text"
        name="nome"
        placeholder="Destinatário"
        required
    >

    <input
        type="text"
        name="ato"
        placeholder="Tipo do ato"
    >

    <input
        type="text"
        name="retirado_por"
        placeholder="Retirado por"
    >

    <input
        type="text"
        name="data_retirada"
        placeholder="Data retirada"
    >

    <input
        type="text"
        name="escrevente"
        placeholder="Escrevente"
    >

    <input
        type="file"
        name="arquivo"
        required
    >

    <button type="submit">
        Salvar Retirada
    </button>

</form>

</div>

<script>

document
.getElementById("formulario")
.addEventListener("submit", function(e){

    e.preventDefault();

    const formData = new FormData(this);

    fetch("/salvar", {
        method: "POST",
        body: formData
    })
    .then(response => {

        if(response.redirected){
            window.location.href = response.url;
        }else{
            alert("Erro ao salvar");
        }

    })
    .catch(error => {
        alert("Erro no envio");
        console.log(error);
    });

});

</script>

</body>
</html>
