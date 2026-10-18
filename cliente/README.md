# Cliente L2J Interlude em modo texto (headless)

Entra no NOSSO servidor (~/estudos/l2j) sem cliente gráfico da NCSoft: fala o protocolo
do jogo em Python. Não é o jogo com imagem — é o jogo por baixo: login, personagem,
posição, chat, pacotes.

## Instalar

    ./instalar.sh
    # cria .venv e instala pycryptodome

## Entrar

Servidor precisa estar no ar (`~/estudos/l2j/scripts/server.sh status`).

    ./.venv/bin/python entrar.py mrrobot <SENHA>

A senha da conta mrrobot está em `~/estudos/l2j/run/contas.env` (arquivo 600, campo
JOINHA_PASS). Não é para circular em chat.

Para conectar de outra máquina na mesma rede:

    ./.venv/bin/python entrar.py mrrobot <SENHA> --host 192.168.0.86

## Comandos dentro do jogo

    pos                    mostra sua posição
    dizer <texto>          fala no chat
    mover <x> <y> <z>      anda até a coordenada
    onde                   coordenadas de cidades úteis
    sair                   desloga

## Limites conhecidos (honestos)

- Sem gráfico: você lê a posição, o chat e as mensagens de sistema. Não vê o boneco.
- Broadcast de chat entre dois clientes headless ainda não chega (bug em investigação).
  Mensagens de sistema e pacotes de mundo chegam normalmente.
- Se o login falhar com "in use", o LoginServer guardou a sessão anterior: reinicie com
  `~/estudos/l2j/scripts/server.sh stop && ~/estudos/l2j/scripts/server.sh start`.
- O cliente da NCSoft (o jogo de verdade, com tela) não vem aqui e não é distribuído por mim.
