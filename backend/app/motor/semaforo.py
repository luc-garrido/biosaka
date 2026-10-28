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
from typing import List
from app.motor.tipos import (
    Semaforo,
    Confianca,
    CodigoRegra,
    ResultadoRegra,
    DiagnosticoFinal,
)

def consolidar_diagnostico(regras: List[ResultadoRegra]) -> DiagnosticoFinal:

    regras_vermelhas = [r for r in regras if r.semaforo == Semaforo.VERMELHO]
    regras_amarelas = [r for r in regras if r.semaforo == Semaforo.AMARELO]
    codigos = {r.codigo: r for r in regras}

    if regras_vermelhas:
        semaforo_final = Semaforo.VERMELHO
        if codigos.get(CodigoRegra.RF05) and codigos[CodigoRegra.RF05].semaforo == Semaforo.VERMELHO:
            frase = "Possível enxameação! A caixa perdeu abelhas de repente. Verifique árvores e galhos próximos."
        elif codigos.get(CodigoRegra.RF04) and codigos[CodigoRegra.RF04].semaforo == Semaforo.VERMELHO:
            frase = "Suas abelhas estão sem comida! Alimente com xarope imediatamente."
        else:
            frase = "Atenção crítica: verifique a colmeia imediatamente."

    elif regras_amarelas:
        semaforo_final = Semaforo.AMARELO
        if codigos.get(CodigoRegra.RF04) and codigos[CodigoRegra.RF04].semaforo == Semaforo.AMARELO and codigos[CodigoRegra.RF04].disparou:
            frase = "Atenção: reservas de alimento em declínio. Prepare alimentação de reforço."
        elif codigos.get(CodigoRegra.RF01) and codigos[CodigoRegra.RF01].semaforo == Semaforo.AMARELO:
            regra_clima = codigos[CodigoRegra.RF01]
            if "Insuficientes" in regra_clima.motivo:
                frase = "Dados meteorológicos indisponíveis. Tenha cautela ao abrir a caixa."
            elif regra_clima.disparou:
                frase = "Tempo desfavorável hoje (chuva, frio ou vento forte). Não abra a colmeia."
            else:
                frase = "Condições climáticas limítrofes. Faça apenas revisões rápidas ou aguarde o tempo firmar."
        elif codigos.get(CodigoRegra.RF03) and codigos[CodigoRegra.RF03].semaforo == Semaforo.AMARELO:
            frase = "A melgueira está em enchimento ativo. Aguarde a maturação completa para colher."
        else:
            frase = "Atenção: dados insuficientes da balança ou colmeia em observação."

    else:
        semaforo_final = Semaforo.VERDE
        if codigos.get(CodigoRegra.RF03) and codigos[CodigoRegra.RF03].disparou:
            frase = "Hora da colheita! A melgueira está cheia e o mel operculado."
        else:
            frase = "Tudo tranquilo no apiário. Colmeia saudável e com boas reservas."

    if any(r.confianca == Confianca.BAIXA for r in regras):
        confianca_geral = Confianca.BAIXA
    elif any(r.confianca == Confianca.MEDIA for r in regras):
        confianca_geral = Confianca.MEDIA
    else:
        confianca_geral = Confianca.ALTA

    return DiagnosticoFinal(
        semaforo=semaforo_final,
        frase_modo_avo=frase,
        detalhes_regras=regras,
        confianca=confianca_geral
    )

