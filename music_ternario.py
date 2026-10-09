from fractions import Fraction

from music21 import stream, note, chord, tempo, meter, instrument


DURACAO_SLOT = Fraction(1, 3)


def extrair_eventos(individuo, pausa=-1, hold=-2, notas_bar=12):
    """Agrupa cada ataque com seus HOLDs; lacunas entre eventos são pausas.

    Um evento pode atravessar compassos. Seu compasso e sua posição sempre
    indicam o ataque. HOLD sem nota ativa é inválido e deve ser reparado antes.
    """
    eventos = []
    nota_ativa = None

    for inicio, gene in enumerate(individuo):
        if gene == pausa:
            nota_ativa = None
        elif gene == hold:
            if nota_ativa is None:
                raise ValueError(f"HOLD sem nota ativa na posição {inicio}.")
            nota_ativa["duracao"] += 1
        else:
            if not isinstance(gene, int) or not 0 <= gene <= 127:
                raise ValueError(f"Nota MIDI inválida na posição {inicio}: {gene}")
            nota_ativa = {
                "pitch": gene,
                "inicio": inicio,
                "duracao": 1,
                "compasso": inicio // notas_bar,
                "posicao_compasso": inicio % notas_bar,
            }
            eventos.append(nota_ativa)

    return eventos


def criar_partitura(
    individuo, pausa, hold, progressao, acordes,
    numero_voltas=2, finalizar_em_c=True, notas_bar=12, acompanhamento=False
):
    """Repete a melodia; a faixa de acordes é opcional e desativada por padrão.

    Com acompanhamento, finalizar_em_c altera apenas o acorde do último
    compasso da última volta. Sem acompanhamento, essa opção não afeta o MIDI.
    Os ataques da melodia são repetidos sem transposição ou reescrita.
    """
    if notas_bar * DURACAO_SLOT != 4:
        raise ValueError("A grade 4/4 ternária precisa de 12 posições por compasso.")
    if not progressao or len(individuo) != len(progressao) * notas_bar:
        raise ValueError("O cromossomo deve preencher exatamente uma volta da progressão.")
    if not isinstance(numero_voltas, int) or numero_voltas < 1:
        raise ValueError("numero_voltas precisa ser um inteiro positivo.")
    eventos = extrair_eventos(individuo, pausa, hold, notas_bar)
    musica = stream.Score()

    melodia = stream.Part()
    melodia.partName = "Melodia"

    melodia.insert(
        0,
        instrument.Piano()
    )

    melodia.append(
        tempo.MetronomeMark(number=100)
    )

    melodia.append(
        meter.TimeSignature("4/4")
    )

    for _ in range(numero_voltas):
        cursor = 0
        for dados in eventos:
            if dados["inicio"] > cursor:
                descanso = note.Rest()
                descanso.quarterLength = (dados["inicio"] - cursor) * DURACAO_SLOT
                melodia.append(descanso)

            evento = note.Note(dados["pitch"])
            evento.quarterLength = dados["duracao"] * DURACAO_SLOT
            evento.volume.velocity = 85
            melodia.append(evento)
            cursor = dados["inicio"] + dados["duracao"]

        if cursor < len(individuo):
            descanso = note.Rest()
            descanso.quarterLength = (len(individuo) - cursor) * DURACAO_SLOT
            melodia.append(descanso)

    musica.insert(
        0,
        melodia
    )

    if acompanhamento:
        harmonia = stream.Part()
        harmonia.partName = "Harmonia"
        harmonia.insert(0, instrument.Piano())
        harmonia.append(meter.TimeSignature("4/4"))
        for volta in range(numero_voltas):
            for bar, nome_acorde in enumerate(progressao):
                if finalizar_em_c and volta == numero_voltas - 1 and bar == len(progressao) - 1:
                    nome_acorde = "C7"
                # Acompanhamento mais suave e uma oitava abaixo da melodia.
                evento_acorde = chord.Chord([pitch - 12 for pitch in acordes[nome_acorde]])
                evento_acorde.quarterLength = notas_bar * DURACAO_SLOT
                evento_acorde.volume.velocity = 45
                harmonia.append(evento_acorde)
        musica.insert(0, harmonia)
    return musica


def exportar_midi(
    individuo, pausa, hold, nome_arquivo, progressao, acordes,
    numero_voltas=2, finalizar_em_c=True, notas_bar=12, acompanhamento=False
):
    musica = criar_partitura(
        individuo, pausa, hold, progressao, acordes,
        numero_voltas=numero_voltas,
        finalizar_em_c=finalizar_em_c,
        notas_bar=notas_bar,
        acompanhamento=acompanhamento,
    )

    musica.write(
        "midi",
        fp=nome_arquivo
    )

    print(
        f"MIDI salvo em: {nome_arquivo}"
    )
