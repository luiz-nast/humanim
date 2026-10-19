# humanim

O Manim com um humano dentro: shorts verticais de 60 s no LinkedIn explicando IA para leigos, com a cara e a voz de quem apresenta. A especificação completa está em https://claude.ai/artifact/PefFxxn3cCWEqqqf2EZt1b.

## Como o repositório funciona

```
humanim/
  CLAUDE.md                 # este arquivo
  .claude/skills/roteiro/   # SKILL.md, voz.md, temas.md
  videos/                   # fica fora do Git (.gitignore)
    arvore-de-decisao/
      roteiro.md
```

- Um repositório só, com uma pasta por vídeo em `videos/<slug>/`. Skill, estilo e ferramenta são compartilhados.
- O Claude é aberto uma vez, na raiz. Para mexer num vídeo, a pasta é apontada ("ajusta a linha 3 de videos/arvore-de-decisao") e o trabalho fica só ali.
- Roteiros são escritos com a skill `roteiro`. O formato e as regras estão em `.claude/skills/roteiro/SKILL.md`.

## Estado atual: etapa 1

- Só a skill de roteiro existe. O comando `humanim` ainda não: as pastas de vídeo são criadas na mão.
- A gravação é feita com um app de teleprompter no celular, só com a cara. As marcas do roteiro já são escritas para as próximas etapas.
- Próximas etapas: teleprompter no Ubuntu gerando `tempos.json`; `montar` e `frames`; `animar`; `previa`; `tratar`; extras como legendas.
