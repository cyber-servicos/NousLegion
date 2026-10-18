#!/usr/bin/env python3
"""Site + painel de contas do NousLegion.

Serve os arquivos estáticos desta pasta e uma API mínima que fala direto com o banco
do servidor (l2jmobius), igual ao que o LoginServer espera:
  senha = base64(sha1(senha))  — mesmo formato do L2J Interlude.

Endpoints:
  GET  /api/status              -> servidor no ar, jogadores online, clãs em guerra
  POST /api/register {login,password}
  POST /api/login    {login,password} -> personagens da conta

Uso:  ../venv/bin/python server.py [porta]
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pymysql

AQUI = Path(__file__).resolve().parent
ENV = Path(os.path.expanduser("~/estudos/l2j/run/db.env"))
BASE = {}
for linha in ENV.read_text().splitlines():
    if "=" in linha:
        k, v = linha.split("=", 1)
        BASE[k.strip()] = v.strip()

LOGIN_RE = re.compile(r"^[A-Za-z0-9]{4,16}$")


def db():
    return pymysql.connect(
        host=BASE.get("DB_HOST", "127.0.0.1"),
        port=int(BASE.get("DB_PORT", 3306)),
        user=BASE.get("DB_USER", "l2j"),
        password=BASE.get("DB_PASS", ""),
        database=BASE.get("DB_NAME", "l2jmobius"),
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def hash_senha(senha: str) -> str:
    return base64.b64encode(hashlib.sha1(senha.encode("utf-8")).digest()).decode("ascii")


def registra(login: str, senha: str) -> dict:
    if not LOGIN_RE.match(login):
        return {"ok": False, "erro": "login: 4 a 16 caracteres, só letras e números"}
    if not (4 <= len(senha) <= 16):
        return {"ok": False, "erro": "senha: 4 a 16 caracteres"}
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT login FROM accounts WHERE login = %s", (login,))
        if cur.fetchone():
            return {"ok": False, "erro": "esse login já existe"}
        cur.execute(
            "INSERT INTO accounts (login, password, accessLevel, lastactive) VALUES (%s, %s, 0, 0)",
            (login, hash_senha(senha)),
        )
    return {"ok": True, "login": login, "msg": "conta criada — já pode entrar no jogo"}


def autentica(login: str, senha: str) -> dict:
    with db() as con, con.cursor() as cur:
        cur.execute(
            "SELECT login, password, accessLevel FROM accounts WHERE login = %s", (login,)
        )
        conta = cur.fetchone()
        if not conta or conta["password"] != hash_senha(senha):
            return {"ok": False, "erro": "login ou senha errados"}
        cur.execute(
            "SELECT char_name, level, pvpkills, pkkills, online, clanid FROM characters"
            " WHERE account_name = %s ORDER BY level DESC",
            (login,),
        )
        chars = cur.fetchall()
        cla_nome = {}
        ids = [c["clanid"] for c in chars if c["clanid"]]
        if ids:
            fmt = ",".join(["%s"] * len(ids))
            cur.execute(f"SELECT clan_id, clan_name FROM clan_data WHERE clan_id IN ({fmt})", ids)
            cla_nome = {r["clan_id"]: r["clan_name"] for r in cur.fetchall()}
    for c in chars:
        c["clan"] = cla_nome.get(c["clanid"], "")
        c.pop("clanid", None)
    return {
        "ok": True,
        "login": conta["login"],
        "gm": conta["accessLevel"] >= 100,
        "personagens": chars,
    }


def status() -> dict:
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM characters WHERE online = 1")
        online = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM clan_wars")
        guerras = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM accounts")
        contas = cur.fetchone()["n"]
    return {"servidor": "online", "jogadores": online, "guerras": guerras, "contas": contas}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(AQUI), **kw)

    def log_message(self, fmt, *args):  # log curto, sem query string
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, dados: dict, codigo: int = 200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self) -> dict:
        tam = int(self.headers.get("Content-Length") or 0)
        if tam <= 0 or tam > 4096:
            return {}
        try:
            return json.loads(self.rfile.read(tam).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        if self.path.startswith("/api/status"):
            try:
                return self._json(status())
            except Exception as exc:
                return self._json({"erro": f"banco indisponível: {exc}"}, 503)
        return super().do_GET()

    def do_POST(self):
        dados = self._corpo()
        login = (dados.get("login") or "").strip()
        senha = (dados.get("password") or "").strip()
        try:
            if self.path.startswith("/api/register"):
                r = registra(login, senha)
                return self._json(r, 200 if r["ok"] else 400)
            if self.path.startswith("/api/login"):
                r = autentica(login, senha)
                return self._json(r, 200 if r["ok"] else 401)
        except Exception as exc:
            return self._json({"ok": False, "erro": f"banco indisponível: {exc}"}, 503)
        return self._json({"ok": False, "erro": "rota desconhecida"}, 404)


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"site em http://0.0.0.0:{porta}  (api: /api/status /api/register /api/login)")
    ThreadingHTTPServer(("0.0.0.0", porta), Handler).serve_forever()
