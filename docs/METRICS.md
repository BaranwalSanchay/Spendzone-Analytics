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

## 3b. API latency

**Claim tested:** `/api/upload` and `/api/budget-scenario` serve concurrent requests
at some stated p50/p95/p99 latency and throughput.

**Command:**
```
python scripts/metrics/load_test.py
```

**Raw output:**
```
Hardware: Windows-11-10.0.26200-SP0, Intel64 Family 6 Model 186 Stepping 3, GenuineIntel, 12 logical cores
Concurrency: 10, requests per endpoint: 60

/api/upload (n=60, concurrency=10):
  p50=71.0ms  p95=84.9ms  p99=92.7ms  throughput=131.2 req/s

/api/budget-scenario (n=60, concurrency=10):
  p50=33.9ms  p95=64.1ms  p99=72.3ms  throughput=254.4 req/s
```

**Computed value:** at concurrency 10 on the stated hardware: `/api/upload`
p50=71.0ms / p95=84.9ms / p99=92.7ms, 131.2 req/s; `/api/budget-scenario`
p50=33.9ms / p95=64.1ms / p99=72.3ms, 254.4 req/s.

**What this does and does not support:** this is a real network round trip -- the
script spins up an actual `uvicorn` process on a dedicated port and drives it with
concurrent `httpx.AsyncClient` requests, not an in-process test client. It's a single
uvicorn worker (no multi-process/multi-worker deployment config, which is how this
repo's `Dockerfile`/`docker-compose.yml` run it too) on one Windows laptop with 12
logical cores, at a fixed concurrency of 10 and 60 requests per endpoint -- these
numbers do not generalize to a production deployment, a different concurrency level,
or different hardware without re-measuring there.

## 3c. Dataset and feature inventory

**Claim tested:** the platform ingests/models some number of datasets, rows, months,
channels, and engineered features.

**Command:**
```
python scripts/metrics/dataset_inventory.py
```

**Raw output (totals):**
```
=== Totals across 3 sample datasets ===
Total rows: 2581
Distinct months covered (union across files): 13
Distinct marketing channels modeled: 7 -- ['Affiliates', 'Content Marketing', 'Digital', 'Online marketing', 'SEM', 'Sponsorship', 'TV']
Engineered feature group 'spend aggregate': 9 distinct column(s)
Engineered feature group 'kpi/business context': 9 distinct column(s)
Engineered feature group 'lagged/derived target': 2 distinct column(s)
Engineered feature group 'identifier/other': 2 distinct column(s)
Engineered feature group 'weather/holiday context': 11 distinct column(s)
```

**Computed value:** **3 sample datasets** (`sample_marketing_spend.csv`,
`Final_monthly.csv`, `Monthly_Master.csv`), **2,581 total rows**, **13 distinct
months** (2023-07 through 2024-07), **7 marketing channels** (TV, Digital,
Sponsorship, Content Marketing, Online marketing, Affiliates, SEM), and **33 distinct
engineered/context columns** across 5 feature groups (9 spend aggregates, 9
KPI/business-context columns, 2 lagged/derived targets, 11 weather/holiday-context
columns, 2 identifiers).

**What this does and does not support:** these are the **synthetic sample datasets**
generated by `scripts/generate_sample_data.py`, not the original proprietary data --
that was scrubbed during the Market-Lens -> Spendzone rebrand, so it's what's
reproducible in this repo. The counts are pulled directly from the CSVs and from
`generate_sample_data.py`'s own channel list (not eyeballed), but the feature-group
classification (spend/lagged/KPI/weather) is keyword-based and approximate -- a couple
of columns (`order_date_only`, `Month`) don't cleanly fit any bucket and are counted
separately as "identifier/other." This supports a claim about what the *pipeline is
built to handle* (channel count, feature breadth, monthly granularity), not a claim
about the scale of any real dataset it has actually processed.

## 4a. The LangGraph concurrency fix

**Claim tested:** the fix in commit `fff1c29` ("Fix LangGraph concurrent-state-update
crash in multi-agent report sections") actually changes whether the report-generation
graph crashes, and the section count named in that commit message is correct.

**Command:**
```
cd backend
python -m venv .venv && .venv/Scripts/python.exe -m pip install "langgraph>=0.3.10,<0.4" pytest
.venv/Scripts/python.exe -m pytest tests/test_report_graph_concurrency.py -v
```

**Raw output:**
```
tests/test_report_graph_concurrency.py::test_section_agent_mapping_has_four_multi_agent_sections PASSED
tests/test_report_graph_concurrency.py::test_pre_fix_pattern_raises_concurrent_update_error PASSED
tests/test_report_graph_concurrency.py::test_pre_fix_pattern_does_not_raise_for_single_agent_sections PASSED
tests/test_report_graph_concurrency.py::test_current_pattern_merges_cleanly_for_all_seven_sections PASSED

4 passed, 1 warning in 1.44s
```

The concurrent-update error the pre-fix pattern actually raises (captured while
debugging the test itself, before a mistake in the test's own buggy-node
reconstruction was fixed -- see "What this does and does not support" below):
```
langgraph.errors.InvalidUpdateError: At key 'messages': Can receive only one value
per step. Use an Annotated key to handle multiple values.
```

**Computed value:** `section_agent_mapping` has **4 of 7 sections** with 2+ agents
(`business_context`: 3 agents, `marketing_performance`: 2, `performance_drivers`: 2,
`marketing_roi`: 2) -- not 3, and not 5. **Neither number already in circulation is
right**: the harness task doc referenced "3 of 7" and commit `fff1c29`'s own message
says "5 of 7" -- both are off from what the mapping actually contains. The pre-fix
node pattern (reconstructed from `git show fff1c29^:backend/agents/report_generator.py`)
raises `InvalidUpdateError` for exactly those 4 sections and not for the other 3; the
current pattern merges cleanly for all 7.

**What this does and does not support:** this confirms the fix is real (the before/after
node patterns produce genuinely different LangGraph behavior, not just a cosmetic
diff) and pins down the correct section count from the source of truth
(`section_agent_mapping`, extracted via `ast` so the test can't silently drift from the
real mapping) rather than from either number already floating around. It does not
touch a real LLM, the SQL database, or any API key -- the six "agents" are inline stub
node functions, not `ROIAgent`/`ExplorationAgent`/etc. One honest note on how this test
came together: my first version of the pre-fix reconstruction added a `return state`
fallback for inactive branches that the real pre-fix code never had (it fell through
to an implicit `return None`) -- that bug in the *test* made every section crash,
masking the true 4-vs-3 split, and was caught and fixed by checking the reconstruction
against the actual git history rather than trusting the first result. Separately,
getting a compatible `langgraph`/`langchain-core` pair to install required a dedicated
`backend/.venv` pinned to the versions in `backend/pyproject.toml` -- an earlier
attempt to import the real (non-stubbed) `agents.report_generator` module pulled in
`langchain-groq`/`langchain-google-genai`/etc., and installing the latest versions of
those into the system Python conflicted with an already-installed newer
`langchain`/`langgraph` stack there, which is why this test avoids importing that
module at all.

## 4b. End-to-end report runtime and cost

**Claim tested:** the full 7-section report pipeline completes in some measured
wall-clock time, at some measured Groq token cost.

**Status: run, for real, against your Groq/Tavily keys.** Result up front, because it
contradicts a clean "generates a complete 7-section report" claim: **6 of 7 sections
completed; `business_context` failed and was replaced with a raw Groq rate-limit error
in the output report**, not real content. Full numbers and why, below.

**What was added:**
- `backend/utils/token_tracking.py`: `TokenUsageCallbackHandler`, a LangChain callback
  attached to the `ChatGroq` instance in `main.py` (`callbacks=[token_handler]`), so it
  captures every LLM call any agent makes through that shared instance -- prompt/
  completion/total tokens (from `response.llm_output["token_usage"]`, the OpenAI-
  compatible shape Groq's integration uses) and per-call wall-clock time.
- `compute_cost_usd()`: cost from Groq's own published per-model pricing --
  `GROQ_PRICING_PER_MILLION_TOKENS["openai/gpt-oss-120b"] = {"input": 0.15, "output":
  0.60}` (USD per 1M tokens), sourced directly from
  https://console.groq.com/docs/model/openai/gpt-oss-120b (checked 2026-09-10). Not
  estimated -- if `GROQ_MODEL` is overridden to a model not in that dict, cost comes
  back as `None` rather than a guess.
- `backend/main.py`'s `generate_markdown_report()`: now tracks each section's wall-
  clock separately, and separately accumulates only the `SECTION_PAUSE`/
  `QUESTION_PAUSE` sleeps this run actually executes (not a theoretical maximum), so
  total runtime can be reported both with and without that fixed overhead, as asked.
  Writes `backend/reports/token_usage_metrics.json` (model, total wall-clock, fixed-
  pause overhead, wall-clock excluding it, per-section breakdown, token totals, cost)
  after the run -- alongside the existing `report.md`/PDF output, no change to what
  `generate_markdown_report()` returns.

**Arithmetic verified without spending tokens, before the real run:** `compute_cost_usd(150000,
40000, 'openai/gpt-oss-120b')` -> `{'input_cost_usd': 0.0225, 'output_cost_usd': 0.024,
'total_cost_usd': 0.0465, ...}` -- 150,000 x ($0.15/1,000,000) = $0.0225; 40,000 x
($0.60/1,000,000) = $0.024; total $0.0465. Matches.

**Command actually run** (from `Spendzone-Analytics/`, using a venv with
`backend/pyproject.toml`'s dependencies installed and `backend/.env` populated --
`python main.py` is the intended production command, but this machine's WeasyPrint
install can't find its native Pango/GObject libraries, a Windows GTK runtime gap
unrelated to the LLM pipeline; `run_report_job.py` calls the same
`generate_markdown_report()` main.py calls, skipping only the PDF-conversion step that
needs those libraries):
```
backend/.venv/Scripts/python.exe scripts/metrics/run_report_job.py --confirm
```

**Raw output (`backend/reports/token_usage_metrics.json`, and the relevant line from
`backend/reports/report.md`):**
```
"business_context" section content in report.md:
Error generating content: Error in analysis: Error code: 429 - {'error': {'message':
'Rate limit reached for model `openai/gpt-oss-120b` in organization ... service tier
`on_demand` on tokens per minute (TPM): Limit 8000, Used 7140, Requested 2706. Please
try again in 13.845s. ...', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}

token_usage_metrics.json:
{
  "model": "openai/gpt-oss-120b",
  "total_wall_clock_s": 510.54,
  "fixed_pause_overhead_s": 60.0,
  "wall_clock_excluding_fixed_pauses_s": 450.54,
  "sections": [
    {"section": "executive_summary",     "wall_clock_s": 55.03,  "n_calls": 6,  "prompt_tokens": 2306, "completion_tokens": 1138, "total_tokens": 3444},
    {"section": "business_context",      "wall_clock_s": 74.81,  "n_calls": 5,  "prompt_tokens": 0,    "completion_tokens": 0,    "total_tokens": 0},
    {"section": "marketing_performance", "wall_clock_s": 50.72,  "n_calls": 5,  "prompt_tokens": 674,  "completion_tokens": 858,  "total_tokens": 1532},
    {"section": "performance_drivers",   "wall_clock_s": 113.33, "n_calls": 9,  "prompt_tokens": 2710, "completion_tokens": 1876, "total_tokens": 4586},
    {"section": "marketing_roi",         "wall_clock_s": 73.14,  "n_calls": 12, "prompt_tokens": 764,  "completion_tokens": 881,  "total_tokens": 1645},
    {"section": "budget_allocation",     "wall_clock_s": 13.28,  "n_calls": 4,  "prompt_tokens": 651,  "completion_tokens": 898,  "total_tokens": 1549},
    {"section": "implementation",        "wall_clock_s": 69.92,  "n_calls": 3,  "prompt_tokens": 3971, "completion_tokens": 2887, "total_tokens": 6858}
  ],
  "totals": {"n_calls": 44, "prompt_tokens": 11076, "completion_tokens": 8538, "total_tokens": 19614},
  "cost_usd": {"input_cost_usd": 0.001661, "output_cost_usd": 0.005123, "total_cost_usd": 0.006784,
               "input_price_per_million": 0.15, "output_price_per_million": 0.6}
}
```

**Computed value:** total wall-clock **510.54s (8m 31s)**; fixed
`SECTION_PAUSE`/`QUESTION_PAUSE` overhead **60.0s** (6 gaps between 7 sections at 10s
each; this run had 1 question per section, so no `QUESTION_PAUSE` gaps fired); real
work time **450.54s (7m 31s)**. Tracked usage: **11,076 prompt + 8,538 completion =
19,614 tokens** across 44 LLM calls, costing **$0.006784** at Groq's published rate
(11,076 x $0.15/1M = $0.001661; 8,538 x $0.60/1M = $0.005123; sum $0.006784).

**What this does and does not support:** two things this run surfaced outrank the
headline numbers above:

1. **The report did not actually complete all 7 sections.** `business_context` hit
   Groq's on-demand-tier rate limit (8,000 tokens/minute) mid-section -- three agents
   (`exploration_agent`, `market_agent`, `sql_agent`) run in parallel for that section,
   and together they burst past the per-minute cap. `SupervisorAgent.analyze()`
   catches the resulting exception and writes a raw API error into the markdown report
   instead of content. So "generates a complete 7-section report" is not what this run
   demonstrates -- it demonstrates 6 of 7 sections succeeding and 1 failing
   predictably under the account's current rate limit. A resume claim should say "6 of
   7" or describe this as a known rate-limit sensitivity, not claim full completion
   from this evidence.
2. **The token/cost totals above are a lower bound, not exact.** `business_context`
   shows `0` for every token field despite 5 successful LLM calls (82s of real
   `llm_wall_clock_s`) -- those specific calls' responses didn't populate
   `response.llm_output["token_usage"]` the way the other sections' calls did (likely a
   difference in how that section's agents return results, not something this
   instrumentation controls). So the real total tokens/cost for this run are higher
   than $0.006784, by an unmeasured amount. This is a real gap in the instrumentation,
   surfaced by an actual run rather than caught in the unit check above -- noting it
   here rather than quietly reporting a number I know is undercounted.

Separately, the general caveat: a single run's timing/cost is one data point (Groq
inference time varies with provider load; parallel agents' tool-calling step counts
aren't fully deterministic even at temperature 0). This run supports "a 7-section
report attempt took about 8.5 minutes and cost under a cent in tracked tokens, with
one section failing on a Groq rate limit" -- not a tight confidence interval on
either number, and not yet a claim of full, reliable completion.

## 4c. Manual-baseline comparison

**Claim tested:** the automated report pipeline is faster than a manual analyst
producing the same 7-section report.

**Recommendation: drop the manual-baseline comparison, report measured automated
runtime alone (4b) instead.** No real "X analyst hours" figure exists anywhere in this
repo -- not in a commit, a doc, or a data file -- so any number here would be invented
to make the comparison land somewhere specific, which is exactly what this whole
exercise is trying to avoid. A resume bullet can say "generates a 7-section report in
N minutes end-to-end" (once 4b measures N) without a baseline attached; that's a
true, checkable claim on its own. It just can't say "Nx faster than manual" or
"saves N analyst-hours" without a real number for the other side of that comparison.
If you have an actual timed instance of someone producing a comparable report by hand
(even a rough one, e.g. "our analyst took about a day for the quarterly version"),
give me that and I'll add a real comparison section -- but I won't manufacture one.
