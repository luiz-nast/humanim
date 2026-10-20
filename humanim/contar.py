"""humanim contar: quanto dura cada linha do roteiro e em que segundo cai cada gatilho, antes de gravar.

É o mesmo ritmo que a prévia e as cenas usam (sílabas, números por extenso, pausas da pontuação); depois da
gravação, as durações da fala gravada (e editada).
"""
import re

from .comum import ok, pasta_do_video, relativo
from .roteiro import fracao_na_fala, ler_roteiro, ler_tempos, palavras

GATILHO = re.compile(r'\bem "([^"]+)"')  # em "palavra": a palavra da fala em que a coisa acontece
ALVO = (60, 90)
SOBRA = 0.7  # o último evento fica pelo menos isto na tela antes do corte


def main(args):
    pasta = pasta_do_video(args.roteiro)
    linhas = ler_roteiro(pasta)
    tempos, estimado = ler_tempos(pasta, linhas)
    total = sum(t.duracao for t in tempos)
    tabela, avisos = [], []
    for linha, t in zip(linhas, tempos):
        vistos, marcas, tarde = {}, [], None
        for g in GATILHO.findall(linha.descricao):
            if not re.search(r"\w", g):
                continue
            vez = vistos[g.lower()] = vistos.get(g.lower(), 0) + 1
            fracao = fracao_na_fala(linha.fala, g, vez)
            if fracao is None:
                marcas.append(f'"{g}" ?')
                avisos.append(f'linha {linha.numero}: o gatilho em "{g}" (vez {vez}) não está na fala. Use a palavra '
                              f'exata da fala, ou escreva o valor mostrado sem "em" antes das aspas.')
                continue
            s = fracao * t.duracao
            marcas.append(f"{g} {s:.1f}")
            if t.duracao - s < SOBRA:
                tarde = (g, s)
        if tarde:
            avisos.append(f'linha {linha.numero}: em "{tarde[0]}" ({tarde[1]:.1f} s) faltam só '
                          f"{t.duracao - tarde[1]:.1f} s para o corte (mínimo {SOBRA} s): o que ele mostra mal aparece. "
                          f"Adiante o evento, alongue a fala ou divida a linha.")
        tabela.append(f"{linha.numero:>3} {linha.marca:<5} {palavras(linha.fala):>3} pal {t.duracao:>5.1f} s"
                      + (f"   {' · '.join(marcas)}" if marcas else ""))
    for i in range(len(linhas) - 2):
        if linhas[i].marca == linhas[i + 1].marca == linhas[i + 2].marca:
            avisos.append(f"linhas {i + 1} a {i + 3}: [{linhas[i].marca}] três vezes seguidas.")
    if linhas[-1].marca != "CARA":
        avisos.append(f"linha {len(linhas)}: o fechamento é [CARA].")
    if not ALVO[0] <= total <= ALVO[1]:
        avisos.append(f"{total:.1f} s, fora de {ALVO[0]} a {ALVO[1]} s: "
                      + ("corte falas." if total > ALVO[1] else "falta conteúdo."))
    origem = "estimados pelo ritmo da fala" if estimado else "da fala gravada"
    ok(f"{relativo(pasta / 'roteiro.md')}: {len(linhas)} linhas, {sum(palavras(n.fala) for n in linhas)} palavras, "
       f"{total:.1f} s ({origem}; alvo {ALVO[0]} a {ALVO[1]} s).\n"
       f"linha, marca, palavras, segundos e o segundo de cada gatilho (em \"...\" da descrição):\n"
       + "\n".join(tabela)
       + ("\nATENÇÃO\n" + "\n".join(f"- {a}" for a in avisos) if avisos else "\nNenhum aviso."))
