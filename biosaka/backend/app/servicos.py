"""
==============================================================================
ARQUIVO: app/servicos.py
PAPEL: "O Maestro Orquestrador / A Regra de Negócio da Aplicação"
==============================================================================

O QUE É ESTE ARQUIVO?
Este é o arquivo que junta todas as peças do quebra-cabeça. Ele não sabe falar
HTTP (isso é papel das rotas) e não sabe fazer matemática pura (isso é papel do motor).
O papel dele é ser o GERENTE: coordenar quem faz o quê e em qual ordem.

POR QUE ELE EXISTE SEPARADO?
Imagine o fluxo de quando a balança ESP32 manda um novo peso:
1. Alguém precisa salvar esse peso no banco de dados.
2. Alguém precisa buscar o histórico de pesos dos últimos 7 dias.
3. Alguém precisa conferir se o apicultor mexeu na caixa hoje cedo.
4. Alguém precisa ligar para o serviço de clima e pegar a temperatura lá fora.
5. Alguém precisa passar esses dados para o motor biológico calcular o semáforo.
6. Alguém precisa atualizar a tabela de 'EstadoAtual' com o novo resultado.

Se colocássemos tudo isso dentro de uma rota em 'rotas.py', o código ficaria gigante,
confuso e impossível de testar. Em 'servicos.py', organizamos esse fluxo em funções
limpas como 'processar_nova_leitura()' e 'registrar_manejo()'.

AS PRINCIPAIS FUNÇÕES QUE FICAM AQUI:
- processar_nova_leitura(db, leitura_in):
  Orquestra todo o fluxo acima sempre que uma nova pesagem chega.

- registrar_manejo(db, evento_in):
  Grava a ação do apicultor (ex: colheita de 15 kg) para que o motor saiba que a perda
  de peso foi humana e não uma fuga de enxame.
==============================================================================
"""
