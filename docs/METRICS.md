# Metrics

Reproducible measurements for the claims behind Spendzone's resume bullets. Each section
below states the exact claim, the command that produces it, the raw output, and what the
number does and does not support. Supporting scripts live in `scripts/metrics/`.

A top-level "what these numbers do and do not show" summary, and the final revised
resume bullets, will be added once every stage below is measured (Stage 5).

## 2a. Projected GMV lift vs. historical allocation

**Claim tested:** the bi-level budget optimizer's recommended split produces higher
projected revenue than the historical allocation, under the optimizer's own objective.

**Command:**
```
ds-pipeline/.venv/Scripts/python.exe scripts/metrics/projected_lift.py
```

**Raw output (table):**
```
Month       Historical Objective   Optimized Objective    % Difference
2023-07                  53.5049               54.9154           2.64%
2023-08                  54.1689               55.4180           2.31%
2023-09                  54.8612               55.8256           1.76%
2023-10                  54.2437               55.7810           2.83%
2023-11                  52.5116               53.7586           2.37%
2023-12                  51.1299               52.4233           2.53%
2024-01                  50.4104               51.6886           2.54%
2024-02                  51.7052               52.5998           1.73%
2024-03                  52.8237               54.1250           2.46%
2024-04                  54.4913               55.8831           2.55%
2024-05                  55.2611               56.2631           1.81%
2024-06                  54.4126               55.3756           1.77%
2024-07                  53.4113               54.3107           1.68%

Mean % difference (optimized vs. historical, in-model objective): 2.23%
Months compared: 13
```

**Computed value:** mean projected lift = **2.23%** across 13 months (range 1.68%–2.83%).

**What this does and does not support:** this is the optimizer's own
`sum(w_i * log(x_i + 1))` objective evaluated under two allocations with identical
learned weights and identical total monthly budget -- it is **not** observed or
predicted revenue in dollars, and it is an upper bound by construction (the optimized
split is search-derived from this exact objective, so it can only tie or beat the
historical split under it). It does not demonstrate a business result. The lift is
small (~2%) because the learned weights themselves came out nearly uniform across
channels (see the near-identical `Norm Weight` values in the run output) -- with 13
months of correlated channel spend, the weight-fitting step doesn't have much signal to
differentiate channels, so the optimizer's recommended split stays close to an even
split rather than concentrating budget.

## 2b. Held-out predictive accuracy

**Claim tested:** the optimizer's projected GMV, learned on a training window,
generalizes to held-out months better than naive baselines.

**Command:**
```
ds-pipeline/.venv/Scripts/python.exe scripts/metrics/backtest_optimizer.py
```

**Raw output (summary):**
```
Total months: 13, training months: 10, held-out months: 3

Training-set actual mean (gmv_next_minus_investment): 176,763.54
Held-out months: ['2024-05', '2024-06', '2024-07']
Actual values:    [243776.37, 203527.56, 174885.37]
Model predicted:  [183350.29, 180458.35, 176988.0]
Persistence pred: [220509.01, 243776.37, 203527.56]
Mean pred:        [176763.54, 176763.54, 176763.54]

BudgetOptimizer      R2:   -0.7483     MAPE:    12.44%     RMSE:    37,362.73
Persistence          R2:   -0.2447     MAPE:    15.23%     RMSE:    31,526.24
Mean                 R2:   -1.1752     MAPE:    13.90%     RMSE:    41,675.57

CAVEAT: n=3 held-out points. R2/MAPE/RMSE at this sample size are
indicative only, not a validated measure of predictive accuracy.
```

**Computed value:** on 3 held-out months, the model scores **R2=-0.75, MAPE=12.44%,
RMSE=37,363**. The persistence baseline (predict last month's actual) scores
**R2=-0.24, MAPE=15.23%, RMSE=31,526**. The model beats persistence on MAPE and RMSE,
but persistence has the least-negative R2 of the three.

**What this does and does not support:** with only 13 monthly rows and a 3-month
holdout, none of these numbers are statistically meaningful -- they are reported as
indicative, not validated. Notably this **contradicts a clean "model beats naive
baseline" claim**: R2 is negative for all three approaches (the mean baseline is
worst; the model and persistence are close, with no method dominating on every
metric). This does not support a predictive-accuracy claim as-is. If a resume bullet
needs a backtest number, MAPE (model 12.44% vs. persistence 15.23%) is the metric
where the model shows a real, if narrow, edge on this tiny holdout -- but that edge
should be described as "beat a naive persistence baseline on MAPE across a 3-month
holdout," not as validated forecasting accuracy.

