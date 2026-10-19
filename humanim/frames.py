"""humanim frames: tira prints do vídeo para a IA conferir."""
import re
import shutil
from pathlib import Path

from .comum import Erro, ok, pasta_do_video, rodar
from .formato import FPS
from .montar import contar_quadros
from .roteiro import ler_roteiro, ler_tempos, quadros

TAMANHO = "540:960"


def extrair(video, indices, destinos):
    """Salva os quadros de número `indices` em `destinos` (PNG 540x960), numa passada só pelo vídeo."""
    pasta = destinos[0].parent
    unicos = sorted(set(indices))
    selecao = "+".join(f"eq(n\\,{i})" for i in unicos)
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", video, "-vf", f"select={selecao},scale={TAMANHO}",
           "-fps_mode", "passthrough", pasta / "_%03d.png"], f"tirar prints de {video.name}")
    for i, destino in zip(indices, destinos):
        shutil.copy(pasta / f"_{unicos.index(i) + 1:03d}.png", destino)
    for p in pasta.glob("_*.png"):
        p.unlink()


def prints_da_cena(video, numero):
    """Clipe de uma cena: início, meio e fim, para ver a animação sem montar o vídeo."""
    pasta = video.parent.parent / "frames"
    pasta.mkdir(exist_ok=True)
    for velho in pasta.glob(f"cena_{numero:02d}_*.png"):
        velho.unlink()
    n = contar_quadros(video)
    indices = [min(n - 1, int(n * f)) for f in (0.10, 0.50, 0.95)]
    destinos = [pasta / f"cena_{numero:02d}_{nome}.png" for nome in ("inicio", "meio", "fim")]
    extrair(video, indices, destinos)
    lista = "\n".join(f"{d.name}  {i / FPS:.2f}s" for d, i in zip(destinos, indices))
    ok(f"3 prints de cenas/{video.name} ({n} quadros, {n / FPS:.2f}s) em {pasta}/ (540x960):\n{lista}")


def prints_por_linha(video):
    """Vídeo montado: um print no meio de cada linha do roteiro."""
    pasta = pasta_do_video(video)
    linhas = ler_roteiro(pasta)
    tempos, _ = ler_tempos(pasta, linhas)
    contagens = quadros(tempos)
    tem = contar_quadros(video)
    if abs(tem - sum(contagens)) > 1:
        raise Erro(f"{video.name} tem {tem} quadros, mas roteiro.md com tempos.json pede {sum(contagens)}: "
                   f"o vídeo é de antes da última mudança. Rode humanim montar de novo.")
    destino = pasta / "frames"
    shutil.rmtree(destino, ignore_errors=True)
    destino.mkdir()
    indices, inicio = [], 0
    for n in contagens:
        indices.append(min(tem - 1, inicio + n // 2))
        inicio += n
    destinos = [destino / f"{linha.cena}_{linha.marca.lower()}.png" for linha in linhas]
    extrair(video, indices, destinos)
    lista = "\n".join(f"{d.name}  {i / FPS:.2f}s  {linha.descricao or 'você em tela cheia'}"
                      for d, i, linha in zip(destinos, indices, linhas))
    ok(f"{len(destinos)} prints de {video.name} em {destino}/ (540x960), um no meio de cada linha. "
       f"Olhe cada um e confira com o roteiro:\n{lista}")


def main(args):
    video = Path(args.video).resolve() if args.video else pasta_do_video() / "saida.mp4"
    if not video.exists():
        raise Erro(f"{video} não existe. Rode humanim montar antes (ou passe o vídeo certo).")
    cena = re.fullmatch(r"linha_(\d+)\.mp4", video.name)
    if cena and video.parent.name == "cenas":
        prints_da_cena(video, int(cena.group(1)))
    else:
        prints_por_linha(video)
