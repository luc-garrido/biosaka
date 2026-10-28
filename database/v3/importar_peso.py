"""Importa weight_2017.csv no MySQL Docker, sem dependencias Python externas.

Valida todo o CSV antes de escrever no banco. A transacao compara registros
existentes, insere somente linhas ausentes e verifica equivalencia integral.
"""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

PASTA = Path(__file__).resolve().parent
ZIP_PADRAO = PASTA.parents[1] / 'data' / 'raw' / 'beehive-metrics.zip'
FONTE = 'https://www.kaggle.com/datasets/se18m502/bee-hive-metrics'
CSV = 'weight_2017.csv'
SERIE = 'beehive-metrics-v3-wurzburg-weight-2017'
TELEFONE_DEMO = '+9990000000000'
NOME_DEMO = 'Demonstracao Beehive Metrics - sem login'
HASH_BLOQUEADO = '!CONTA_DEMONSTRACAO_BLOQUEADA'


def literal(texto):
    """Literal hexadecimal UTF-8; nao interpreta aspas ou escapes do CSV."""
    if texto == '':
        return "''"
    return "CONVERT(0x" + texto.encode('utf-8').hex() + ' USING utf8mb4)'


def validar_linha(linha, numero):
    if set(linha) != {'timestamp', 'weight'} or any(v is None for v in linha.values()):
        raise ValueError(f'Linha {numero}: quantidade de colunas invalida.')
    instante = linha['timestamp']
    try:
        data = datetime.strptime(instante, '%Y-%m-%d %H:%M:%S')
    except ValueError as erro:
        raise ValueError(f'Linha {numero}: timestamp invalido.') from erro
    if data.strftime('%Y-%m-%d %H:%M:%S') != instante or data.year != 2017:
        raise ValueError(f'Linha {numero}: data fora do formato/ano esperado.')
    original = linha['weight']
    if len(original) > 100:
        raise ValueError(f'Linha {numero}: valor original excede 100 caracteres.')
    if not original.strip():
        return instante, 'NULL', original
    try:
        valor = Decimal(original)
    except InvalidOperation as erro:
        raise ValueError(f'Linha {numero}: peso nao numerico.') from erro
    if not valor.is_finite() or abs(valor) >= Decimal('1000000000000'):
        raise ValueError(f'Linha {numero}: peso fora do dominio DECIMAL(24,12).')
    return instante, format(valor, 'f'), original


def exigir(saida, nome, condicao):
    # CREATE/DROP TEMPORARY TABLE nao realiza commit implicito no MySQL.
    saida.write(f'CREATE TEMPORARY TABLE assert_{nome} (ok TINYINT NOT NULL, '
                f'CONSTRAINT ck_import_{nome} CHECK (ok=1)) ENGINE=InnoDB;\n'
                f'INSERT INTO assert_{nome} VALUES (COALESCE(({condicao}),0));\n'
                f'DROP TEMPORARY TABLE assert_{nome};\n')


