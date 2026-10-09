import random
from collections import Counter
import matplotlib.pyplot as plt
from music_ternario import exportar_midi
from music_ternario import extrair_eventos as extrair_eventos_grade


# Configuração do algoritmo e dos componentes do fitness ---------------

GERACOES = 100
POPULATION_SIZE = 100
TOURNAMENT_SIZE = 3
ELITE_SIZE = 5

TAXA_MUTACAO = 0.05
TAXA_CROSSOVER = 0.8
PROB_PAUSA = 0.10
PROB_HOLD = 0.20  # Resto gera nota

PESOS_FITNESS = {
    "Harmonia": 1.0,
    "Movimento": 1.0,
    "Repetição": 1.0,
    "Ritmo": 1.0,
    "Durações": 0.7,
    "Frases": 1.2,
    "Motivos rítmicos": 0.6,
    "Resolução": 1.0,
}

NUM_BARS = 12
NOTAS_BAR = 12
CHROMOSSOME_SIZE = NUM_BARS * NOTAS_BAR

PAUSA = -1
HOLD = -2

ALLOWED_NOTES = list(range(60, 73))

BLUES_SCALE_CLASSES = [
    0, # C4
    3, # Eb4
    5, # F4
    6, # F#4
    7, # G4
    10, # Bb4

]

FINS_DE_FRASE = [3, 7, 11]
BONUS_TEMPOS_FORTES = {0: 2, 6: 1}
POSICOES_OFFBEAT = {2, 5, 8, 11}
PARES_MOTIVOS = [(0, 2), (4, 6)]
DENSIDADE_ALVO = {
    0: (4, 7), 1: (4, 7), 2: (4, 7),
    3: (3, 5),  # final da frase 1
    4: (4, 7), 5: (4, 8), 6: (4, 7),
    7: (3, 5),  # final da frase 2
    8: (5, 8), 9: (5, 8),  # clímax
    10: (3, 6), 11: (4, 8),  # preparação e turnaround
}

PROPORCAO_DURACAO_RELEVANTE = 0.10
PROPORCAO_DURACAO_DOMINANTE = 0.85
PROPORCAO_MAXIMA_LONGAS = 0.40
DURACAO_EXTREMA = 12
PROPORCAO_MAXIMA_EXTREMAS = 0.10

# Harmonia Blues ---------------

ACORDES = {
    "C7": [60, 64, 67, 70],
    "F7": [65, 69, 72, 75],
    "G7": [67, 71, 74, 77]
}

BLUES_PROGRESSION = [
    "C7",
    "F7",
    "C7",
    "C7",
    "F7",
    "F7",
    "C7",
    "C7",
    "G7",
    "F7",
    "C7",
    "G7"
]

# Cria Indivíduos ------------


def create_individuo():
    individuo = []
    nota_ativa = False

    for _ in range(CHROMOSSOME_SIZE):
        r = random.random()
        if r < PROB_PAUSA:
                # 10% de pausa
            individuo.append(PAUSA)
            nota_ativa = False

        elif r < PROB_PAUSA + PROB_HOLD and nota_ativa:
                # 20% de chance de sustentar
            individuo.append(HOLD)

        else:
                # nova nota
            individuo.append(
                random.choice(ALLOWED_NOTES)
            )
            nota_ativa = True

    return individuo

def create_populacao():
    return [
        create_individuo()
        for _ in range(POPULATION_SIZE)
    ]

def extrair_eventos(individuo):
    return extrair_eventos_grade(individuo, PAUSA, HOLD, NOTAS_BAR)


# Fitness ---------

def fitness_harmonico(individuo, eventos):
    score = 0.0
    classes_por_acorde = {
        nome: {nota % 12 for nota in notas}
        for nome, notas in ACORDES.items()
    }

    for evento in eventos:
        nome_acorde = BLUES_PROGRESSION[evento["compasso"]]
        note_class = evento["pitch"] % 12
        if note_class in classes_por_acorde[nome_acorde]:
            score += 2
            score += BONUS_TEMPOS_FORTES.get(evento["posicao_compasso"], 0)
        elif note_class in BLUES_SCALE_CLASSES:
            score += 1
        else:
            score -= 1
    return score

