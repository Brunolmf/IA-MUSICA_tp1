"""Verificações da camada de experimentos, sem executar os lotes completos."""

import ast
import contextlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import experimentos as exp
import main_ternario as ga


class ParametrizacaoTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())

    def test_baseline_e_taxa_padrao_equivalente(self):
        self.assertEqual(
            (ga.GERACOES, ga.POPULATION_SIZE, ga.TOURNAMENT_SIZE, ga.ELITE_SIZE,
             ga.TAXA_MUTACAO, ga.TAXA_CROSSOVER),
            (100, 100, 3, 5, 0.05, 0.8),
        )
        with patch.object(ga, "GERACOES", 3), patch.object(ga, "POPULATION_SIZE", 12):
            random.seed(42)
            with contextlib.redirect_stdout(io.StringIO()):
                padrao = ga.run_genetic_algorithm()
                random.seed(42)
                explicito = ga.run_genetic_algorithm(taxa_mutacao=0.05)
        self.assertEqual(padrao, explicito)

    def test_taxa_recebida_controla_mutacao(self):
        genes = [60] * 144
        with patch.object(ga.random, "random", return_value=0.1), patch.object(
            ga.random, "choice", return_value=67
        ):
            self.assertEqual(ga.mutate(genes, 0.01), genes)
            alterado = ga.mutate(genes, 0.15)
        self.assertNotEqual(alterado, genes)
        ga.extrair_eventos(alterado)  # O reparo de HOLDs continua funcionando.
        self.assertEqual(genes, [60] * 144)

    def test_ga_repassa_taxa_e_nao_define_seed(self):
        random.seed(42)
        with patch.object(ga, "GERACOES", 2), patch.object(ga, "POPULATION_SIZE", 12), \
                patch.object(ga, "mutate", wraps=ga.mutate) as mutacao, \
                patch.object(ga.random, "seed", side_effect=AssertionError("Seed deve ser externa")), \
                contextlib.redirect_stdout(io.StringIO()):
            ga.run_genetic_algorithm(taxa_mutacao=0.15)
        self.assertTrue(mutacao.call_args_list)
        self.assertTrue(all(chamada.args[1] == 0.15 for chamada in mutacao.call_args_list))

    def test_grafico_aceita_nome_e_controla_exibicao(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(ga.plt, "show") as mostrar:
            arquivo = Path(temporary) / "fitness.png"
            abertas = ga.plt.get_fignums()
            ga.plot_fitness([1, 2], [0, 1], nome_arquivo=arquivo, titulo="Teste")
            mostrar.assert_not_called()
            self.assertTrue(arquivo.read_bytes().startswith(b"\x89PNG"))
            self.assertEqual(ga.plt.get_fignums(), abertas)
            ga.plot_fitness([1, 2], [0, 1], nome_arquivo=arquivo, mostrar=True)
            mostrar.assert_called_once()
            self.assertEqual(ga.plt.get_fignums(), abertas)


class ExperimentosTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())
        self.chamadas = []

    def ga_curto(self, taxa_mutacao):
        # Registra o estado ANTES de criar o indivíduo, para conferir cada seed.
        self.chamadas.append((taxa_mutacao, random.getstate()))
        individuo = ga.create_individuo()
        return individuo, [taxa_mutacao, taxa_mutacao + 1], [0, taxa_mutacao]

    def test_seeds_variam_apenas_aleatoriedade(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(ga, "run_genetic_algorithm", side_effect=self.ga_curto), \
                patch.object(ga, "exportar_midi", wraps=ga.exportar_midi) as exportar, \
                patch.object(ga.plt, "show") as mostrar, contextlib.redirect_stdout(io.StringIO()) as saida:
            resultados = exp.experimento_seeds(temporary)
            pasta = Path(temporary) / "seeds_001"
            self.assertEqual(list(resultados), [42, 123, 999])
            for seed, (taxa, estado) in zip(exp.SEEDS_EXPERIMENTO, self.chamadas):
                self.assertEqual(taxa, 0.05)
                self.assertEqual(estado, random.Random(seed).getstate())
                self.assertEqual(resultados[seed]["seed"], seed)
                self.assertEqual(resultados[seed]["fitness"], ga.fitness(resultados[seed]["best"]))
                self.assertTrue((pasta / f"seed_{seed}.mid").read_bytes().startswith(b"MThd"))
                self.assertTrue((pasta / f"fitness_seed_{seed}.png").is_file())
            dados = json.loads((pasta / "resultados_seeds.json").read_text())
            self.assertEqual(dados["resultados"]["42"]["best"], resultados[42]["best"])
            self.assertEqual(dados["hiperparametros_fixos"]["POPULATION_SIZE"], 100)
            self.assertIn("MESMA CONFIGURAÇÃO — SEEDS DIFERENTES", saida.getvalue())
            for chamada in exportar.call_args_list:
                opcoes = {k: v for k, v in chamada.kwargs.items() if k not in ("individuo", "nome_arquivo")}
                self.assertEqual(opcoes, exp.OPCOES_MIDI)
            mostrar.assert_not_called()

    def test_mutacao_reinicia_mesma_seed_e_salva_comparacao(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(ga, "run_genetic_algorithm", side_effect=self.ga_curto), \
                patch.object(ga.plt, "show") as mostrar, contextlib.redirect_stdout(io.StringIO()) as saida:
            resultados = exp.experimento_taxa_mutacao(temporary)
            pasta = Path(temporary) / "mutacao_001"
            self.assertEqual(list(resultados), [0.01, 0.05, 0.15])
            self.assertEqual([taxa for taxa, _ in self.chamadas], [0.01, 0.05, 0.15])
            self.assertTrue(all(estado == random.Random(42).getstate() for _, estado in self.chamadas))
            for taxa, sufixo in ((0.01, "001"), (0.05, "005"), (0.15, "015")):
                self.assertEqual(resultados[taxa]["seed"], 42)
                self.assertEqual(resultados[taxa]["taxa_mutacao"], taxa)
                self.assertTrue((pasta / f"mutacao_{sufixo}.mid").is_file())
                self.assertTrue((pasta / f"fitness_mutacao_{sufixo}.png").is_file())
            self.assertTrue((pasta / "comparacao_taxas_mutacao.png").read_bytes().startswith(b"\x89PNG"))
            dados = json.loads((pasta / "resultados_taxa_mutacao.json").read_text())
            self.assertEqual(dados["resultados"]["0.15"]["best_history"], resultados[0.15]["best_history"])
            self.assertIn("EXPERIMENTO — TAXA DE MUTAÇÃO", saida.getvalue())
            mostrar.assert_not_called()

    def test_nova_pasta_preserva_resultado_anterior(self):
        with tempfile.TemporaryDirectory() as temporary:
            anterior = exp._criar_pasta_experimento("mutacao", temporary)
            arquivo = anterior / "fitness_mutacao_001.png"
            arquivo.write_bytes(b"resultado anterior")
            proxima = exp._criar_pasta_experimento("mutacao", temporary)
            self.assertEqual(proxima.name, "mutacao_002")
            self.assertEqual(arquivo.read_bytes(), b"resultado anterior")

    def test_comparacao_mostra_tres_curvas_de_melhor_fitness(self):
        resultados = {taxa: {"best_history": [taxa, taxa + 1]} for taxa in (0.01, 0.05, 0.15)}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(exp.plt, "close") as fechar:
                exp._plotar_comparacao_mutacao(resultados, Path(temporary) / "comparacao.png")
            figura = fechar.call_args.args[0]
            try:
                curvas = figura.axes[0].lines
                self.assertEqual(len(curvas), 3)
                for curva, (taxa, resultado) in zip(curvas, resultados.items()):
                    self.assertEqual(list(curva.get_ydata()), resultado["best_history"])
                    self.assertEqual(curva.get_label(), f"Mutação = {taxa:.2f}")
            finally:
                exp.plt.close(figura)

    def test_opcoes_midi_iguais_a_execucao_normal(self):
        arvore = ast.parse(Path(ga.__file__).read_text())
        chamadas = [
            no for no in ast.walk(arvore)
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "exportar_midi"
        ]
        opcoes = {kw.arg: kw.value for kw in chamadas[0].keywords}
        for nome in ("numero_voltas", "finalizar_em_c", "acompanhamento"):
            self.assertEqual(exp.OPCOES_MIDI[nome], ast.literal_eval(opcoes[nome]))
        self.assertEqual(exp.OPCOES_MIDI["progressao"], ga.BLUES_PROGRESSION)
        self.assertEqual(exp.OPCOES_MIDI["acordes"], ga.ACORDES)
        self.assertEqual(exp.OPCOES_MIDI["notas_bar"], ga.NOTAS_BAR)


if __name__ == "__main__":
    unittest.main()
