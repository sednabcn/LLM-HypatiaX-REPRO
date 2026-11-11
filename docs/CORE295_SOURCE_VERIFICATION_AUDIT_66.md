# Core-295 source verification audit 66: Perpetual funding-rate formula and protocol-specific premium dampers

**Date:** 2026-11-11  
**Status:** source check of the author-pool funding-rate candidate; no source-register or equation-catalogue record is added.

## 1. Candidate under review

The author-pool expression:
\[
f=\frac{F-S}{8S}
\]
is a normalized futures/spot basis divided by eight. It is not a universal perpetual-funding formula. It omits the mark/index or impact-bid/ask definition, premium averaging window, interest component, damper, cap/floor and funding-interval normalization used by real venues.

At most, it is a simplified basis-per-eight-period proxy under a separately stated convention. The symbol \(F\), \(S\), time unit and intended venue were not specified in the author pool, so the expression cannot be assigned a reproducible protocol meaning as written.

## 2. Deribit official funding specification

Deribit defines premium rate as:
\[
P=\frac{MarkPrice-IndexPrice}{IndexPrice}.
\]
Its uncapped funding rate is the premium after a symmetric damper:
\[
F_{uncapped}=
\max(\delta,P)+\min(-\delta,P),
\]
with default \(\delta=0.025\%\), followed by an instrument-specific cap/floor:
\[
F=\min(F_{max},\max(F_{min},F_{uncapped})).
\]
The published rate is expressed as an 8-hour rate, while funding is applied continuously. For a position held for \(\Delta t\):
\[
FundingPayment=F\cdot PositionSize\cdot\frac{\Delta t}{8\text{ hours}}.
\]
Deribit permits custom dampers and caps for individual instruments.

## 3. Binance official funding specification

Binance's published formula uses an average premium index \(P\), an interest-rate component \(I\), a symmetric premium damper and an interval normalization. Its 18 September 2025 update specifies:
\[
F=
\frac{P+\operatorname{clamp}(I-P,-d,d)}{8/N},
\]
where \(N\) is the funding interval in hours, \(d=0.05\%\) under the stated default, and the result is subject to contract-specific funding caps/floors. The premium index itself is derived from impact bid/ask prices relative to the index price and is time-averaged over the funding period. Funding payment is nominal position value multiplied by the adjusted funding rate.

Thus even two major perpetual venues use different premium constructions, dampers, interval rules and payment timing. These are versioned market microstructure mechanisms, not a universal \(F-S\) equation.

## 4. Structural classification

The general perpetual-funding family includes:
- mark/index or depth-weighted premium calculation;
- time aggregation of premium observations;
- interest-rate offset/damper;
- instrument-specific cap/floor;
- interval scaling and position-value payment.

Deribit and Binance are structurally related funding mechanisms but not identical formulas. Their different dampers, caps, index definitions and payment cadence are protocol parameters/specifications, not independent equation samples. The simple basis expression may be a rough proxy but cannot replace either venue's exact funding rule.

## 5. Decision

**Disposition:** reject the author-pool formula as a universal perpetual funding-rate equation. Retain it only as an underspecified basis proxy pending a named protocol, exact version, price-index definition, premium averaging method, interest component, damper, cap/floor, funding interval and payment convention. Do not add it to the formal equation catalogue.

No experiments, market-data retrieval, funding-rate calculation, validators, solvers, workflows, paid compute, API calls or trades were run. This is documentation-only source review.
