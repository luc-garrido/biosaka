"""Reinicia somente o MySQL do BIOSAKA e compara o resumo antes/depois."""
import json
import subprocess

from importar_peso import PASTA
from verificar_importacao import resumo


def main():
    antes = resumo()
    compose = ['docker', 'compose', '-f', str(PASTA / 'compose.yaml')]
    for argumentos in [['restart', 'mysql'], ['up', '-d', '--wait', '--wait-timeout', '90', 'mysql']]:
        resultado = subprocess.run(compose + argumentos, capture_output=True, text=True, timeout=120)
        if resultado.returncode:
            raise RuntimeError(resultado.stderr)
    depois = resumo()
    if antes != depois or depois['total'] != 524110:
        raise RuntimeError('Dados apos reinicio nao correspondem ao resumo anterior.')
    print('OK: 524.110 leituras preservadas apos reiniciar o MySQL.')
    print(json.dumps(depois, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
