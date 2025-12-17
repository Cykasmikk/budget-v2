# Neuro-Symbolic AI Integration Report

**Date:** 2025-12-14
**Status:** Phases 1-3 Complete (Core & Advanced Features)
**Author:** Antigravity Agent

## 1. Executive Summary
This report documents the implementation of "Neuro-Symbolic" AI features into the `budget-v2` frontend. The integration combines **Neural** capabilities (probabilistic insights, LLM parsing) with **Symbolic** guarantees (deterministic rules, mathematical invariants, explainable traces).

## 2. Component Implementation Details

### 2.4 Budget Rules Engine (`rules-card.ts`)
*   **Objective:** Bridge Neural suggestions with Symbolic enforcement.
*   **Neural Feature:** **Suggested Rules**.
    *   *Logic:* AI detects recurring patterns (e.g., "Netflix" -> "Entertainment") and lists them as suggestions.
    *   *UI:* "Suggested Rules" tab displaying pattern, category, and occurrences.
*   **Symbolic Feature:** **Promotion Workflow**.
    *   *Logic:* One-click "Approve" (✅) action promotes a probabilistic suggestion to a deterministic rule.
    *   *UI:* "Active Rules" tab listing enforced strict rules with "Delete" capability.
*   **Files Modified:**
    *   `src/components/widgets/rules-card.ts`

### 2.5 Neuro-Symbolic Charts (`budget-chart.ts`)
*   **Objective:** Visualize uncertainty in forecasts.
*   **Neural Feature:** **Forecast Visualization**.
    *   *Logic:* Future/Predicted data points are rendered distinctly from historical data.
    *   *UI:* Dashed lines (`borderDash: [5, 5]`) for forecast segments.
*   **Symbolic Feature:** **Explicit Tooltips**.
    *   *Logic:* Tooltip data accessor checks `is_forecast` boolean.
    *   *UI:* Tooltips explicitly label values as "(Actual)" or "(Predicted)".
*   **Files Modified:**
    *   `src/components/budget-chart.ts`

### 2.6 What-If Simulator (`simulator-widget.ts`)
*   **Objective:** Deterministic scenario planning.
*   **Neural Feature:** **Scenario Input**.
    *   *UI:* Text input for users to describe scenarios naturally (e.g., "Cut dining by 20%").
*   **Symbolic Feature:** **Deterministic Calculation**.
    *   *Logic:* Parses the intent and applies a precise mathematical delta to the budget state to calculate `Projected Savings` and `New Total`.
    *   *UI:* "Simulator-Widget" integrated into the Dashboard Analysis Card.
*   **Files Modified:**
    *   `src/components/widgets/simulator-widget.ts`
    *   `src/components/widgets/analysis-card.ts` (Integration)
    *   `src/types/interfaces.ts` (Added `simulator` ViewMode)

## 3. Verification & Quality Assurance

### 3.1 New Test Plans
Six TDD test suites were created to strictly enforce these requirements:

1.  **`src/components/widgets/analysis-card.neuro.test.ts`**
    *   Verifies the `VerifiedBadge` appears when sums match.
    *   Verifies the `VerifiedBadge` disappears when invariants are broken.

2.  **`src/components/budget-table.neuro.test.ts`**
    *   Verifies low-confidence rows render with warning indicators.
    *   Verifies rule-matched rows render with lock icons.

3.  **`src/components/widgets/ai-chat.neuro.test.ts`**
    *   Verifies the `explanation-panel` validates existence of `explanation` data.

4.  **`src/components/widgets/rules-card.neuro.test.ts`**
    *   Verifies "Suggested Rules" tab rendering and approval logic.

5.  **`src/components/budget-chart.neuro.test.ts`**
    *   Verifies tooltips distinguish between Actuals and Forecasts.

6.  **`src/components/widgets/simulator-widget.neuro.test.ts`**
    *   Verifies deterministic calculation of savings based on input.

### 3.2 Manual Audit Steps
To independently audit this work, run the following command:
```bash
npm test src/components/widgets/analysis-card.neuro.test.ts src/components/budget-table.neuro.test.ts src/components/widgets/ai-chat.neuro.test.ts src/components/widgets/rules-card.neuro.test.ts src/components/budget-chart.neuro.test.ts src/components/widgets/simulator-widget.neuro.test.ts
```

## 4. Next Steps (Phase 4)
The implementation phases are verification. The next immediate steps are:
1.  **Browser Verification**: Run the application locally and verify the UI aesthetics and interactions in a real browser.
2.  **User Walkthrough**: Conduct a final review of the features with the user.