def fitness_ritmico(individuo, eventos):
    score = 0.0
    por_compasso = [[] for _ in range(NUM_BARS)]
    for evento in eventos:
        por_compasso[evento["compasso"]].append(evento)

    for bar in range(NUM_BARS):
        start = bar * NOTAS_BAR
        end = start + NOTAS_BAR
        compasso = individuo[start:end]
        posicoes = [evento["posicao_compasso"] for evento in por_compasso[bar]]
        ataques = len(posicoes)
        holds = compasso.count(HOLD)
        pausas = compasso.count(PAUSA)

        minimo, maximo = DENSIDADE_ALVO[bar]
        distancia = max(minimo - ataques, ataques - maximo, 0)
        if distancia == 0:
            score += 3
        elif distancia == 1:
            score += 1
        else:
            score -= min(4, distancia)

        if 1 <= holds <= 6:
            score += 2
        elif holds >= 9:
            score -= 2

        if 1 <= pausas <= 3:
            score += 1
        elif pausas >= 6:
            score -= 2

        if any(pos < NOTAS_BAR // 2 for pos in posicoes) and any(
            pos >= NOTAS_BAR // 2 for pos in posicoes
        ):
            score += 0.5

        offbeats = sum(pos in POSICOES_OFFBEAT for pos in posicoes)
        if 1 <= offbeats <= 3:
            score += 0.5

    return score


def fitness_resolucao(individuo, eventos):
    
    ultima_nota = ultima_nota_atacada_compasso(eventos, NUM_BARS - 1)
    classes_finais = {nota % 12 for nota in ACORDES[BLUES_PROGRESSION[-1]]}
    if ultima_nota is None or ultima_nota % 12 not in classes_finais:
        return 0.0

    score = 2.0
    primeiro = next((evento for evento in eventos if evento["compasso"] == 0), None)
    classes_iniciais = {nota % 12 for nota in ACORDES[BLUES_PROGRESSION[0]]}
    if primeiro is not None:
        intervalo = abs(primeiro["pitch"] - ultima_nota)
        if primeiro["pitch"] % 12 in classes_iniciais and 1 <= intervalo <= 2:
            score += 1
    return score

def fitness_movimento(eventos):
    score = 0.0

    nota_anterior = None

    for evento in eventos:
        nota = evento["pitch"]

        if nota_anterior is not None:

            intervalo = abs(nota - nota_anterior)

            if intervalo == 0:
                score += 0

            elif intervalo <= 2:
                score += 2

            elif intervalo <= 5:
                score += 1

            elif intervalo <= 7:
                score += 0

            else:
                score -= 2

        nota_anterior = nota

    return score


def fitness_repeticao(eventos):
    score = 0.0

    contador_repeticao = 1

    for anterior, atual in zip(eventos, eventos[1:]):
        if atual["pitch"] == anterior["pitch"]:

            contador_repeticao += 1

            if contador_repeticao >= 4:
                score -= 2

        else:
            contador_repeticao = 1

    return score


def fitness_duracoes(eventos):
   
    if not eventos:
        return 0.0

    contagem = Counter(evento["duracao"] for evento in eventos)
    total = len(eventos)
    relevantes = sum(
        quantidade / total >= PROPORCAO_DURACAO_RELEVANTE
        for quantidade in contagem.values()
    )
    score = 0.0
    if max(contagem.values()) / total >= PROPORCAO_DURACAO_DOMINANTE:
        score -= 3
    elif 2 <= relevantes <= 3:
        score += 3
    elif relevantes == 4:
        score += 1

    curtas = contagem[1] / total
    longas = sum(qtd for duracao, qtd in contagem.items() if duracao >= 4) / total
    extremas = sum(
        qtd for duracao, qtd in contagem.items() if duracao >= DURACAO_EXTREMA
    ) / total
    if curtas >= PROPORCAO_DURACAO_DOMINANTE:
        score -= 2
    if longas > PROPORCAO_MAXIMA_LONGAS:
        score -= 2
    if extremas > PROPORCAO_MAXIMA_EXTREMAS:
        score -= 2
    return score


