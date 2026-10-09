# Geração de blues com algoritmo genético

Projeto de geração musical simbólica para o TP1 de IA Generativa para Música.
O algoritmo genético cria uma melodia de blues de 12 compassos em uma grade
ternária. A música é exportada para MIDI e pode ser convertida para WAV.

## Estrutura

```text
README.md
requirements.txt
main_ternario.py
music_ternario.py
midi_para_wav.py
experimentos.py
test_experimentos.py
resultados_experimentos/
    mutacao_001/   # três MIDIs, três WAVs, gráficos e resultados em JSON
    seeds_001/     # três MIDIs, gráficos e resultados em JSON
```

- `main_ternario.py`: representação, fitness e operadores do algoritmo genético.
- `music_ternario.py`: extração de eventos musicais e exportação MIDI.
- `midi_para_wav.py`: conversão para áudio com FluidSynth.
- `experimentos.py`: execução dos experimentos.
- `test_experimentos.py`: testes da execução dos experimentos.

## Instalação

Ambiente usado: Python 3.12.3 em Linux. As versões das dependências Python
estão em [requirements.txt](requirements.txt).

Na pasta do projeto:

```bash
python3 -m venv .musica
.musica/bin/python -m pip install -r requirements.txt
```

No Ubuntu, se o módulo `venv` não estiver disponível:

```bash
sudo apt install python3-venv
```

Para converter MIDI em WAV, também são necessários o FluidSynth e um banco
de instrumentos SoundFont. No Ubuntu:

```bash
sudo apt install fluidsynth timgm6mb-soundfont
```

O conversor procura primeiro as ferramentas locais em `.musica/audio` e,
se elas não existirem, usa a instalação do sistema. A pasta `.musica` é
local e não faz parte do repositório. Para apenas ouvir os WAVs já incluídos,
basta um reprodutor de áudio.

## Gerar e ouvir uma música

```bash
.musica/bin/python main_ternario.py
```

O programa salva `melodia_blues_ternario.mid` e
`fitness_evolution_ternario.png` na pasta do projeto. O gráfico também é
exibido em uma janela; feche-a para terminar a execução.

Para converter o MIDI e ouvir no Linux com `pw-play` disponível:

```bash
.musica/bin/python midi_para_wav.py melodia_blues_ternario.mid
pw-play melodia_blues_ternario.wav
```

Também é possível abrir o WAV em outro reprodutor. A conversão gera áudio
a 44.100 Hz. Para escolher outro arquivo de saída ou SoundFont:

```bash
.musica/bin/python midi_para_wav.py melodia_blues_ternario.mid \
    --saida minha_musica.wav --soundfont /caminho/banco.sf2
```

Substitua o caminho do SoundFont por um arquivo existente. A execução normal
substitui seus arquivos MIDI e PNG; a conversão substitui o WAV de destino.
Depois de gerar um novo MIDI, converta-o novamente para atualizar o áudio.

## Exportação MIDI

A configuração atual usa piano, andamento de 100 BPM e duas voltas da mesma
melodia, totalizando 24 compassos. O acompanhamento está ativado nas chamadas
de `main_ternario.py` e `experimentos.py`: os acordes são tocados uma oitava
abaixo e com menor intensidade.

Para ouvir somente a melodia, use `acompanhamento=False`. Na execução normal,
as opções ficam na chamada de `exportar_midi()`; nos experimentos, em
`OPCOES_MIDI`. Mantenha as duas configurações iguais para comparar os áudios.

`numero_voltas` controla as repetições. Com acompanhamento,
`finalizar_em_c=True` troca somente o acorde do último compasso da última
volta por C7, sem alterar a melodia nem a progressão usada pelo GA. Sem
acompanhamento, essa opção não afeta o MIDI.

## Experimentos e reprodução dos resultados

```bash
.musica/bin/python experimentos.py seeds
.musica/bin/python experimentos.py mutacao
```

Os experimentos são opcionais e não são iniciados pela execução normal nem
pela importação dos módulos. Cada comando cria uma pasta numerada nova em
`resultados_experimentos/`, preservando as anteriores. Como as pastas `_001`
já estão incluídas, a próxima execução cria `_002`.

Cada pasta contém três MIDIs, gráficos e um JSON com os resultados e as
configurações da execução. Os gráficos são salvos sem abrir janelas.

### Músicas incluídas

As três músicas em WAV foram sintetizadas dos MIDIs de `mutacao_001`, com
FluidSynth e o SoundFont TimGM6mb.

| Música | MIDI | Áudio WAV |
| --- | --- | --- |
| 1 | [mutacao_001.mid](resultados_experimentos/mutacao_001/mutacao_001.mid) | [mutacao_001.wav](resultados_experimentos/mutacao_001/mutacao_001.wav) |
| 2 | [mutacao_005.mid](resultados_experimentos/mutacao_001/mutacao_005.mid) | [mutacao_005.wav](resultados_experimentos/mutacao_001/mutacao_005.wav) |
| 3 | [mutacao_015.mid](resultados_experimentos/mutacao_001/mutacao_015.mid) | [mutacao_015.wav](resultados_experimentos/mutacao_001/mutacao_015.wav) |

Para converter os três MIDIs incluídos novamente:

```bash
.musica/bin/python midi_para_wav.py resultados_experimentos/mutacao_001/mutacao_001.mid
.musica/bin/python midi_para_wav.py resultados_experimentos/mutacao_001/mutacao_005.mid
.musica/bin/python midi_para_wav.py resultados_experimentos/mutacao_001/mutacao_015.mid
```

Para ouvir uma música:

```bash
pw-play resultados_experimentos/mutacao_001/mutacao_001.wav
```

Os mesmos comandos servem para novos resultados, ajustando o caminho da pasta.

## Testes

```bash
.musica/bin/python -m unittest test_experimentos -v
```

Os nove testes verificam a parametrização da mutação, o uso das seeds,
a exportação dos resultados, os gráficos e a preservação de execuções anteriores.

## Uso de IA

Foi utilizado ChatGPT/Codex como apoio na discussão da representação musical,
revisão de trechos de código, integração da exportação MIDI e
conversão para WAV, testes e documentação.

Conversa compartilhada:
[registro do apoio de IA](https://chatgpt.com/share/6ac80496-0c98-83e8-a408-86b38bd24d3f).
