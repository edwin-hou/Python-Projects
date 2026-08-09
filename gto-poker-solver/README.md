# GTO Poker Solver

A readable, tested poker solver that learns approximate Nash-equilibrium strategies with **Counterfactual Regret Minimization (CFR)** and **CFR+**.

The project solves complete finite game trees, then measures the resulting strategy against an **exact best response**. That means the reported exploitability is calculated, not guessed.

> **Scope:** this is a serious educational/research solver for finite heads-up games. It is not a replacement for PioSOLVER or GTO Wizard and does not attempt to solve the full no-limit Texas Hold'em game tree. The included games are small enough to solve and verify exactly, while the architecture is designed to be extended with abstractions and subgame solving.

## Included games

| Game | Model | Tree size |
|---|---|---:|
| Kuhn Poker | Three private cards, one betting round | 58 nodes / 12 information sets |
| Leduc Hold'em | Six-card deck, private card, public card, two fixed-limit betting rounds | 18,277 nodes / 528 information sets |
| One-card river abstraction | Configurable ranks, pot, and bet size | 1,418 nodes / 52 information sets at 13 ranks |

## Headline benchmark results

| Game | Iterations | Player 0 value | Exact exploitability |
|---|---:|---:|---:|
| Kuhn Poker | 100,000 | -0.0555548 chips | 0.0003194 chips/hand |
| Leduc Hold'em | 5,000 | -0.0776761 chips | 0.0018318 chips/hand |
| 13-rank river, pot 100, bet 75 | 20,000 | -3.9617803 chips | 0.0073251 chips/hand |

The Kuhn value is within `0.00000075` chips of the exact game value, `-1/18`.

![Exact exploitability over training](results/convergence.svg)

See [RESULTS.md](RESULTS.md) for learned frequencies and interpretation. The compact benchmark files in [`results/`](results/) include full Kuhn and one-card strategies, selected Leduc frequencies, and convergence data; the reproduction script can regenerate the complete Leduc strategy.

## A useful sanity check

For a river bet of 75 into a pot of 100, game theory predicts that a polarized betting range should contain

\[
\frac{B}{P+2B}=\frac{75}{100+150}=30\%
\]

bluffs. In the solved 13-rank game, ranks 1-4 contribute **30.01% of Player 0's total betting mass**. The solver discovers the standard poker result from self-play rather than having it hard-coded.

It also recovers the corresponding Kuhn structure: Player 0's J bluff frequency is approximately one third of the K value-bet frequency, making roughly 25% of the opening betting range bluffs for a one-chip bet into a two-chip pot.

## Installation

```bash
cd gto-poker-solver
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

Python 3.11 or newer is required.

## Solve a game

```bash
# Canonical Kuhn Poker
python -m gto_poker_solver solve kuhn \
  --iterations 100000 \
  --variant cfr+ \
  --averaging-delay 1000 \
  --output results/my_kuhn_run.json

# Fixed-limit Leduc Hold'em
python -m gto_poker_solver solve leduc \
  --iterations 5000 \
  --max-raises 2 \
  --averaging-delay 500 \
  --output results/my_leduc_run.json

# Configurable one-card river game
python -m gto_poker_solver solve one-card \
  --ranks 13 \
  --pot 100 \
  --bet 75 \
  --iterations 20000 \
  --output results/my_river_run.json
```

After installation, the equivalent console command is available:

```bash
gto-solver solve kuhn --iterations 100000
```

Each JSON result contains:

- game parameters and tree dimensions;
- profile expected value;
- each player's exact best-response value;
- NashConv and exploitability;
- the complete average strategy at every information set.

## Reproduce the checked-in benchmarks

```bash
PYTHONPATH=src python scripts/generate_results.py --game all
```

Individual runs are available with `--game kuhn`, `--game leduc`, or `--game one-card`.

## How it works

The default engine performs full-tree CFR+ updates with NumPy:

1. Regret matching converts cumulative counterfactual regrets into the current mixed strategy.
2. A top-down pass computes chance and player reach probabilities.
3. A bottom-up pass computes expected values for every game-tree node.
4. Counterfactual action advantages are aggregated by information set.
5. Linear averaging produces the strategy returned by the solver.

The repository also contains a compact, standard-library-only reference implementation. The tests verify that the vectorized and reference engines produce the same updates to floating-point precision.

Evaluation is separate from training. For each player, the evaluator groups all histories in an information set and chooses one information-consistent action that maximizes counterfactual value. This produces an exact best response for the finite tree, from which NashConv and exploitability are calculated.

See [ALGORITHM.md](ALGORITHM.md) for the formulas and implementation details.

## Project layout

```text
src/gto_poker_solver/
  core.py       finite game tree, reference CFR, exact evaluation
  fast.py       NumPy-vectorized CFR/CFR+
  games.py      Kuhn, Leduc, and one-card poker rules
  cli.py        command-line interface
  reporting.py  JSON result serialization
scripts/
  generate_results.py
results/
  full strategies, convergence data, and chart
tests/
  convergence, equivalence, and game-integrity tests
```

## Limitations and next extensions

The largest missing component is a Texas Hold'em abstraction layer. A practical no-limit solver would also need hand bucketing, a restricted bet-size tree, public-state decomposition, and usually continual subgame re-solving. The current code deliberately solves its included trees without abstraction so that correctness and exploitability remain transparent.

Natural extensions include:

- actual Hold'em hand/range input and river equity matrices;
- multiple no-limit bet sizes and stack-to-pot ratios;
- external-sampling MCCFR for larger trees;
- public-chance decomposition and subgame re-solving;
- strategy visualization by range bucket.

## References

- Martin Zinkevich, Michael Johanson, Michael Bowling, and Carmelo Piccione, *Regret Minimization in Games with Incomplete Information*, NeurIPS 2007: https://papers.nips.cc/paper_files/paper/2007/hash/08d98638c6fcd194a4b1e6992063e944-Abstract.html
- Oskari Tammelin, *Solving Large Imperfect Information Games Using CFR+*, 2014: https://arxiv.org/abs/1407.5042
- Matej Moravčík et al., *DeepStack: Expert-Level Artificial Intelligence in Heads-Up No-Limit Poker*, 2017: https://arxiv.org/abs/1701.01724

## License

MIT
