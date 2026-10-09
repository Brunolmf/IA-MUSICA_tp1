"""Converte MIDI para WAV usando o FluidSynth e um banco de instrumentos."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess


def converter_midi_para_wav(arquivo_midi, arquivo_wav=None, soundfont=None):
    """Gera um WAV a 44100 Hz e retorna o caminho do arquivo criado."""
    midi = Path(arquivo_midi).resolve()
    wav = Path(arquivo_wav).resolve() if arquivo_wav else midi.with_suffix(".wav")

    if not midi.is_file():
        raise FileNotFoundError(f"MIDI não encontrado: {midi}")
    with midi.open("rb") as entrada:
        if entrada.read(4) != b"MThd":
            raise ValueError(f"O arquivo não contém um MIDI padrão: {midi}")
    if wav == midi:
        raise ValueError("O arquivo de saída precisa ser diferente do MIDI.")
    if wav.suffix.lower() != ".wav":
        raise ValueError("O arquivo de saída precisa ter a extensão .wav.")
    if not wav.parent.is_dir():
        raise FileNotFoundError(f"Pasta de saída não encontrada: {wav.parent}")

    # Ferramentas preparadas na pasta do projeto, sem instalação no sistema.
    audio_local = Path(__file__).resolve().parent / ".musica" / "audio"
    executavel_local = audio_local / "usr/bin/fluidsynth"
    ambiente = os.environ.copy()

    if executavel_local.is_file():
        executavel = str(executavel_local)
        bibliotecas = str(audio_local / "usr/lib/x86_64-linux-gnu")
        anteriores = ambiente.get("LD_LIBRARY_PATH")
        ambiente["LD_LIBRARY_PATH"] = (
            bibliotecas + os.pathsep + anteriores if anteriores else bibliotecas
        )
    else:
        executavel = shutil.which("fluidsynth")
        if not executavel:
            raise FileNotFoundError("FluidSynth não encontrado no projeto ou no sistema.")

    if soundfont is not None:
        banco = Path(soundfont).resolve()
    else:
        candidatos = [
            audio_local / "usr/share/sounds/sf2/TimGM6mb.sf2",
            Path("/usr/share/sounds/sf2/default-GM.sf2"),
            Path("/usr/share/sounds/sf2/TimGM6mb.sf2"),
        ]
        banco = next((caminho for caminho in candidatos if caminho.is_file()), None)
    if banco is None or not banco.is_file():
        raise FileNotFoundError("Banco de instrumentos não encontrado. Use --soundfont caminho.sf2.")

    subprocess.run(
        [
            executavel, "-ni",
            "-F", str(wav),
            "-T", "wav",
            "-r", "44100",
            str(banco), str(midi),
        ],
        env=ambiente,
        check=True,
    )
    return wav


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("midi", help="Caminho do arquivo .mid ou .midi")
    parser.add_argument(
        "-o", "--saida",
        help="Caminho do WAV (padrão: mesmo local e nome do MIDI, com extensão .wav). "
             "Um WAV existente nesse caminho será substituído.",
    )
    parser.add_argument("--soundfont", help="Banco de instrumentos .sf2 opcional")
    args = parser.parse_args()

    try:
        wav = converter_midi_para_wav(args.midi, args.saida, args.soundfont)
    except (OSError, ValueError, subprocess.CalledProcessError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
    print(f"WAV salvo em: {wav}")


if __name__ == "__main__":
    main()


# .musica/bin/python midi_para_wav.py melodia_blues.mid