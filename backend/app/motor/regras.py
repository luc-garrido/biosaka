"""
==============================================================================
ARQUIVO: app/motor/regras.py
PAPEL: "O Cérebro Biológico / Os 4 Especialistas em Abelhas"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo contém a lógica das 4 regras de negócio biológicas do Biosaka.
Cada função aqui dentro responde a uma pergunta específica sobre o estado da colmeia.

POR QUE ELE EXISTE SEPARADO?
Separar as regras biológicas do restante do sistema permite que você teste cada
cálculo isoladamente (usando o simulador.py) sem precisar ligar o banco de dados
e sem precisar de internet. É ciência apícola codificada em Python.

AS 4 REGRAS QUE FICAM AQUI:

1. RF01 - ABERTURA SEGURA DA CAIXA:
   - Pergunta: "O apicultor pode abrir a caixa hoje para fazer revisão?"
   - Lógica: Olha o clima. Se a temperatura for menor que 18°C, se estiver chovendo
     ou se o vento estiver forte, abrir a caixa esfria os favos e mata as larvas/crias.
   - Resposta: Bloqueia abertura se o clima for perigoso.

2. RF03 - PONTO DE COLHEITA DE MEL:
   - Pergunta: "O mel já está pronto para ser colhido?"
   - Lógica: Quando a melgueira está cheia, o peso para de subir e fica estável por
     alguns dias. Isso indica que as abelhas terminaram de desidratar o néctar e
     já fecharam os favos com cera (mel operculado / maduro).
   - Resposta: Sugere colheita se o peso atingiu o teto da capacidade.

3. RF04 - ALERTA DE FOME E ESGOTAMENTO DE RESERVAS:
   - Pergunta: "As abelhas estão sem comida?"
   - Lógica: Subtrai o peso da madeira da caixa (a tara). Se a reserva restante
     cair abaixo de 3.0 kg (ou estiver em queda diária contínua na entressafra),
     o enxame corre risco iminente de morte por inanição.
   - Resposta: Dispara alerta vermelho de alimentação urgente com xarope.

4. RF05 - ALERTA DE ENXAMEAÇÃO:
   - Pergunta: "As abelhas fugiram ou enxamearam?"
   - Lógica: Se a balança registrar uma perda brusca de peso (ex: queda de 1.5 kg a 3.0 kg
     em apenas 2 horas) E NÃO houver registro de que o apicultor foi lá colher mel,
     significa que a rainha velha foi embora levando metade da colônia com ela!
   - Resposta: Dispara alerta vermelho de enxameação imediata.
==============================================================================
"""