## 5. Roadmap: True Neuro-Symbolic AI Implementation

**Status:** Current implementation uses heuristics and basic validation. This section outlines concrete goals to achieve genuine neuro-symbolic AI capabilities.

### 5.1 Neural Component Goals

#### 5.1.1 Pattern Detection with Machine Learning
**Current State:** Keyword matching via hardcoded dictionaries  
**Goal:** Implement actual neural pattern detection

**Objectives:**
1. **Embedding-Based Pattern Discovery with Knowledge Graphs** (Updated for 2025)
   - Replace `CategoryClassifier.infer()` with state-of-the-art embeddings (e.g., `sentence-transformers/all-mpnet-base-v2` or `BAAI/bge-large-en-v1.5` for 2025)
   - **NEW:** Integrate knowledge graphs (Neo4j, Amazon Neptune, or open-source alternatives) to represent category hierarchies, merchant relationships, and transaction patterns
   - Use hybrid search: vector similarity + graph traversal to find semantically similar transactions
   - Leverage graph embeddings (e.g., Node2Vec, GraphSAGE) combined with text embeddings for richer pattern discovery
   - Cluster transactions by multi-modal similarity (text + graph structure)
   - **Success Metric:** Pattern detection accuracy >90% on unseen transactions, graph-augmented suggestions show 15% improvement over pure vector search

2. **Fine-Tuned Classification Model with Continual Learning** (Updated for 2025)
   - Train a lightweight transformer model (e.g., DistilBERT, or newer models like Phi-3-mini for efficiency)
   - **NEW:** Implement continual learning framework to prevent catastrophic forgetting when new patterns emerge
   - Use user-approved rules as training data with online learning (not just batch retraining)
   - Implement confidence scores with proper uncertainty quantification using conformal prediction or Bayesian neural networks
   - **NEW:** Use structured output/function calling from LLMs (Gemini, Claude, GPT-4) for zero-shot category inference as fallback
   - **Success Metric:** Classification F1-score >0.92, calibration error <0.03, model adapts to new patterns without forgetting old ones

3. **Probabilistic Pattern Suggestions**
   - Replace frequency counting with Bayesian inference
   - Calculate posterior probability: P(category | description, historical_data)
   - Provide confidence intervals, not just point estimates
   - **Success Metric:** Suggestions ranked by probability, not just count

4. **Online Learning Pipeline**
   - Implement feedback loop: user approvals/rejections update model weights
   - Use incremental learning to adapt to new patterns without full retraining
   - Track model performance over time with drift detection
   - **Success Metric:** Model accuracy improves with user feedback, drift alerts trigger retraining

**Implementation Files:**
- `backend/src/application/ml_services/pattern_detector.py` (new)
- `backend/src/application/ml_services/embedding_service.py` (new)
- `backend/src/application/ml_services/model_trainer.py` (new)
- Replace `CategoryClassifier.infer()` calls with ML service

#### 5.1.2 Natural Language Understanding for Simulator
**Current State:** Regex pattern matching (`/(?:cut|reduce|decrease)\s+(.+?)\s+by\s+(\d+(?:\.\d+)?)%/i`)  
**Goal:** LLM-based intent extraction and scenario parsing

**Objectives:**
1. **LLM-Powered Intent Extraction with Structured Output** (Updated for 2025)
   - Use LLM (Gemini 2.0 Flash, Claude 3.7 Sonnet, or GPT-4o) with **structured output/function calling** (not just JSON mode)
   - **NEW:** Implement agentic AI pattern - LLM acts as autonomous agent that can break down complex scenarios into atomic operations
   - Support complex scenarios: "If dining exceeds $500, reduce by 15%", "Increase marketing by 20% but cap at $10k", "Apply 10% cut to all categories over $1000"
   - Extract structured schema: action (cut/increase/set), target (category/project/merchant), amount/percentage, conditions, chained operations
   - **NEW:** Use few-shot learning with example scenarios stored in vector database for context-aware parsing
   - **Success Metric:** Parses 98% of natural language inputs correctly, handles 5+ step chained scenarios

2. **Few-Shot Learning with RAG** (Updated for 2025)
   - **NEW:** Use Retrieval-Augmented Generation (RAG) - store example scenarios in vector database
   - Retrieve similar examples dynamically based on user input similarity
   - Allow users to provide examples that improve parsing for similar future inputs
   - **NEW:** Implement semantic caching to avoid redundant LLM calls for similar inputs
   - **Success Metric:** System learns new scenario patterns from 2-3 examples, 40% reduction in LLM calls via caching

