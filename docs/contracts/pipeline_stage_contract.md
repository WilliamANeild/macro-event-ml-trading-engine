# Pipeline Stage Contract

## Purpose
This document defines the order of the main pipeline stages and the expected handoff between them.

## Stage Order

### 1. Universe
Defines the tradable instruments and their sleeve or sub-sleeve labels.

**Output:**
- instrument list
- instrument metadata
- theme and subtheme mappings

### 2. Data
Loads and caches market, macro, and reference data.

**Input:**
- universe output

**Output:**
- cleaned price data
- macro data
- cached raw inputs

### 3. Features
Builds model-ready features from market and macro data.

**Input:**
- data output

**Output:**
- feature rows by date, theme, subtheme, or instrument

### 4. Events
Builds event features from event or news inputs.

**Input:**
- raw event data
- optional market context

**Output:**
- event feature rows by date, theme, subtheme, or region

### 5. Experts
Each expert consumes context and returns one standardized `ExpertPrediction`.

**Input:**
- feature rows
- event features
- theme or subtheme context

**Output:**
- list of `ExpertPrediction` objects

### 6. Meta
Combines expert predictions into higher-level theme scores.

**Input:**
- expert predictions

**Output:**
- meta scores
- combined conviction or ranking outputs

### 7. Expression
Chooses how to express a theme view.

**Input:**
- meta outputs
- universe mappings

**Output:**
- expression choice such as ETF, single name, or blend

### 8. Portfolio
Transforms expressed views into constrained positions.

**Input:**
- expression outputs
- risk constraints

**Output:**
- target portfolio weights or notional exposures

### 9. Derivatives
Adds optional convexity overlays when allowed.

**Input:**
- portfolio outputs
- severity and confidence signals

**Output:**
- overlay trades
- premium usage
- overlay risk usage

### 10. Backtest
Runs walk-forward simulation with costs and attribution.

**Input:**
- portfolio decisions
- overlay decisions
- market data

**Output:**
- returns
- trades
- costs
- attribution records

### 11. Reporting
Builds summary outputs for review.

**Input:**
- backtest outputs
- expert outputs
- meta outputs

**Output:**
- attribution summary
- event replay summary
- audit trail

## Rules
1. Each stage should have a clear input and output.
2. Stages should not skip around the pipeline without a strong reason.
3. Contracts should stay stable even if implementation changes.
4. Early modules should return clean structured objects, not random dictionaries everywhere.