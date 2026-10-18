# NousLegion — servidor Lineage 2 Interlude (C6)

Site estático + painel de contas do servidor **NousLegion**: L2J Mobius `CT_0_Interlude`
(GPL), protocolo **746**, rate **x1**, sem loja e sem venda de item.

    Emulador ....... L2J_Mobius_CT_0_Interlude · commit 5ddd6ff (14/10/2026)
    Runtime ........ OpenJDK 27 · MariaDB 11.8
    Login / Game ... :2106 · :7777
    Clãs ........... NousLegion (lvl 5) × BlackCrew (lvl 5) — guerra declarada em jogo

## Estrutura

    index.html      landing page (topbar, hero, começar, conta, rates, download, rankings, guerra, FAQ)
    server.py       serve o site E a API de contas (login/registro) falando direto com o banco
    img/hero.jpg    arte do hero
    cliente/        fonte do cliente de texto (o download servido é l2j-cliente-texto.tar.gz)

## Rodar

O painel de contas precisa do `server.py`, que conversa com o MySQL do servidor:

    ../venv/bin/python server.py 8080     # http://ip-da-maquina:8080

Credenciais do banco vêm de `~/estudos/l2j/run/db.env` (fora deste repositório, chmod 600).
No GitHub Pages só o site estático funciona — a aba Conta avisa "API offline" porque Pages
não executa código no servidor.

## API

    GET  /api/status                        → servidor, jogadores online, guerras, contas
    POST /api/register  {"login","password"} → cria conta (mesmo hash do LoginServer)
    POST /api/login     {"login","password"} → valida e lista personagens/clã/PvP

Senha é gravada como `base64(sha1(senha))`, exatamente o formato que o L2J Interlude espera —
então a conta criada no site loga no jogo sem passo extra. Verificado ponta a ponta:
conta criada pela API → LoginOk + PlayOk no LoginServer.

## Limites (honestos)

- Sem cliente gráfico: o cliente do jogo é da NCSoft e não é distribuído aqui.
- Servidor na LAN, sem porta aberta no roteador — não é servidor público.
- Broadcast de chat entre clientes headless ainda não chega (bug aberto).
- Lineage 2 é marca da NCSoft. Emulador GPL. Projeto não afiliado.
