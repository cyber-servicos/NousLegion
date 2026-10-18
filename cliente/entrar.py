#!/usr/bin/env python3
"""Entra no nosso servidor L2J como jogador, em modo texto.

Uso:
  python3 entrar.py <usuario> <senha> [--host 127.0.0.1] [--porta 2106]

Dentro do jogo, comandos (uma por linha):
  pos                      mostra posicao
  dizer <texto>            fala no chat geral
  mover <x> <y> <z>        anda ate a coordenada
  onde                     coordenadas de pontos uteis (Talking Island etc.)
  sair                     desloga e fecha
"""
from __future__ import annotations

import argparse
import os
import socket
import struct
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l2_client import full_connect, decode_string  # noqa: E402

PONTOS = {
    "talking_island": (-71417, 258270, -3104),
    "giran": (83352, 148104, -3400),
    "aden": (147450, 26740, -2200),
    "dion": (15670, 142983, -2700),
    "oren": (82956, 53162, -1490),
    "heine": (111115, 219042, -3540),
}


def descreve_pacote(raw: bytearray) -> str | None:
    if not raw:
        return None
    op = raw[0]
    if op == 0x4A and len(raw) > 10:  # CreatureSay
        try:
            ct = struct.unpack_from("<i", raw, 5)[0]
            nome, usado = decode_string(raw, 9)
            texto, _ = decode_string(raw, 9 + usado)
            return f"[chat {ct}] {nome or 'servidor'}: {texto}"
        except Exception:
            return None
    if op == 0x64 and len(raw) >= 5:  # SystemMessage
        try:
            sid = struct.unpack_from("<i", raw, 1)[0]
            return f"[sistema #{sid}]"
        except Exception:
            return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("usuario")
    ap.add_argument("senha")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--porta", type=int, default=2106)
    args = ap.parse_args()

    jogo = full_connect(args.usuario, args.senha, login_host=args.host, login_port=args.porta)
    if not jogo:
        print("Nao entrou. Servidor no ar? Login/senha certos? (conta 'in use' = reinicie o LoginServer)")
        return 1

    print(f"\n=== dentro do mundo como {jogo.name} ===")
    print(f"posicao ({jogo.x}, {jogo.y}, {jogo.z}) | comandos: pos, dizer, mover, onde, sair\n")

    vivo = True

    def leitor():
        nonlocal vivo
        jogo.sock.settimeout(1.0)
        while vivo:
            try:
                raw = jogo.recv_packet()
            except socket.timeout:
                continue
            except Exception:
                break
            linha = descreve_pacote(raw)
            if linha:
                print(linha)

    t = threading.Thread(target=leitor, daemon=True)
    t.start()

    try:
        while vivo:
            try:
                linha = input().strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not linha:
                continue
            cmd, _, resto = linha.partition(" ")
            if cmd == "sair":
                break
            if cmd == "pos":
                print(f"({jogo.x}, {jogo.y}, {jogo.z})")
            elif cmd == "onde":
                for nome, xyz in PONTOS.items():
                    print(f"  {nome:16s} {xyz[0]} {xyz[1]} {xyz[2]}")
            elif cmd == "dizer":
                jogo.send_chat(resto)
            elif cmd == "mover":
                try:
                    x, y, z = (int(v) for v in resto.split())
                except ValueError:
                    print("uso: mover <x> <y> <z>")
                    continue
                jogo.send_move(x, y, z)
                time.sleep(1.0)
            else:
                print("comandos: pos | dizer <texto> | mover <x> <y> <z> | onde | sair")
    finally:
        vivo = False
        jogo.close()
        print("deslogado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
