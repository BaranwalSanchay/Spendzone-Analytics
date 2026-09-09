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

## 2c. Negative marginal ROI spend share

**Claim tested:** some marketing channels have negative marginal ROI, and a
measurable share of total spend goes to those channels.

**Command:**
```
ds-pipeline/.venv/Scripts/python.exe scripts/metrics/roi_regression.py
```

**Raw output:**
```
Months after monthly aggregation: 13

Current-month model (spend -> same-month GMV) (n=13 months, intercept=2,374.89):
Channel                    Coefficient   Avg Monthly Spend
TV                              2.7370           16,858.62
Digital                         5.4301            9,732.39
Sponsorship                     5.5680            5,521.99
Content Marketing               5.2019            4,077.97
Online marketing                7.6936           10,442.23
Affiliates                     -6.5334            3,165.22  (negative marginal ROI)
SEM                             7.9177            2,984.89
Spend share absorbed by negative-marginal-ROI channels: 6.00%

Next-month model (spend -> following month's GMV) (n=12 months, intercept=42,329.29):
Channel                    Coefficient   Avg Monthly Spend
TV                              3.8815           16,997.26
Digital                       -10.8885            9,884.44  (negative marginal ROI)
Sponsorship                    87.2342            5,524.83
Content Marketing             -47.3744            4,047.93  (negative marginal ROI)
Online marketing                3.2867           10,457.01
Affiliates                    -49.2386            3,153.31  (negative marginal ROI)
SEM                            22.2945            2,955.24
Spend share absorbed by negative-marginal-ROI channels: 32.22%
```

**Computed value:** current-month model: 1 of 7 channels (Affiliates) has a negative
coefficient, absorbing **6.00%** of spend. Next-month model: 3 of 7 channels (Digital,
Content Marketing, Affiliates) are negative, absorbing **32.22%** of spend.

**What this does and does not support:** these are `roi.py`'s own regression method
(channel spend -> GMV, current- and next-month variants) run directly against
`scripts/sample_data/Monthly_Master.csv`, without the `roi.py` tool's two
dataset-specific adjustments that don't apply to this data (a x1e7 crore-to-rupee
conversion, and hardcoded month exclusions -- see `roi_regression.py`'s docstring).
With 13 (or 12) monthly observations against 7 channel predictors, this regression is
poorly identified: the next-month model's coefficients swing as high as +87 and as low
as -49, which is a strong sign of overfitting to a handful of data points rather than a
stable estimate of channel effectiveness. Treat both spend-share numbers as
illustrative of the method, not as a validated attribution result -- and note the two
models don't even agree on which channels are negative, so no single "X% of spend goes
to negative-ROI channels" claim is defensible from this data without more observations.

## 2d. Robyn benchmark

**Claim tested:** compare the platform's own model against Meta's Robyn MMM as a
benchmark.

**Status: not run.** `robynpy` (pinned in `ds-pipeline/requirements.txt`) depends on
`rpy2`, which requires a working R installation for its Python-to-R bridge. No R or
`Rscript` is present on this machine (`which R` / `which Rscript` both fail), and
`Robyn.ipynb`'s own recorded run confirms it was last executed in a different
environment that had R installed (`/Library/Frameworks/Python.framework/...`, i.e. a
Mac with R already set up), not this one.

**What this does and does not support:** nothing -- there is no Robyn result to report
from this repo in its current state. Per the Stage 0 recommendation, this benchmark
claim should be dropped rather than describing a model that was never run here. If you
want a real Robyn comparison, that requires installing R locally (or in CI) and
re-running `Robyn.ipynb` against the same `scripts/sample_data/` inputs used above --
I can do that if you supply/install R. Absent that, 2b's backtest against naive
baselines is the only validated-effort predictive-accuracy claim this repo supports.

## 3a. Ingestion throughput

**Claim tested:** `/api/upload` (parse + schema validation + profiling) processes
marketing-spend CSVs at some stated rows/second, and that rate holds up as file size
grows.

**Command:**
```
python scripts/metrics/ingestion_throughput.py
```

**Raw output:**
```
  Days      Rows   Median Time (s)      Rows/sec
    30       210            0.0058        36,108
    90       630            0.0106        59,433
   365      2555            0.0106       240,995
  1000      7000            0.0161       435,906
  3000     21000            0.0281       747,015
```

**Computed value:** throughput ranges from **~36k rows/sec** at 210 rows up to
**~747k rows/sec** at 21,000 rows (median of 5 requests per size).

**What this does and does not support:** this times `/api/upload`'s actual processing
(pandas CSV parse, schema check, per-column profiling) via FastAPI's in-process
`TestClient` -- it isolates server-side compute from network transport (that's covered
in 3b) and from disk I/O (the CSV is built in memory, not read from disk). Throughput
rises with file size because a roughly fixed per-request overhead (FastAPI routing,
response-model validation) gets amortized over more rows -- so "rows/sec" at small
sizes understates steady-state throughput and shouldn't be quoted alone without the
file size it was measured at. This says nothing about behavior under concurrent
uploads (3b) or on real network-attached storage.

