"""O comando humanim. Cada subcomando vive no seu módulo, com uma função main(args)."""
import argparse
import errno
import importlib
import sys

from .comum import RAIZ, Erro, comandos, ok


def novo(args):
    pasta = RAIZ / "videos" / args.slug
    if pasta.exists():
        raise Erro(f"videos/{args.slug}/ já existe. Escolha outro nome ou trabalhe nela.")
    (pasta / "cenas").mkdir(parents=True)
    (pasta / "dados").mkdir()
    ok(f"videos/{args.slug}/ criada. Próximo: a pesquisa (teoria.md, fontes.md e dados/, skill diretor), "
       f"depois roteiro.md (skill roteiro).")


def main():
    p = argparse.ArgumentParser(prog="humanim")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("novo", help="cria a pasta do vídeo")
    s.add_argument("slug")

    s = sub.add_parser("contar", help="duração de cada linha do roteiro e o segundo de cada gatilho")
    s.add_argument("roteiro", nargs="?")

    s = sub.add_parser("animar", help="renderiza as cenas na duração de cada fala")
    s.add_argument("roteiro", nargs="?")
    s.add_argument("--linha", type=int, action="append", help="só esta linha (pode repetir)")

    s = sub.add_parser("previa", help="abre a prévia no navegador")
    s.add_argument("pasta", nargs="?")
    s.add_argument("--nao-abrir", action="store_true", help="só gera, não abre o navegador")

    s = sub.add_parser("gravar", help="abre o teleprompter no navegador")
    s.add_argument("roteiro", nargs="?")
    s.add_argument("--porta", type=int, default=8765)
    s.add_argument("--nao-abrir", action="store_true", help="não abre o navegador sozinho")

    s = sub.add_parser("editar", help="corta pausas, muletas e repetições da fala gravada")
    s.add_argument("gravacao", nargs="?")

    s = sub.add_parser("tratar", help="remove o fundo da gravação")
    s.add_argument("gravacao", nargs="?")

    s = sub.add_parser("montar", help="junta gravação, tempos e animações")
    s.add_argument("pasta", nargs="?")

    s = sub.add_parser("frames", help="tira prints para a IA conferir")
    s.add_argument("video", nargs="?")

    args = p.parse_args()
    try:
        if args.comando == "novo":
            novo(args)
        else:
            importlib.import_module(f"humanim.{args.comando}").main(args)
    except Erro as e:
        print(f"ERRO {comandos(str(e))}", flush=True)
        sys.exit(1)
    except OSError as e:  # disco cheio, sem permissão, arquivo sumiu: também vira ERRO, não traceback
        causa = ("O disco está cheio: libere espaço (df -h .) e rode de novo." if e.errno == errno.ENOSPC else
                 "Confira o espaço em disco (df -h .) e as permissões, e rode de novo.")
        print(f"ERRO falha de arquivo: {e}. {causa}", flush=True)
        sys.exit(1)
    except KeyboardInterrupt:
        print("ERRO interrompido.", flush=True)
        sys.exit(130)


if __name__ == "__main__":
    main()
