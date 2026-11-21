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
import time
import httpx
from .motor.tipos import ContextoClima

# Dicionário de cache: (lat, lon) -> (tempo_em_que_expira, ContextoClima)
_CACHE_CLIMA = {}
TTL_CACHE_SEGUNDOS = 1800  # 1800 segundos = 30 minutos


def obter_clima_indisponivel() -> ContextoClima:
    """Devolve um objeto padrão indicando que os dados climáticos falharam."""
    return ContextoClima(
        temperatura_celsius=0.0,
        chovendo=False,
        vento_kmh=0.0,
        dados_confiaveis=False,
        umidade_pct=0.0,
    )

def consultar_clima(latitude: float, longitude: float) -> ContextoClima:
    # Arredonda para 2 casas para agrupar o apiário inteiro na mesma chave
    chave = (round(latitude, 2), round(longitude, 2))
    agora = time.time()

    # 1. VERIFICAÇÃO DE CACHE: Se já temos o clima e não expirou, devolve na hora!
    if chave in _CACHE_CLIMA:
        expira_em, contexto_salvo = _CACHE_CLIMA[chave]
        if agora < expira_em:
            return contexto_salvo

    url = "https://api.open-meteo.com/v1/forecast"
    parametros = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "auto",
    }

    try:
        resposta = httpx.get(url, params=parametros, timeout=5.0)

        if resposta.status_code == 200:
            dados = resposta.json().get("current", {})
            precipitacao = float(dados.get("precipitation", 0.0))

            contexto = ContextoClima(
                temperatura_celsius=float(dados.get("temperature_2m", 0.0)),
                chovendo=(precipitacao > 0.1),
                vento_kmh=float(dados.get("wind_speed_10m", 0.0)),
                dados_confiaveis=True,
                umidade_pct=float(dados.get("relative_humidity_2m", 0.0)),
            )

            # 2. SALVA NO CACHE: Guarda o resultado pelos próximos 30 minutos
            _CACHE_CLIMA[chave] = (agora + TTL_CACHE_SEGUNDOS, contexto)
            return contexto

    except Exception:
        pass

    return obter_clima_indisponivel()
