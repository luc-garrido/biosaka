"""Inspecao reproduzivel do ZIP original; nao importa dados nem infere unidades."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile

BASE = Path(__file__).resolve().parents[2]
ARQUIVO = BASE / 'data' / 'raw' / 'beehive-metrics.zip'
SAIDA = Path(__file__).with_name('perfil_dataset.json')


def main():
    digest = hashlib.sha256()
    with ARQUIVO.open('rb') as entrada:
        for bloco in iter(lambda: entrada.read(1024 * 1024), b''):
            digest.update(bloco)
    relatorio = {
        'fonte': 'https://www.kaggle.com/datasets/se18m502/bee-hive-metrics',
        'sha256_zip': digest.hexdigest(),
        'observacao': 'Unidades e fuso horario nao inferidos dos valores.',
        'arquivos': [],
    }
    with ZipFile(ARQUIVO) as arquivo:
        for item in arquivo.infolist():
            if not item.filename.lower().endswith('.csv'):
                continue
            perfil = {'arquivo': item.filename, 'bytes': item.file_size,
                      'linhas': 0, 'ausentes': 0, 'numeros_invalidos': 0,
                      'timestamps_repetidos': 0, 'minimo': None, 'maximo': None,
                      'inicio': None, 'fim': None, 'amostras': []}
            vistos = set()
            pesos_vistos = {}
            repeticoes_peso = {'mesmo_valor': 0, 'valor_diferente': 0,
                               'amostras_conflitantes': []}
            with arquivo.open(item) as bruto:
                leitor = csv.DictReader(io.TextIOWrapper(bruto, encoding='utf-8-sig'))
                perfil['colunas'] = leitor.fieldnames
                if not leitor.fieldnames or len(leitor.fieldnames) != 2:
                    raise ValueError(f'Cabecalho inesperado: {item.filename}')
                metrica = leitor.fieldnames[1]
                for linha in leitor:
                    perfil['linhas'] += 1
                    if len(perfil['amostras']) < 3:
                        perfil['amostras'].append(linha)
                    instante = linha['timestamp']
                    if instante in vistos:
                        perfil['timestamps_repetidos'] += 1
                    vistos.add(instante)
                    perfil['inicio'] = min(perfil['inicio'] or instante, instante)
                    perfil['fim'] = max(perfil['fim'] or instante, instante)
                    valor = linha[metrica]
                    if item.filename == 'weight_2017.csv' and valor:
                        from decimal import Decimal
                        peso = Decimal(valor)
                        if instante in pesos_vistos:
                            anterior = pesos_vistos[instante]
                            chave = 'mesmo_valor' if peso == anterior else 'valor_diferente'
                            repeticoes_peso[chave] += 1
                            if peso != anterior and len(repeticoes_peso['amostras_conflitantes']) < 3:
                                repeticoes_peso['amostras_conflitantes'].append({
                                    'timestamp': instante, 'primeiro': str(anterior),
                                    'repetido': str(peso)})
                        else:
                            pesos_vistos[instante] = peso
                    if valor is None or not valor.strip():
                        perfil['ausentes'] += 1
                        continue
                    try:
                        numero = float(valor)
                        if not math.isfinite(numero):
                            raise ValueError('Nao finito')
                    except ValueError:
                        perfil['numeros_invalidos'] += 1
                        continue
                    perfil['minimo'] = numero if perfil['minimo'] is None else min(perfil['minimo'], numero)
                    perfil['maximo'] = numero if perfil['maximo'] is None else max(perfil['maximo'], numero)
            relatorio['arquivos'].append(perfil)
            if item.filename == 'weight_2017.csv':
                relatorio['repeticoes_weight_2017'] = repeticoes_peso
            print(item.filename, perfil['linhas'], 'linhas;',
                  perfil['ausentes'], 'ausentes;', perfil['timestamps_repetidos'],
                  'timestamps repetidos;', perfil['inicio'], 'a', perfil['fim'])
    SAIDA.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Relatorio:', SAIDA)


if __name__ == '__main__':
    main()
