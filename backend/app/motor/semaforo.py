"""
==============================================================================
ARQUIVO: app/motor/semaforo.py
PAPEL: "O Consolidador de Prioridades e Tradutor para o 'Modo Avô'"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo recebe os resultados de todas as regras biológicas de regras.py,
decide qual delas é a mais importante no momento e traduz tudo em uma cor
simples (Verde, Amarelo ou Vermelho) acompanhada de uma frase clara e humana.

POR QUE ELE EXISTE SEPARADO?
Imagine a seguinte situação:
- A regra de colheita diz: "Pode colher mel! A caixa está cheia (VERDE)".
- Mas a regra do clima diz: "Está caindo uma tempestade com vento de 60 km/h (AMARELO)".
- E a regra de enxameação acabou de apitar: "Perda brusca de 2 kg (VERMELHO)".

Quem decide o que mostrar na tela do celular do apicultor? O semaforo.py!
Ele resolve esses conflitos aplicando a Hierarquia de Gravidade:
   VERMELHO (Urgência máxima) > AMARELO (Atenção/Incerteza) > VERDE (Tudo normal)

O QUE ELE FAZ NA PRÁTICA:
1. Resolução de Conflitos: Alerta de perigo (fome, enxameação) anula avisos festivos
   (colheita). A prioridade é sempre salvar a vida do enxame.
2. Mecanismo de Falha Segura (Fail-Safe): se o sinal da internet falhou e não temos
   dados de clima, ele rebaixa o status para AMARELO com aviso: "Dados meteorológicos
   indisponíveis, tome cuidado antes de abrir a caixa".
3. O 'Modo Avô': O apicultor no campo não quer gráficos complexos ou equações.
   Ele quer bater o olho e saber o que fazer:
   - Vermelho: "Suas abelhas estão sem comida! Alimente com xarope imediatamente."
   - Vermelho: "Possível enxameação: a caixa perdeu peso de repente."
   - Verde: "Dia favorável para abrir a caixa e fazer revisão."
   - Verde: "Hora da colheita! A melgueira está cheia."
==============================================================================
"""
