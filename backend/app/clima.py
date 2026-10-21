"""
==============================================================================
ARQUIVO: app/clima.py
PAPEL: "O Termômetro na Janela / Integração com Meteorologia Externa"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo é o cliente que se conecta à internet para consultar uma API pública
de previsão do tempo (usamos a Open-Meteo, que é gratuita e não exige cartão de crédito).

POR QUE ELE EXISTE SEPARADO?
A saúde e o comportamento das abelhas dependem do ambiente externo:
- Se estiver muito frio (< 18°C) ou chovendo, as abelhas não saem e o apicultor não pode abrir.
- Se a colmeia perder peso num dia de sol, é forrageamento natural. Se perder peso
  numa semana de chuva contínua, é fome severa (estão comendo o mel estocado sem repor).

O QUE ELE FAZ NA PRÁTICA:
1. Consulta Externa: Recebe a latitude e a longitude do apiário e pergunta para a
   Open-Meteo: "Qual a temperatura, a velocidade do vento e a probabilidade de chuva agora?".
2. Cache em Memória com TTL (Time-To-Live):
   - A previsão do tempo não muda a cada 5 segundos.
   - Guardamos o resultado em memória por 30 a 60 minutos.
   - Assim, se 10 balanças mandarem leituras ao mesmo tempo, não precisamos fazer 10
     chamadas à internet; usamos o valor que já temos em cache, poupando tempo e banda.
3. Tratamento de Falha Segura (Fail-Safe):
   - Se a internet cair ou o serviço externo estiver fora do ar, o sistema NÃO quebra.
   - Ele devolve um aviso de dados indisponíveis, fazendo com que o motor acione o
     semáforo AMARELO por cautela até a conexão voltar.
==============================================================================
"""
