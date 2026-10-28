"""Confere dados persistidos e prova recusa de arquivo alterado sem perda de dados."""
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

from importar_peso import PASTA, SERIE, preparar_sql
from validar_banco import executar


def resumo():
    resultado = executar("""
SELECT JSON_OBJECT('total',COUNT(*),'negativos',SUM(l.valor_original<0),
    'inicio',MIN(l.instante_original),'fim',MAX(l.instante_original),
    'checksum',MAX(s.sha256_arquivo),'serie_id',MAX(s.id))
FROM leituras l JOIN series_dataset s ON s.id=l.serie_id
WHERE s.codigo='""" + SERIE + "';")
    if resultado.returncode:
        raise RuntimeError(resultado.stderr)
    return json.loads(resultado.stdout.strip())


def main():
    antes = resumo()
    if antes['total'] != 524110 or antes['negativos'] != 507:
        raise RuntimeError('Contagens da importacao nao correspondem ao arquivo original.')
    print('OK: 524.110 leituras persistidas; 507 pesos negativos preservados.')
    repetidos = executar("""
SELECT COUNT(*) FROM (
 SELECT l.instante_original,COUNT(*) AS n
 FROM leituras l JOIN series_dataset s ON s.id=l.serie_id
 WHERE s.codigo='""" + SERIE + """'
 GROUP BY l.instante_original HAVING COUNT(*)>1
) AS repetidos;""")
    if repetidos.returncode or repetidos.stdout.strip() != '60':
        raise RuntimeError('Horarios repetidos nao foram preservados.')
    print('OK: 60 horarios repetidos preservados como linhas independentes.')
    # CSV pequeno e valido com checksum diferente: deve falhar antes de alterar a serie.
    with tempfile.TemporaryDirectory(prefix='verificar-import-', dir=PASTA) as temporario:
        zip_path = Path(temporario) / 'alterado.zip'
        sql_path = Path(temporario) / 'alterado.sql'
        with ZipFile(zip_path, 'w') as arquivo:
            arquivo.writestr('weight_2017.csv', 'timestamp,weight\n2017-01-01 05:15:00,999\n')
        preparar_sql(zip_path, sql_path)
        comando = ['docker','compose','-f',str(PASTA/'compose.yaml'),'exec','-T','mysql',
                   'sh','-c','MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -h 127.0.0.1 '
                   '-u "$MYSQL_USER" -D "$MYSQL_DATABASE" --batch --skip-column-names']
        with sql_path.open('rb') as entrada:
            resultado = subprocess.run(comando, stdin=entrada, capture_output=True, timeout=30)
        if resultado.returncode == 0 or b'ck_import_origem_inalterada' not in resultado.stderr:
            raise RuntimeError('Arquivo alterado nao foi bloqueado conforme esperado.')
    depois = resumo()
    if antes != depois:
        raise RuntimeError('Banco foi alterado pelo teste de arquivo conflitante.')
    print('OK: arquivo alterado rejeitado; serie e leituras originais mantidas.')
    print(json.dumps(depois, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
