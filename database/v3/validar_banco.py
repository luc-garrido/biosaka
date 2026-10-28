"""Verifica integridade no MySQL real com registros temporarios e ROLLBACK."""
import subprocess
import uuid
from pathlib import Path

COMPOSE = Path(__file__).with_name('compose.yaml')


def executar(sql):
    return subprocess.run(
        ['docker', 'compose', '-f', str(COMPOSE), 'exec', '-T', 'mysql',
         'sh', '-c', 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql '
         '-h 127.0.0.1 -u "$MYSQL_USER" -D "$MYSQL_DATABASE" --batch --skip-column-names'],
        input=sql, text=True, capture_output=True, timeout=30,
    )


def main():
    marca = uuid.uuid4().hex
    telefone = '+999' + str(int(marca[:8], 16)).zfill(10)
    base = f"""
START TRANSACTION;
INSERT INTO usuarios (nome, telefone, senha_hash)
VALUES ('teste-integridade-{marca}', '{telefone}', 'HASH_FICTICIO_SOMENTE_TESTE');
SET @u = LAST_INSERT_ID();
INSERT INTO apiarios (usuario_id, nome) VALUES (@u, 'Apiario de teste');
SET @a = LAST_INSERT_ID();
INSERT INTO colmeias (apiario_id, codigo) VALUES (@a, 'TESTE-01');
SET @c = LAST_INSERT_ID();
"""
    sucesso = executar(base + """
INSERT INTO inspecoes (colmeia_id, data_inspecao) VALUES (@c, '2017-01-01');
INSERT INTO series_dataset (colmeia_id, codigo, metrica, fonte_url,
    arquivo_origem, sha256_arquivo)
VALUES (@c, 'serie-teste', 'weight', 'https://example.invalid', 'teste.csv', REPEAT('a',64));
SET @s = LAST_INSERT_ID();
INSERT INTO leituras (serie_id, instante_original, valor_original,
    texto_valor_original, linha_origem)
VALUES (@s, '2017-01-01 05:15:00', 52.6974, '52.6974', 2),
       (@s, '2017-01-01 05:15:00', NULL, '', 3);
SELECT COUNT(*), SUM(valor_original IS NULL) FROM leituras WHERE serie_id = @s;
ROLLBACK;
""")
    if sucesso.returncode or sucesso.stdout.strip() != '2\t1':
        raise RuntimeError('Falha no fluxo relacional: ' + sucesso.stderr + sucesso.stdout)
    print('OK: cadeia usuario -> apiario -> colmeia -> serie -> leitura; timestamp repetido e valor ausente preservados.')
    casos = [
        ('telefone unico', f"INSERT INTO usuarios (nome,telefone,senha_hash) VALUES ('duplicado','{telefone}','teste');", '1062'),
        ('codigo unico por apiario', "INSERT INTO colmeias (apiario_id,codigo) VALUES (@a,'TESTE-01');", '1062'),
        ('chave estrangeira', "INSERT INTO inspecoes (colmeia_id,data_inspecao) VALUES (0,'2017-01-01');", '1452'),
        ('exclusao restringida', 'DELETE FROM apiarios WHERE id=@a;', '1451'),
        ('tara nao negativa', "INSERT INTO colmeias (apiario_id,codigo,peso_tara_kg) VALUES (@a,'TARA',-1);", '3819'),
        ('linha unica da serie', """INSERT INTO series_dataset (colmeia_id,codigo,metrica,fonte_url,arquivo_origem,sha256_arquivo)
            VALUES (@c,'serie-teste','weight','https://example.invalid','teste.csv',REPEAT('a',64));
            SET @s=LAST_INSERT_ID();
            INSERT INTO leituras (serie_id,instante_original,valor_original,linha_origem)
            VALUES (@s,'2017-01-01 00:00:00',1,2),(@s,'2017-01-01 00:01:00',2,2);""", '1062'),
    ]
    for nome, comando, codigo in casos:
        resultado = executar(base + comando + '\nROLLBACK;')
        # Ao falhar, o cliente encerra a conexao e o InnoDB desfaz a transacao.
        if resultado.returncode == 0 or f'ERROR {codigo}' not in resultado.stderr:
            raise RuntimeError(f'Falha em {nome}: {resultado.stderr}')
        print('OK:', nome)
    restante = executar(f"SELECT COUNT(*) FROM usuarios WHERE nome='teste-integridade-{marca}';")
    if restante.returncode or restante.stdout.strip() != '0':
        raise RuntimeError('Registros temporarios nao foram desfeitos.')
    print('OK: nenhum registro temporario permaneceu no banco.')


if __name__ == '__main__':
    main()
