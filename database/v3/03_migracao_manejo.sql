-- Migracao para bancos criados antes da coluna houve_manejo.
-- Os scripts 01/02 so rodam em volume vazio; este ALTER atualiza um banco existente
-- sem apagar dados. Rodar uma unica vez:
--   docker exec -i biosaka-v3-mysql-1 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" biosaka_v3_dev' < database/v3/03_migracao_manejo.sql
ALTER TABLE inspecoes
    ADD COLUMN houve_manejo BOOLEAN NOT NULL DEFAULT FALSE
    AFTER observacoes;