3. **Multi-Step Reasoning**
   - Support chained scenarios: "Cut dining by 20%, then increase marketing by the savings"
   - Use LLM to break down complex scenarios into atomic operations
   - **Success Metric:** Handles 3+ step scenarios correctly

**Implementation Files:**
- `backend/src/application/ml_services/scenario_parser.py` (new)
- Update `simulator-widget.ts` to call LLM parsing endpoint
- Add structured output schema for scenario parsing

#### 5.1.3 Probabilistic Forecasting
**Current State:** Holt-Winters forecasting with visual styling  
**Goal:** Bayesian forecasting with uncertainty quantification

**Objectives:**
1. **Bayesian Time Series Models** (Updated for 2025)
   - Implement probabilistic forecasting using **PyMC v5** (or newer) or **TensorFlow Probability** for GPU acceleration
   - **NEW:** Consider **Prophet 2.0** or **NeuralProphet** for hybrid neural-symbolic forecasting
   - Generate posterior predictive distributions, not just point estimates
   - Provide credible intervals (e.g., 80%, 95%) for forecast values
   - **NEW:** Use **conformal prediction** for distribution-free uncertainty quantification (more robust than Bayesian for non-stationary data)
   - **Success Metric:** Forecasts include uncertainty bands with proper coverage (95% intervals contain 95% of actuals)

2. **Monte Carlo Simulation**
   - Run 1000+ simulations to generate forecast distributions
   - Visualize uncertainty with violin plots or confidence bands in charts
   - Show probability of exceeding budget thresholds
   - **Success Metric:** Charts display uncertainty distributions, not just single lines

3. **Model Selection and Validation**
   - Compare multiple forecasting models (ARIMA, Prophet, LSTM, Transformer)
   - Use cross-validation to select best model per category
   - Track forecast accuracy over time and retrain when accuracy degrades
   - **Success Metric:** Forecast MAPE <10%, model selection automated

**Implementation Files:**
- `backend/src/application/ml_services/forecast_service.py` (refactor)
- `backend/src/application/ml_services/bayesian_forecast.py` (new)
- Update `budget-chart.ts` to render uncertainty bands

### 5.2 Symbolic Component Goals

#### 5.2.1 Formal Verification of Invariants
**Current State:** Simple sum check (`Math.abs(total - sum) < 0.02`)  
**Goal:** Formal verification using theorem provers

**Objectives:**
1. **Constraint-Based Verification**
   - Use Z3 or Alloy to formally verify budget invariants
   - Define invariants in first-order logic: `∀c ∈ categories: sum(transactions[c]) = breakdown[c]`
   - Generate proof certificates when invariants hold
   - **Success Metric:** Invariants verified with formal proofs, not just numeric checks

2. **Rule Conflict Detection**
   - Use constraint solver to detect conflicting rules before promotion
   - Example: Rule A matches "Netflix" → "Entertainment", Rule B matches "Netflix.*" → "Software"
   - Generate conflict reports with resolution suggestions
   - **Success Metric:** System prevents conflicting rules, suggests resolutions

3. **Temporal Logic for Forecasting**
   - Use temporal logic (LTL/CTL) to verify forecast properties
   - Example: "Forecast never exceeds 2x historical maximum"
   - Verify scenario simulations maintain invariants
   - **Success Metric:** Scenarios validated against temporal constraints

**Implementation Files:**
- `backend/src/application/symbolic/verification_service.py` (new)
- `backend/src/application/symbolic/constraint_solver.py` (new)
- Replace `checkInvariant()` with formal verification calls

#### 5.2.2 Proof-Generating Explanations
**Current State:** Metadata strings ("Generated by Google Gemini...")  
**Goal:** Symbolic reasoning traces with proof trees

**Objectives:**
1. **Proof Tree Generation**
   - Generate step-by-step proof traces for calculations
   - Example: "Total = Σ(categories) because: category_breakdown['Dining'] = $500 (from transactions 1, 3, 7), category_breakdown['Software'] = $300 (from transaction 2), ..."
   - Show derivation path from raw data to final result
   - **Success Metric:** Explanations include complete proof trees, not just metadata

