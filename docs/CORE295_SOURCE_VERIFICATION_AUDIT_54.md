# Core-295 source verification audit 54: Society of Actuaries DeFi risk classification framework

**Date:** 2026-11-11  
**Status:** classification of existing source-register lead RISK-SOA-CLASSIFICATION; no equation is added to the formal catalogue or counted toward 295.

## 1. Source and stated purpose

Tara Chang, Joe Ho, Zachary Tirrell, Gwen Weng and Jo You, *A Risk Classification Framework for Decentralized Finance Protocols: Exploring Emerging Risks for Insurers and Reinsurers*, Society of Actuaries Research Institute, September 2022.

The report's purpose is to classify DeFi protocol risks for insurers, reinsurers and risk managers. It is a taxonomy and incident-analysis framework, not a mathematical model of a DeFi protocol or a source of governing equations.

## 2. Framework structure

The report organizes incident-based risks into four principal categories:
1. Smart-contract technical risk;
2. Smart-contract economic-design risk;
3. Cybersecurity operational risk;
4. Blockchain infrastructure risk.

Examples include logic errors, incorrect library/standard integration, price manipulation, collateralization failures, dysfunctional stablecoin stabilization mechanisms, governance, fraud, business disruption, MEV, transaction congestion, base-network malfunctions, scalability and cryptographic vulnerabilities.

The report additionally proposes higher-level social/people, financial and societal risk categories. It explicitly notes that the framework is not exhaustive at the subcategory/risk level and that the incident database is focused on economic-loss events.

## 3. Method and limitations relevant to Core-295

The incident review uses historical incidents available through year-end 2021, primarily from SlowMist with additional public-source corroboration. The authors focus on Ethereum and BNB Smart Chain incident records; Avalanche and Polygon events that duplicated incidents already counted on Ethereum/BNB Smart Chain are excluded. The paper states that it excludes price-volatility losses from its incident classification because other financial instruments may be more suitable for managing those exposures.

The framework therefore provides useful domain boundaries and risk-source terminology, but it does not provide:
- a quantitative risk function;
- a probability/severity model;
- a calibrated loss distribution;
- a protocol-specific equation or deterministic state transition;
- an independent statistical sampling unit for the 59-per-domain target.

Incident counts are not independent equation counts, and the taxonomy's categories should not be mistaken for scientific equation families.

## 4. Decision

**Disposition:** retain RISK-SOA-CLASSIFICATION as contextual taxonomy and domain-scope evidence only. It can inform risk labels, inclusion/exclusion rules and documentation of protocol-risk categories, but it is not a candidate equation source and cannot supply Core-295 equation records.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No incident data were downloaded, no risk model was fitted, and no experiments, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is report-level source review only.
