"""
==============================================================================
ARQUIVO: app/rotas.py
PAPEL: "O Balcão de Atendimento / Os Endpoints HTTP da API"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo define as URLs da sua API. Ele é a única camada que "fala a língua
da Web" (o protocolo HTTP com GET, POST, PUT, DELETE).

POR QUE ELE EXISTE SEPARADO?
O papel de uma rota é ser simples e direta:
1. Receber a requisição que veio pela internet (do frontend ou do ESP32).
2. Usar os contratos de 'schemas.py' para validar se os dados estão certos.
3. Chamar a função correspondente em 'servicos.py' para fazer o trabalho pesado.
4. Responder com o status HTTP correto (200 OK, 201 Created, 404 Not Found).
A rota NÃO deve conter lógica matemática nem comandos SQL diretos.

AS ROTAS PRINCIPAIS DO BIOSAKA:
1. POST /leituras
   - Quem chama: A balança ESP32 enviando o peso medido em tempo real.
   - O que faz: Recebe o peso e dispara a avaliação de saúde da colmeia.

2. GET /colmeias
   - Quem chama: O aplicativo na tela inicial.
   - O que faz: Devolve a lista de todas as caixas cadastradas no apiário.

3. POST /colmeias
   - Quem chama: O apicultor cadastrando uma caixa nova no sistema.

4. POST /colmeias/{id}/manejo
   - Quem chama: O apicultor registrando uma ação de campo (colheu mel, alimentou).

5. GET /colmeias/{id}/status
   - Quem chama: A tela principal do "Modo Avô" no aplicativo.
   - O que faz: Devolve a cor do semáforo (Verde/Amarelo/Vermelho) e a frase de ação.
==============================================================================
"""