def preparar_sql(zip_path, sql_path):
    with ZipFile(zip_path) as arquivo:
        if arquivo.namelist().count(CSV) != 1:
            raise ValueError(f'O ZIP deve conter exatamente um {CSV}.')
        checksum = hashlib.sha256()
        with arquivo.open(CSV) as entrada:
            for bloco in iter(lambda: entrada.read(1024 * 1024), b''):
                checksum.update(bloco)
        sha = checksum.hexdigest()
        perfil = {'arquivo': CSV, 'sha256_arquivo': sha, 'fonte_url': FONTE,
                  'unidade': 'kg', 'fuso': None, 'linhas': 0, 'ausentes': 0,
                  'pesos_negativos': 0, 'pesos_zero': 0,
                  'inicio': None, 'fim': None}
        with sql_path.open('w', encoding='utf-8', newline='\n') as saida:
            saida.write("SET SESSION time_zone='+00:00';\n"
                        "SET SESSION sql_mode='STRICT_ALL_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';\n"
                        "SET @lock_import=GET_LOCK('biosaka_import_weight_2017',15);\n")
            exigir(saida, 'lock', '@lock_import=1')
            saida.write('START TRANSACTION;\n')
            saida.write('INSERT INTO usuarios (nome,telefone,senha_hash) SELECT '
                        f'{literal(NOME_DEMO)},{literal(TELEFONE_DEMO)},{literal(HASH_BLOQUEADO)} '
                        f'WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE telefone={literal(TELEFONE_DEMO)});\n'
                        f'SET @u=(SELECT id FROM usuarios WHERE telefone={literal(TELEFONE_DEMO)});\n')
            exigir(saida, 'conta_demo', f"EXISTS(SELECT 1 FROM usuarios WHERE id=@u AND nome={literal(NOME_DEMO)} AND senha_hash={literal(HASH_BLOQUEADO)})")
            nome_apiario = literal('Beehive Metrics - historico Wurzburg')
            saida.write('INSERT INTO apiarios (usuario_id,nome,localizacao) '
                        f'SELECT @u,{nome_apiario},{literal("Wurzburg, Alemanha - dados historicos HOBOS")} '
                        f'WHERE NOT EXISTS (SELECT 1 FROM apiarios WHERE usuario_id=@u AND nome={nome_apiario});\n')
            exigir(saida, 'apiario_unico', f'(SELECT COUNT(*) FROM apiarios WHERE usuario_id=@u AND nome={nome_apiario})=1')
            saida.write(f'SET @a=(SELECT id FROM apiarios WHERE usuario_id=@u AND nome={nome_apiario});\n'
                        "INSERT INTO colmeias (apiario_id,codigo) SELECT @a,'WURZBURG-2017' "
                        "WHERE NOT EXISTS (SELECT 1 FROM colmeias WHERE apiario_id=@a AND codigo='WURZBURG-2017');\n"
                        "SET @c=(SELECT id FROM colmeias WHERE apiario_id=@a AND codigo='WURZBURG-2017');\n")
            saida.write('INSERT INTO series_dataset (colmeia_id,codigo,metrica,fonte_url,arquivo_origem,sha256_arquivo,unidade_original) '
                        f"SELECT @c,{literal(SERIE)},'weight',{literal(FONTE)},{literal(CSV)},{literal(sha)},'kg' "
                        f'WHERE NOT EXISTS (SELECT 1 FROM series_dataset WHERE codigo={literal(SERIE)});\n'
                        f'SET @s=(SELECT id FROM series_dataset WHERE codigo={literal(SERIE)});\n')
            exigir(saida, 'origem_inalterada',
                   f"EXISTS(SELECT 1 FROM series_dataset WHERE id=@s AND colmeia_id=@c AND metrica='weight' "
                   f"AND arquivo_origem={literal(CSV)} AND sha256_arquivo={literal(sha)} "
                   f"AND fonte_url={literal(FONTE)} AND unidade_original='kg' AND fuso_original IS NULL)")
            saida.write('SET @antes=(SELECT COUNT(*) FROM leituras WHERE serie_id=@s);\n'
                        'CREATE TEMPORARY TABLE stage_peso ('
                        'linha INT UNSIGNED PRIMARY KEY, instante DATETIME NOT NULL, '
                        'valor DECIMAL(24,12) NULL, original VARCHAR(100) NOT NULL) ENGINE=InnoDB;\n')
            lote = []
            with arquivo.open(CSV) as entrada:
                leitor = csv.DictReader(io.TextIOWrapper(entrada, encoding='utf-8-sig', newline=''))
                if leitor.fieldnames != ['timestamp', 'weight']:
                    raise ValueError('Cabecalho inesperado: esperado timestamp,weight.')
                for numero, linha in enumerate(leitor, 2):
                    instante, valor, original = validar_linha(linha, numero)
                    perfil['linhas'] += 1
                    perfil['ausentes'] += valor == 'NULL'
                    if valor != 'NULL':
                        perfil['pesos_negativos'] += Decimal(valor) < 0
                        perfil['pesos_zero'] += Decimal(valor) == 0
                    perfil['inicio'] = min(perfil['inicio'] or instante, instante)
                    perfil['fim'] = max(perfil['fim'] or instante, instante)
                    lote.append(f"({numero},'{instante}',{valor},{literal(original)})")
                    if len(lote) == 1000:
                        saida.write('INSERT INTO stage_peso VALUES ' + ','.join(lote) + ';\n')
                        lote.clear()
            if lote:
                saida.write('INSERT INTO stage_peso VALUES ' + ','.join(lote) + ';\n')
            if perfil['linhas'] == 0:
                raise ValueError('CSV vazio.')
            exigir(saida, 'sem_linhas_extras',
                   'NOT EXISTS(SELECT 1 FROM leituras l LEFT JOIN stage_peso p ON p.linha=l.linha_origem '
                   'WHERE l.serie_id=@s AND p.linha IS NULL)')
            comparacao = ('l.instante_original=p.instante AND (l.valor_original <=> p.valor) '
                          'AND (BINARY l.texto_valor_original <=> BINARY p.original)')
            exigir(saida, 'conteudo_existente',
                   'NOT EXISTS(SELECT 1 FROM leituras l JOIN stage_peso p ON p.linha=l.linha_origem '
                   f'WHERE l.serie_id=@s AND NOT ({comparacao}))')
            saida.write('INSERT INTO leituras (serie_id,instante_original,valor_original,texto_valor_original,linha_origem) '
                        'SELECT @s,p.instante,p.valor,p.original,p.linha FROM stage_peso p '
                        'LEFT JOIN leituras l ON l.serie_id=@s AND l.linha_origem=p.linha '
                        'WHERE l.id IS NULL ORDER BY p.linha;\nSET @inseridas=ROW_COUNT();\n')
            exigir(saida, 'total_final', f'(SELECT COUNT(*) FROM leituras WHERE serie_id=@s)={perfil["linhas"]}')
            exigir(saida, 'equivalencia_final',
                   f'(SELECT COUNT(*) FROM stage_peso p JOIN leituras l ON l.serie_id=@s '
                   f'AND l.linha_origem=p.linha WHERE {comparacao})={perfil["linhas"]}')
            saida.write('COMMIT;\nSELECT JSON_OBJECT(\'serie_id\',@s,\'colmeia_id\',@c,'
                        "'antes',@antes,'inseridas',@inseridas,'depois',"
                        '(SELECT COUNT(*) FROM leituras WHERE serie_id=@s));\n'
                        "DO RELEASE_LOCK('biosaka_import_weight_2017');\n")
    return perfil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, default=ZIP_PADRAO)
    parser.add_argument('--validar-apenas', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='import-peso-', dir=PASTA) as temporario:
        sql = Path(temporario) / 'importacao.sql'
        perfil = preparar_sql(args.zip, sql)
        print(f"CSV validado: {perfil['linhas']} linhas; SHA256 {perfil['sha256_arquivo']}", flush=True)
        if args.validar_apenas:
            print(json.dumps(perfil, ensure_ascii=False, indent=2))
            return
        comando = ['docker', 'compose', '-f', str(PASTA / 'compose.yaml'), 'exec', '-T', 'mysql',
                   'sh', '-c', 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -h 127.0.0.1 '
                   '-u "$MYSQL_USER" -D "$MYSQL_DATABASE" --default-character-set=utf8mb4 '
                   '--batch --skip-column-names']
        with sql.open('rb') as entrada:
            resultado = subprocess.run(comando, stdin=entrada, capture_output=True, timeout=300)
        if resultado.returncode:
            raise RuntimeError('Importacao interrompida; confira o estado antes de repetir. '
                               'Falhas antes do COMMIT desfazem a transacao.\n' +
                               resultado.stderr.decode('utf-8', errors='replace'))
        resumo = json.loads(resultado.stdout.decode('utf-8').strip())
        relatorio = {**perfil, **resumo, 'executado_em_utc': datetime.now(timezone.utc).isoformat(),
                     'verificacao': 'Todas as linhas comparadas em MySQL: data, valor decimal e texto original.',
                     'precisao': 'DECIMAL(24,12); texto original preserva precisao adicional.',
                     'conta_demo': 'Conta tecnica bloqueada para login; telefone sintetico.'}
        (PASTA / 'importacao_peso.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
        with (PASTA / 'historico_importacao.jsonl').open('a', encoding='utf-8') as historico:
            historico.write(json.dumps(relatorio, ensure_ascii=False) + '\n')
        print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
