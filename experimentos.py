"""Experimentos opcionais do GA ternário: python experimentos.py seeds|mutacao."""

import argparse
from itertools import count
import json
from pathlib import Path
import random

import matplotlib.pyplot as plt

import main_ternario as ga


# Seed NÃO é um hiperparâmetro do GA. Ela controla a sequência
# pseudoaleatória e permite reproduzir uma execução específica.
SEEDS_EXPERIMENTO = [42, 123, 999]
SEED_HIPERPARAMETRO = 42

# A taxa de mutação É um hiperparâmetro do GA: altera o comportamento da evolução.
TAXA_MUTACAO_BASELINE = 0.05
TAXAS_MUTACAO_EXPERIMENTO = [0.01, 0.05, 0.15]
PASTA_RESULTADOS = "resultados_experimentos"

# Mesmas opções da execução atual em main_ternario.py, para todas as músicas.
# O exportador é reutilizado sem alterar sua lógica musical.
OPCOES_MIDI = {
    "pausa": ga.PAUSA,
    "hold": ga.HOLD,
    "progressao": ga.BLUES_PROGRESSION,
    "acordes": ga.ACORDES,
    "numero_voltas": 2,
    "finalizar_em_c": True,
    "notas_bar": ga.NOTAS_BAR,
    "acompanhamento": True,
}


def _criar_pasta_experimento(tipo, pasta_base):
    """Reserva uma pasta numerada, preservando resultados de execuções anteriores."""
    base = Path(pasta_base)
    base.mkdir(parents=True, exist_ok=True)
    for numero in count(1):
        pasta = base / f"{tipo}_{numero:03d}"
        try:
            pasta.mkdir()
        except FileExistsError:
            continue
        return pasta


def _executar(seed, taxa_mutacao, pasta, nome, titulo):
    random.seed(seed)
    best, best_history, avg_history = ga.run_genetic_algorithm(taxa_mutacao=taxa_mutacao)
    resultado = {
        "seed": seed,
        "taxa_mutacao": taxa_mutacao,
        "best": best,
        "fitness": ga.fitness(best),
        "best_history": best_history,
        "avg_history": avg_history,
    }
    ga.exportar_midi(
        individuo=best,
        nome_arquivo=pasta / f"{nome}.mid",
        **OPCOES_MIDI,
    )
    ga.plot_fitness(
        best_history,
        avg_history,
        nome_arquivo=pasta / f"fitness_{nome}.png",
        titulo=titulo,
        mostrar=False,
    )
    return resultado


def _salvar_resultados(resultados, pasta, nome_arquivo):
    dados = {
        "hiperparametros_fixos": {
            "GERACOES": ga.GERACOES,
            "POPULATION_SIZE": ga.POPULATION_SIZE,
            "TOURNAMENT_SIZE": ga.TOURNAMENT_SIZE,
            "ELITE_SIZE": ga.ELITE_SIZE,
            "TAXA_CROSSOVER": ga.TAXA_CROSSOVER,
        },
        "opcoes_midi": OPCOES_MIDI,
        "resultados": resultados,
    }
    arquivo = pasta / nome_arquivo
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultados salvos em: {pasta.resolve()}")


def experimento_seeds(pasta_base=PASTA_RESULTADOS):
    """Varia apenas a aleatoriedade; retorna resultados indexados pela seed."""
    pasta = _criar_pasta_experimento("seeds", pasta_base)
    resultados = {}
    print("\nMESMA CONFIGURAÇÃO — SEEDS DIFERENTES")
    for seed in SEEDS_EXPERIMENTO:
        print(f"\nSeed {seed}:")
        resultado = _executar(
            seed, TAXA_MUTACAO_BASELINE, pasta, f"seed_{seed}",
            f"Evolução do fitness — seed {seed}; mutação {TAXA_MUTACAO_BASELINE:.2f}",
        )
        resultados[seed] = resultado
        print(f"fitness = {resultado['fitness']:.2f}")
    _salvar_resultados(resultados, pasta, "resultados_seeds.json")
    return resultados


def _plotar_comparacao_mutacao(resultados, nome_arquivo):
    figura, eixo = plt.subplots()
    for taxa, resultado in resultados.items():
        historico = resultado["best_history"]
        eixo.plot(range(len(historico)), historico, label=f"Mutação = {taxa:.2f}")
    eixo.set(
        xlabel="Geração",
        ylabel="Melhor fitness",
        title=f"Comparação das taxas de mutação — seed {SEED_HIPERPARAMETRO}",
    )
    eixo.legend()
    figura.tight_layout()
    figura.savefig(nome_arquivo, dpi=300)
    plt.close(figura)


def experimento_taxa_mutacao(pasta_base=PASTA_RESULTADOS):
    """Varia apenas a taxa; reinicia a mesma seed antes de cada execução."""
    pasta = _criar_pasta_experimento("mutacao", pasta_base)
    resultados = {}
    print("\nEXPERIMENTO — TAXA DE MUTAÇÃO")
    for taxa in TAXAS_MUTACAO_EXPERIMENTO:
        print(f"\nTaxa {taxa:.2f}:")
        sufixo = str(taxa).replace(".", "")
        resultado = _executar(
            SEED_HIPERPARAMETRO, taxa, pasta, f"mutacao_{sufixo}",
            f"Evolução do fitness — mutação {taxa:.2f}; seed {SEED_HIPERPARAMETRO}",
        )
        resultados[taxa] = resultado
        print(f"fitness final = {resultado['fitness']:.2f}")
    _plotar_comparacao_mutacao(resultados, pasta / "comparacao_taxas_mutacao.png")
    _salvar_resultados(resultados, pasta, "resultados_taxa_mutacao.json")
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experimento", choices=("seeds", "mutacao"))
    args = parser.parse_args()
    if args.experimento == "seeds":
        experimento_seeds()
    else:
        experimento_taxa_mutacao()