2. **Symbolic Execution for Scenarios**
   - Use symbolic execution to explore all possible scenario outcomes
   - Generate explanation: "If dining cut by 20%: current=$500 → new=$400, savings=$100, new_total=$4900 (was $5000)"
   - Show intermediate calculation steps
   - **Success Metric:** Scenario explanations show complete calculation traces

3. **Contradiction Detection**
   - Detect when neural suggestions conflict with symbolic rules
   - Example: Neural suggests "Netflix" → "Entertainment" but symbolic rule says "Netflix.*" → "Software"
   - Generate explanation of conflict with resolution path
   - **Success Metric:** System detects and explains neural-symbolic conflicts

**Implementation Files:**
- `backend/src/application/symbolic/proof_generator.py` (new)
- `backend/src/application/symbolic/explanation_service.py` (new)
- Update `ai_chat_service.py` to use proof generation

#### 5.2.3 Deterministic Rule Engine
**Current State:** Regex pattern matching  
**Goal:** Formal rule system with conflict resolution

**Objectives:**
1. **Rule Precedence and Conflict Resolution**
   - Implement rule priority system (specificity, recency, user preference)
   - Use symbolic reasoning to determine which rule applies when multiple match
   - Generate explanations for rule selection
   - **Success Metric:** Rule conflicts resolved deterministically with explanations

2. **Rule Composition and Chaining**
   - Support rule chains: "If matches pattern A, then apply rule B, else rule C"
   - Use symbolic execution to verify rule chains don't create cycles
   - **Success Metric:** Complex rule chains work correctly, cycles detected

3. **Invariant Preservation**
   - Verify that rule applications preserve budget invariants
   - Use formal methods to prove: "Applying rule R maintains invariant I"
   - **Success Metric:** Rules validated before activation, invariants always preserved

**Implementation Files:**
- `backend/src/application/symbolic/rule_engine.py` (refactor)
- `backend/src/application/symbolic/rule_validator.py` (new)

### 5.3 Neuro-Symbolic Integration Goals

#### 5.3.1 Hybrid Reasoning Pipeline with Iterative Refinement
**Current State:** Neural and symbolic components operate independently  
**Goal:** True integration where neural and symbolic inform each other

**Objectives:**
1. **Iterative Refinement Architecture** (Updated for 2025)
   - **NEW:** Implement parallel integration - neural and symbolic process simultaneously, then combine results
   - **NEW:** Use iterative refinement - neural suggests, symbolic validates, neural refines based on validation feedback (3-5 iterations)
   - Use neural embeddings to guide symbolic constraint solving
   - Example: Neural suggests likely categories, symbolic verifies against rules, neural adjusts confidence based on verification
   - **Success Metric:** Symbolic verification 10x faster with neural guidance, iterative refinement improves accuracy by 12% over single-pass

2. **Symbolic Constraints for Neural Training**
   - Use symbolic rules as constraints during neural model training
   - Example: Neural model learns to never suggest categories that violate budget rules
   - **Success Metric:** Neural model respects symbolic constraints without post-processing

3. **Confidence Calibration**
   - Calibrate neural confidence scores using symbolic verification results
   - If symbolic verifies neural suggestion, increase confidence; if conflicts, decrease
   - **Success Metric:** Calibrated confidence scores correlate with actual accuracy (ECE <0.05)

4. **Continual Learning with Symbolic Constraints** (Updated for 2025)
   - **NEW:** Implement continual learning framework (e.g., Elastic Weight Consolidation, Progressive Neural Networks) to prevent catastrophic forgetting
   - Neural suggests, symbolic validates, neural learns from validation feedback
   - Create feedback loop: symbolic corrections improve neural model without forgetting previous patterns
   - **NEW:** Use knowledge distillation - symbolic rules distilled into neural model for efficiency
   - **Success Metric:** Neural accuracy improves over time with symbolic feedback, zero catastrophic forgetting after 100+ new pattern additions

**Implementation Files:**
- `backend/src/application/neuro_symbolic/hybrid_reasoner.py` (new)
- `backend/src/application/neuro_symbolic/calibration_service.py` (new)
- `backend/src/application/neuro_symbolic/iterative_refiner.py` (new)
- `backend/src/application/neuro_symbolic/continual_learner.py` (new)

#### 5.3.2 Explainable AI with Symbolic Proofs
**Current State:** Basic explanations  
**Goal:** Complete explainability with neural-symbolic reasoning traces

**Objectives:**
1. **Unified Explanation Framework**
   - Combine neural attention maps with symbolic proof trees
   - Show: "Neural model focused on 'Netflix' (attention=0.85), symbolic rule matched pattern 'Netflix.*', final decision: Entertainment"
   - **Success Metric:** All decisions have complete neural-symbolic explanations

