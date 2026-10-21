"""
==============================================================================
ARQUIVO: app/main.py
PAPEL: "A Chave de Ignição / O Ponto de Entrada da Aplicação"
==============================================================================

O QUE É ESTE ARQUIVO?
Este é o primeiro arquivo que o Python lê quando você digita o comando para iniciar
o servidor (ex: uvicorn app.main:app --reload). Ele é o ponto de partida de tudo.

POR QUE ELE EXISTE SEPARADO?
Em vez de misturar código de banco, rotas e regras aqui dentro, o main.py funciona
apenas como um organizador que aperta o botão de "Ligar" e conecta os módulos.

O QUE ELE FAZ NA PRÁTICA:
1. Cria a aplicação FastAPI: app = FastAPI(title="Biosaka API", ...).
2. Configura o CORS (Cross-Origin Resource Sharing):
   - Por segurança, os navegadores impedem que uma página web (ex: seu frontend React
     rodando na porta 5173 ou 3000) converse com uma API que está na porta 8000.
   - O CORS é o middleware que avisa ao navegador: "Pode confiar, libere as
     requisições que vierem do frontend do Biosaka".
3. Registra as Rotas: ele importa o arquivo 'rotas.py' e pluga na aplicação com
   app.include_router(...), fazendo com que todos os links fiquem ativos.
4. Ciclo de Vida (Lifespan): quando o servidor liga, ele pode conferir se as tabelas
   do banco de dados estão prontas; e quando desliga, fecha conexões pendentes.
==============================================================================
"""