def padrao_ritmico_compasso(individuo, bar):
    start = bar * NOTAS_BAR
    compasso = individuo[start:start + NOTAS_BAR]
    if len(compasso) != NOTAS_BAR:
        raise ValueError(f"Compasso {bar} incompleto: esperado {NOTAS_BAR} genes.")
    return tuple(int(gene not in (PAUSA, HOLD)) for gene in compasso)


def fitness_motivos_ritmicos(individuo):
    padroes = [padrao_ritmico_compasso(individuo, bar) for bar in range(NUM_BARS)]
    score = 0.0
    for primeiro, segundo in PARES_MOTIVOS:
        a, b = padroes[primeiro], padroes[segundo]
        if not any(a) or not any(b):
            continue  # Silêncio repetido não é um motivo de ataques.
        distancia = sum(x != y for x, y in zip(a, b))
        if distancia == 0:
            score += 0.5
        elif distancia <= 3:
            score += 2
        elif distancia <= 6:
            score += 0.5

    repetidos = 1
    for anterior, atual in zip(padroes, padroes[1:]):
        repetidos = repetidos + 1 if atual == anterior else 1
        if repetidos >= 3:
            score -= 1
    return score


def fitness_frases(individuo, eventos):

    score = 0.0

    for bar in FINS_DE_FRASE:

        ultima_nota = ultima_nota_atacada_compasso(
            eventos,
            bar
        )

        if ultima_nota is None:
            continue

        nome_acorde = BLUES_PROGRESSION[bar]

        acorde_classes = {
            nota % 12
            for nota in ACORDES[nome_acorde]
        }

        note_class = ultima_nota % 12


        # Inclui o G7 do compasso 12: não exige C no turnaround.
        if note_class in acorde_classes:
            score += 3

    return score


def componentes_fitness(individuo, eventos):
    
    return {
        "Harmonia": fitness_harmonico(individuo, eventos),
        "Movimento": fitness_movimento(eventos),
        "Repetição": fitness_repeticao(eventos),
        "Ritmo": fitness_ritmico(individuo, eventos),
        "Durações": fitness_duracoes(eventos),
        "Frases": fitness_frases(individuo, eventos),
        "Motivos rítmicos": fitness_motivos_ritmicos(individuo),
        "Resolução": fitness_resolucao(individuo, eventos),
    }


def fitness(individuo):
    eventos = extrair_eventos(individuo)
    componentes = componentes_fitness(individuo, eventos)
    return sum(PESOS_FITNESS[nome] * valor for nome, valor in componentes.items())


def diagnosticar_fitness(individuo):
    eventos = extrair_eventos(individuo)
    componentes = componentes_fitness(individuo, eventos)
    ponderados = {
        nome: PESOS_FITNESS[nome] * valor
        for nome, valor in componentes.items()
    }
    duracoes = dict(sorted(Counter(evento["duracao"] for evento in eventos).items()))
    ataques = Counter(evento["compasso"] for evento in eventos)
    ataques_por_compasso = [ataques[bar] for bar in range(NUM_BARS)]
    total = sum(ponderados.values())

    print("\nDiagnóstico do melhor indivíduo (componentes ponderados):")
    for nome, valor in componentes.items():
        print(
            f"{nome}: {ponderados[nome]:.2f} "
            f"(bruto: {valor:.2f}; peso: {PESOS_FITNESS[nome]:.2f})"
        )
    print(f"TOTAL: {total:.2f}")
    print(f"Número total de eventos: {len(eventos)}")
    print(f"Distribuição das durações (slots): {duracoes}")
    print(f"Número de pausas (slots): {individuo.count(PAUSA)}")
    print(f"Número de HOLDs: {individuo.count(HOLD)}")
    print(f"Ataques por compasso: {ataques_por_compasso}")

    return {
        "componentes": ponderados,
        "total": total,
        "numero_eventos": len(eventos),
        "duracoes": duracoes,
        "pausas": individuo.count(PAUSA),
        "holds": individuo.count(HOLD),
        "ataques_por_compasso": ataques_por_compasso,
    }




# SELEÇÃO-----------

def tournament_selection(population):
    competidor = random.sample(population,TOURNAMENT_SIZE)

    vencedor = max(competidor, key=fitness)

    return vencedor