2. **Counterfactual Explanations**
   - Generate: "If description was 'Netflix Premium' instead of 'Netflix', category would be 'Software' because rule R2 would match"
   - Use symbolic execution to explore alternative scenarios
   - **Success Metric:** System provides counterfactual explanations for all suggestions

3. **Confidence Decomposition**
   - Break down confidence scores: "Neural confidence: 0.85, Symbolic verification: +0.10, Final: 0.95"
   - Show which components contribute to final decision
   - **Success Metric:** Users understand why system is confident/uncertain

**Implementation Files:**
- `backend/src/application/neuro_symbolic/explanation_generator.py` (new)
- Update all explanation endpoints to use unified framework

### 5.4 Enterprise & 2025 Standards

#### 5.4.0 Knowledge Graph Integration (NEW for 2025)
**Current State:** No structured knowledge representation  
**Goal:** Integrate knowledge graphs for enhanced reasoning

**Objectives:**
1. **Knowledge Graph Construction**
   - Build graph schema: Categories, Merchants, Projects, Rules, Transactions as nodes
   - Define relationships: "belongs_to", "similar_to", "conflicts_with", "precedes"
   - Use graph database: Neo4j, Amazon Neptune, or open-source (ArangoDB, NebulaGraph)
   - **Success Metric:** Graph contains all transactions, categories, rules with relationships

2. **Hybrid Search: Vector + Graph**
   - Combine vector embeddings with graph traversal for pattern discovery
   - Example: Find transactions similar to "Netflix" (vector) that belong to "Entertainment" category (graph)
   - Use graph neural networks (GNNs) for learning on graph structure
   - **Success Metric:** Hybrid search 20% more accurate than vector-only or graph-only

3. **Graph-Enhanced Explanations**
   - Generate explanations by traversing graph: "Netflix → Entertainment because: similar_to(Netflix, Hulu) → Entertainment, belongs_to(Netflix, Streaming) → Entertainment"
   - Show reasoning paths through knowledge graph
   - **Success Metric:** Explanations include graph traversal paths

**Implementation Files:**
- `backend/src/infrastructure/knowledge_graph/graph_service.py` (new)
- `backend/src/infrastructure/knowledge_graph/graph_builder.py` (new)
- `backend/src/application/neuro_symbolic/graph_enhanced_reasoner.py` (new)

#### 5.4.1 Observability and Monitoring
**Objectives:**
1. **LLM Call Tracking**
   - Log all LLM requests: prompt, response, tokens, latency, cost
   - Track token usage per user/tenant with budgets and alerts
   - **Success Metric:** 100% of LLM calls logged, cost tracking per tenant

2. **Model Performance Monitoring**
   - Track neural model accuracy, drift, and calibration over time
   - Alert when model performance degrades below thresholds
   - **Success Metric:** Automated alerts for model degradation, performance dashboards

3. **Symbolic Verification Metrics**
   - Track verification time, proof complexity, conflict rates
   - Monitor invariant violations and rule conflicts
   - **Success Metric:** Verification metrics dashboard, anomaly detection

**Implementation Files:**
- `backend/src/infrastructure/observability/llm_tracker.py` (new)
- `backend/src/infrastructure/observability/model_monitor.py` (new)

#### 5.4.2 Model Management
**Objectives:**
1. **Model Versioning and Registry** (Updated for 2025)
   - Version all neural models with **MLflow 2.0+** or **Weights & Biases (W&B)** for better experiment tracking
   - **NEW:** Use **Hugging Face Model Hub** or **MLflow Model Registry** for model storage and deployment
   - Track model lineage: training data, hyperparameters, performance, graph structure (for knowledge graphs)
   - **NEW:** Implement model cards and data cards for transparency (MLflow 2.0+ supports this)
   - **Success Metric:** All models versioned with complete lineage, one-click rollback, model cards published

2. **A/B Testing Framework**
   - Test new models against production with traffic splitting
   - Compare neural vs symbolic vs hybrid approaches
   - **Success Metric:** A/B testing infrastructure, statistical significance testing

3. **Continuous Integration for AI**
   - Automated testing: model accuracy, symbolic verification, integration tests
   - Pre-commit hooks: verify models meet performance thresholds
   - **Success Metric:** CI/CD pipeline for AI components, automated quality gates

