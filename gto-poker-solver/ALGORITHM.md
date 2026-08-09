# Algorithm Notes

## Extensive-form representation

A game state supplies:

- the current player (`0`, `1`, chance, or terminal);
- legal actions;
- chance probabilities;
- a child-state transition;
- an information-set key containing only information visible to the acting player;
- terminal zero-sum utility.

`GameTree.from_root` expands the complete finite game once. Every history receives an integer node ID. Decision nodes that share an information-set key are checked to ensure they expose identical legal actions.

## Regret matching

For information set \(I\) and action \(a\), let cumulative regret be \(R^T(I,a)\). The current policy is

\[
\sigma^T(I,a)=
\begin{cases}
\dfrac{\max(R^T(I,a),0)}{\sum_b \max(R^T(I,b),0)}, & \text{if the denominator is positive},\\[6pt]
\dfrac{1}{|A(I)|}, & \text{otherwise}.
\end{cases}
\]

CFR+ applies regret matching to nonnegative regrets and clips cumulative regrets after each update:

\[
R^{T+1}(I,a) \leftarrow \max\left(0, R^T(I,a)+r^{T+1}(I,a)\right).
\]

The implementation freezes the policy for a complete iteration, computes both players' updates against that same profile, and then clips for CFR+.

## Counterfactual regret

At a history \(h\) in Player \(i\)'s information set, the counterfactual reach excludes Player \(i\)'s own action probability:

\[
\pi_{-i}^{\sigma}(h)=\pi_c(h)\pi_{1-i}^{\sigma}(h).
\]

For an action \(a\), the regret increment is

\[
r(I,a)=\sum_{h\in I}\pi_{-i}^{\sigma}(h)
\left(v_i(h\cdot a)-v_i(h)\right).
\]

The NumPy engine computes chance reach, Player 0 reach, and Player 1 reach in one top-down pass. It then computes all node values in a reverse-depth pass and aggregates the action advantages into information-set regret arrays.

## Average strategy

The returned strategy is a realization-weighted average rather than the final iterate. For Player \(i\), the local strategy at information set \(I\) is weighted by Player \(i\)'s own reach probability. CFR+ uses linear iteration weights after the configured averaging delay.

All histories in a perfect-recall information set have the same own reach probability, so one representative tree node is sufficient for the average-strategy update.

## Exact profile value

For a complete behavioral strategy profile, expected value is evaluated recursively:

- terminal node: stored payoff;
- chance node: probability-weighted child values;
- decision node: strategy-weighted child values.

Because the games are zero-sum, Player 1's value is the negative of Player 0's value.

## Exact best response under imperfect information

A naive node-by-node maximization would cheat by conditioning on hidden cards. The evaluator instead enforces one chosen action for every information set.

For a responding player \(i\):

1. Traverse the tree and calculate counterfactual reach from chance and the fixed opponent strategy, excluding Player \(i\)'s actions.
2. When an information set \(I\) is evaluated, aggregate each action's continuation value over **all** histories in \(I\):

\[
Q(I,a)=\sum_{h\in I}\pi_{-i}^{\sigma}(h)V(h\cdot a).
\]

3. Select one action \(a^*(I)=\arg\max_a Q(I,a)\) for the complete information set.
4. Reuse that action at every member history.

Perfect recall guarantees that descendant information sets are compatible with this dynamic program.

## NashConv and exploitability

Let \(u_i(\sigma)\) be Player \(i\)'s profile value and \(BR_i(\sigma_{-i})\) the exact best-response value. Then

\[
\operatorname{NashConv}(\sigma)=
\sum_i \left(BR_i(\sigma_{-i})-u_i(\sigma)\right).
\]

For a two-player zero-sum game, this project reports

\[
\operatorname{exploitability}(\sigma)=
\frac{\operatorname{NashConv}(\sigma)}{2}.
\]

## Why two engines exist

`core.py` contains a small recursive reference trainer that is easy to inspect. `fast.py` performs the same update using padded NumPy arrays and depth-batched passes. The test suite trains both engines from identical initial conditions and checks that their values and exploitability agree to floating-point precision.