#CROSSOVER-----------
def crossover(parent1, parent2):
    if random.random() > TAXA_CROSSOVER:
        return parent1[:], parent2[:]

    possible_points = [i* NOTAS_BAR
                       for i in range(1, NUM_BARS)]

    cut = random.choice(possible_points)

    filho1 = parent1 [:cut] + parent2[cut:]
    filho2 = parent2[:cut] + parent1[cut:]

    filho1 = reparar_individuo(filho1)
    filho2 = reparar_individuo(filho2)

    return filho1, filho2


# Mutação-----------------
def reparar_individuo(individuo):

    reparado = individuo[:]

    nota_ativa = False

    for i, gene in enumerate(reparado):

        if gene == PAUSA:

            nota_ativa = False

        elif gene == HOLD:

            if not nota_ativa:

                reparado[i] = random.choice(
                    ALLOWED_NOTES
                )

                nota_ativa = True

        else:

            nota_ativa = True

    return reparado

def mutate(individuo, taxa_mutacao=TAXA_MUTACAO):

    mutated = individuo[:]

    for i in range(len(mutated)):

        if random.random() < taxa_mutacao:
            r = random.random()

            if r < PROB_PAUSA:
                mutated[i] = PAUSA

            elif r < PROB_PAUSA + PROB_HOLD:
                mutated[i] = HOLD

            else:

                mutated[i] = random.choice(
                    ALLOWED_NOTES
                )

    return reparar_individuo(mutated)



# Algoritmo Genético -----------------

def run_genetic_algorithm(taxa_mutacao=TAXA_MUTACAO):

    population = create_populacao()

    best_history = []
    avg_history = []

    for geracao in range(GERACOES):

        population.sort(key=fitness,reverse=True)

        fitness_values = [
            fitness(individuo)
            for individuo in population
        ]

        best_fitness = fitness_values[0]

        avg_fitness = (sum(fitness_values) / len(fitness_values))

        best_history.append(best_fitness)
        avg_history.append(avg_fitness)
        
        print(
            f"Geração {geracao:03d} | "
            f"Melhor: {best_fitness:.2f} | "
            f"Média: {avg_fitness:.2f}"
            )

        new_population = [
            individuo[:]
            for individuo in population[:ELITE_SIZE]
        ]

        while len(new_population) < POPULATION_SIZE:
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)

            filho1, filho2 = crossover(parent1, parent2)

            filho1 = mutate(filho1, taxa_mutacao)
            filho2 = mutate(filho2, taxa_mutacao)

            new_population.append(filho1)

            if(len(new_population) < POPULATION_SIZE):
                new_population.append(filho2)

        population = new_population
    population.sort(key=fitness, reverse=True)

    best_individuo = population[0]

    return (best_individuo, best_history, avg_history)


# Plotar gráfico --------------

def plot_fitness(
    best_history,
    average_history,
    nome_arquivo="fitness_evolution_ternario.png",
    titulo="Evolução do fitness ao longo das gerações",
    mostrar=False
):

    generations = range(len(best_history))

    figura = plt.figure()

    plt.plot(
        generations,
        best_history,
        label="Melhor fitness"
    )

    plt.plot(
        generations,
        average_history,
        label="Fitness médio"
    )

    plt.xlabel("Geração")
    plt.ylabel("Fitness")

    plt.title(
        titulo
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        nome_arquivo,
        dpi=300
    )

    if mostrar:
        plt.show()
    plt.close(figura)


# Auxiliares ---------------

def ultima_nota_atacada_compasso(eventos, bar):
    for evento in reversed(eventos):
        if evento["compasso"] == bar:
            return evento["pitch"]
    return None


# Executa ----------------

if __name__ == "__main__":
    random.seed(42)

    best, best_history, avg_history = (run_genetic_algorithm())

    print("\n Melhor indivíduo:")
    print(best)

    print("\nFitness final:")
    print(fitness(best))
    diagnosticar_fitness(best)

    exportar_midi(
        individuo=best,
        pausa=PAUSA,
        hold=HOLD,
        nome_arquivo="melodia_blues_ternario.mid",
        progressao=BLUES_PROGRESSION,
        acordes=ACORDES,
        numero_voltas=2,
        finalizar_em_c=True,
        notas_bar=NOTAS_BAR,
        acompanhamento=True
    )

    plot_fitness(
        best_history,
        avg_history,
        mostrar=True
    )