**Implementation Files:**
- `backend/src/infrastructure/ml/model_registry.py` (new)
- `backend/src/infrastructure/ml/ab_testing.py` (new)

#### 5.4.3 Security and Safety
**Objectives:**
1. **Prompt Injection Protection**
   - Sanitize user inputs before sending to LLMs
   - Detect and block prompt injection attempts
   - **Success Metric:** Zero successful prompt injections in security tests

2. **Output Validation**
   - Verify LLM outputs meet schema constraints before use
   - Use symbolic validation to catch hallucinated or invalid outputs
   - **Success Metric:** 100% of LLM outputs validated, invalid outputs rejected

3. **Adversarial Robustness**
   - Test neural models against adversarial inputs
   - Verify symbolic rules can't be exploited
   - **Success Metric:** Models pass adversarial robustness tests

**Implementation Files:**
- `backend/src/infrastructure/security/prompt_sanitizer.py` (new)
- `backend/src/infrastructure/security/output_validator.py` (new)

### 5.5 Success Metrics Summary (Updated for 2025)

**Neural Components:**
- Pattern detection accuracy >90% (with knowledge graph: +15% improvement)
- Classification F1-score >0.92
- Calibration error <0.03
- Scenario parsing accuracy >98%
- Forecast MAPE <8% (with conformal prediction coverage >95%)
- Zero catastrophic forgetting after 100+ new patterns

**Symbolic Components:**
- 100% of invariants formally verified
- Zero rule conflicts in production
- All explanations include proof trees
- Scenario validation maintains invariants

**Integration:**
- Symbolic verification 10x faster with neural guidance
- Iterative refinement improves accuracy by 12% over single-pass
- Neural model respects symbolic constraints (via knowledge distillation)
- Confidence calibration ECE <0.03
- All decisions have complete explanations (including graph traversal paths)
- 40% reduction in LLM calls via semantic caching

**Enterprise:**
- 100% LLM call logging and cost tracking
- Automated model performance monitoring
- Model versioning and A/B testing operational
- Zero security vulnerabilities

### 5.6 Implementation Priority (Updated for 2025)

**Phase 1 (Foundation - 3 months):**
1. Knowledge graph construction and integration (NEW - critical for 2025)
2. Embedding-based pattern detection with graph augmentation
3. Formal verification service (Z3 integration)
4. LLM call tracking and observability
5. Structured output/function calling for LLMs (NEW)
6. Proof generation for explanations

**Phase 2 (Integration - 3 months):**
1. Iterative refinement architecture (NEW - parallel + iterative)
2. Hybrid reasoning pipeline with graph-enhanced search
3. Bayesian forecasting with conformal prediction (NEW)
4. LLM-based scenario parsing with RAG and semantic caching (NEW)
5. Continual learning framework (NEW)
6. Model versioning and registry (MLflow 2.0+)

**Phase 3 (Enterprise - 2 months):**
1. A/B testing framework
2. Security hardening (prompt injection, output validation)
3. Performance optimization (hardware acceleration if needed)
4. Agentic AI capabilities for autonomous scenario execution (NEW)
5. Complete documentation with model cards

**Total Timeline:** 8 months to full neuro-symbolic AI implementation (updated with 2025 best practices)

### 5.7 Key 2025 Additions Summary

**What's New for December 2025:**
1. **Knowledge Graphs** - Essential for modern neuro-symbolic AI, enables hybrid search and graph-enhanced reasoning
2. **Iterative Refinement** - Parallel processing + multi-pass refinement for better accuracy
3. **Continual Learning** - Prevent catastrophic forgetting, adapt to new patterns without retraining
4. **Structured Output/Function Calling** - Modern LLM integration pattern, more reliable than JSON mode
5. **RAG + Semantic Caching** - Reduce LLM costs, improve context-aware parsing
6. **Conformal Prediction** - Distribution-free uncertainty quantification, more robust than pure Bayesian
7. **Agentic AI Patterns** - Autonomous agents that can break down and execute complex scenarios
8. **Graph Neural Networks** - Learn patterns from knowledge graph structure
9. **Model Cards & Data Cards** - Transparency and compliance requirements for 2025
10. **MLflow 2.0+ / W&B** - Modern experiment tracking and model registry

**Removed/Deprecated:**
- Pure vector search (replaced with hybrid vector+graph)
- Single-pass neural-symbolic integration (replaced with iterative refinement)
- Batch retraining (replaced with continual learning)
- Simple JSON mode for LLMs (replaced with structured output/function calling)
