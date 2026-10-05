# SLM-Based Intelligent Network Configuration

**Department of Computer Science & Engineering, MEA Engineering College**  
**Group Number:** 11  
- MEA23CS060: Muhammed Rishal K  
- MEA23CS062: Muhammed Shahil K  
- MEA23CS076: Rifa  
- MEA23CS078: Riza Parveen T  

**Project Guide:** Prof. Nusna Khalid CK  
**Primary Reference:** *"Network Self-Configuration Based on Fine-Tuned Small Language Models"*, IEEE Open Journal of the Communications Society (OJCOMS), Vol. 7, 2026.

---

## 1. Project Overview

Modern enterprise and cloud networks require frequent and intricate device configurations. Manual configuration via Command Line Interfaces (CLI) is time-consuming, requires specialized vendor expertise, and is highly prone to human misconfigurations—the primary cause of network outages and security vulnerabilities.

While Large Language Models (LLMs) have shown capability in natural language translation, they pose substantial barriers: high computational and memory requirements, slow translation latency, unpredictable hallucinations of invalid CLI keywords, and security/privacy risks associated with sending confidential network topologies to external cloud APIs.

**SLM-Based Intelligent Network Configuration** introduces a lightweight, privacy-preserving, on-premise framework that leverages a Fine-Tuned Small Language Model (SLM) integrated with an **Agentic Closed-Loop Verification Pipeline**:
- Translates natural language requirements into vendor-specific Cisco IOS XE configurations.
- Employs a structured 3-prompt strategy: **Requirement Classifier**, **Steps Generator**, and **Configuration Generator**.
- Executes **3-tier automated validation** (Syntax, Semantics, and User Intent).
- Performs deterministic **Error Detection and Auto-Correction/Suggestion**.
- Simulates network control/data plane states via a discrete **Network State Simulator**.
- Provides seamless export for **Cisco Packet Tracer** and **GNS3** demonstration.
- Evaluates performance using rigorous mathematical metrics (Syntax Accuracy, Goal Accuracy, Translation Latency, and Complexity Scores).

---

## 2. Complete System Architecture

```
User Natural Language Input (Requirement / Question)
                       │
                       ▼
         MODULE 2: AGENT / CONTROLLER
  ┌──────────────────────────────────────────────────┐
  │  Requirement Loader  ──>  Prompt Manager         │
  │          ▲                        │              │
  │          │ (Refinement Loop)      ▼              │
  │  Execution Controller <──  Result Logger         │
  └────────────────────────┬─────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
 MODULE 3: KB        MODULE 5: SLM       MODULE 7: CONFIG
- Cisco CLI Specs   - Llama-3.2-1B      - Cisco IOS XE
- CIDR Math Rules   - Qwen2.5-Coder     - Device Boundaries
- Reserved VLANs    - 3-Prompt Design   - Multi-device (~~~)
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
             MODULE 8: CONFIG VALIDATION
             ┌─────────────────────────┐
             │ Tier 1: Syntax (Batfish)│
             │ Tier 2: Semantic Bounds │
             │ Tier 3: Intent Fulfill  │
             └─────────────┬───────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       [Errors Found]             [Status: PASSED]
             │                           │
             ▼                           ▼
   MODULE 9 & 10: ERROR        MODULE 11: SIMULATOR
    DETECTION & ADVICE          - VLAN State DB
- Typo auto-fix ('acces')       - Interface IP Table
- Reserved VLAN check           - Routing / OSPF State
- Feedback to Agent loop        - ACL Packet Filter Walk
                                         │
                                         ▼
                               MODULE 12: VERIFIER
                                - Functional Assertions
                                - Packet Tracer Export
                                         │
                                         ▼
                                MODULE 13: EVALUATOR
                                - Syntax Accuracy Eq (2)
                                - Goal Accuracy Eq (4)
                                - Complexity Score Eq (7)
                                         │
                                         ▼
                              MODULE 14: STREAMLIT UI
```

---

## 3. Technology Stack

- **Core Language:** Python 3.10.10
- **Deep Learning & Fine-Tuning:** PyTorch, Hugging Face `transformers`, `peft` (LoRA), `accelerate`, `datasets`
- **Network Configuration Parsing:** `ciscoconfparse2`
- **Web Dashboard:** `streamlit`
- **Data & Visualization:** `pandas`, `numpy`, `matplotlib`, `seaborn`, `rich`
- **Automated Testing:** `pytest` (12/12 Automated Verification Scenarios)
- **Network Emulation / Target:** Cisco Packet Tracer / GNS3 script integration

---

## 4. Project Directory Structure

```
SLM/
├── app/
│   ├── __init__.py
│   ├── input_handler.py        # Module 1: Natural language entity extraction & intake
│   └── ui.py                   # Module 14: Interactive 5-tab Streamlit dashboard
├── controller/
│   ├── __init__.py
│   └── agent.py                # Module 2: 4-component Agent orchestrator with closed-loop
├── knowledge_base/
│   ├── __init__.py
│   ├── cisco_ios_commands.json # Cisco command specifications & allowed parameter ranges
│   ├── networking_rules.json   # Subnet masks, reserved VLANs, and typo dictionary
│   ├── config_patterns.json    # Standard configuration AST patterns
│   └── kb_manager.py           # Module 3: Knowledge Base retrieval and grounding engine
├── dataset/
│   ├── __init__.py
│   ├── build_dataset.py        # Module 4: 7-stage dataset engineering pipeline
│   ├── dataset_loader.py       # Dataset access utility for train, val, and benchmark sets
│   ├── train/                  # Declarative & Interrogative training JSONL files
│   ├── validation/             # Validation split
│   └── test/                   # 150-scenario benchmark test dataset
├── models/
│   ├── __init__.py
│   └── slm_engine.py           # Module 5: SLM 3-prompt engine (Classifier, Steps, CLI)
├── training/
│   ├── __init__.py
│   ├── lora_train.py           # Module 6: PEFT LoRA training pipeline (r=64, alpha=16)
│   └── SLM_NetConfig_Colab_FineTuning.ipynb # Google Colab Tesla T4 training notebook
├── generation/
│   ├── __init__.py
│   └── config_generator.py     # Module 7: Multi-device Cisco CLI formatter
├── validation/
│   ├── __init__.py
│   └── validator.py            # Modules 8 & 9: 3-tier validation (Syntax, Semantics, Intent)
├── correction/
│   ├── __init__.py
│   └── error_corrector.py      # Module 10: Auto-fix and suggestion diagnostics
├── simulation/
│   ├── __init__.py
│   ├── network_simulator.py    # Module 11: Discrete Cisco IOS device state machine
│   └── packet_tracer_exporter.py # Packet Tracer / GNS3 automation script generator
├── verification/
│   ├── __init__.py
│   └── verifier.py             # Module 12: Behavioral & functional policy assertions
├── evaluation/
│   ├── __init__.py
│   └── evaluator.py            # Module 13: Mathematical evaluation engine (Eq 1-9)
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py        # Automated 12-test suite for pytest
│   └── generate_test_report.py # Generates docs/TEST_RESULTS.md
├── output/
│   ├── ConfigsRepo/            # Approved, verified device configurations
│   ├── PacketTracer_Exports/   # Ready-to-paste Cisco Packet Tracer scripts
│   ├── agent_execution_history.jsonl
│   └── benchmark_evaluation_report.json
├── docs/
│   └── TEST_RESULTS.md         # Documented 12-test execution table
├── requirements.txt
├── IMPLEMENTATION_STATUS.md    # Real-time truthful status tracker
├── run.py                      # Master CLI and UI entrypoint
└── README.md
```

---

## 5. Installation and Setup Guide

### Step 1: Clone / Navigate to Workspace
```powershell
cd "c:\Users\MUHAMMED RISHAL K\OneDrive\Desktop\SLM"
```

### Step 2: Install Required Dependencies
All dependencies are recorded in `requirements.txt`:
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Verify the Installation
Run the automated test suite to ensure all 12 modules pass:
```powershell
python -m pytest tests/test_pipeline.py -v
```
*Expected Output:* `12 passed in < 1.0s`.

---

## 6. How to Run the System

### Option A: Interactive Web Dashboard (Recommended for Viva)
Launch the Streamlit user interface:
```powershell
python run.py --ui
```
or directly:
```powershell
python -m streamlit run app/ui.py
```
*The web browser will open at `http://localhost:8501` featuring:*
1. **Configuration Pipeline Tab:** Real-time intent translation, decomposed steps, and generated Cisco CLI.
2. **Validation & Errors Tab:** Syntax status (`PASSED`, `PARTIALLY_UNRECOGNIZED`), semantic bounds, and auto-fix suggestions.
3. **Simulation Tab:** Virtual device state (VLAN DB, Interface status, Routing table) and downloadable Packet Tracer scripts.
4. **Evaluation Tab:** Run the 150-scenario benchmark and compute IEEE 2026 accuracy and complexity metrics.
5. **Knowledge Base Tab:** Inspect Cisco commands, RFC 1918 subnets, and typo dictionaries.

### Option B: Command Line Interface (CLI)
Execute an immediate query via terminal:
```powershell
python run.py --cli --query "Create VLAN 10 named HR and assign FastEthernet0/1 to VLAN 10."
```

### Option C: Run 150-Scenario Benchmark Evaluation
Evaluate the framework using the mathematical formulas from the IEEE 2026 paper:
```powershell
python run.py --eval --samples 20
```

---

## 7. Mathematical Evaluation Metrics (IEEE OJCOMS 2026)

Our evaluation strictly adheres to the formulas defined in Section VII-B of the base paper:

1. **Syntax Accuracy (Equations 2 & 3):**
   $$\text{Syntax Accuracy} = \begin{cases} 1 & \text{if } \forall l_i, \text{valid}(l_i) = 1 \\ 0 & \text{if } \exists l_i : \text{valid}(l_i) = 0 \\ -1 & \text{if } \exists l_i : \text{valid}(l_i) = -1 \end{cases}$$
   Where $\text{valid}(l_i) = 1$ if command matches Cisco IOS XE grammar, $0$ if incomplete, and $-1$ if unrecognized.

2. **Goal Accuracy (Equation 4):**
   $$\text{Goal Accuracy} = \begin{cases} 1 & \text{if } C \text{ fully satisfies } R \\ 0 & \text{if } C \text{ partially satisfies } R \\ -1 & \text{if } C \text{ fails to satisfy } R \end{cases}$$

3. **Translation Latency (Equations 5 & 6):**
   $$\text{total\_dura\_time} = \frac{T_{\text{pci}} + T_{\text{gcc}}}{60}$$
   Normalized via min-max scaling to enable fair comparison across topologies.

4. **Complexity Score (Equations 7, 8 & 9):**
   $$\text{complexity\_score} = \frac{\text{norm\_total\_len} + \text{norm\_total\_dura\_time}}{2}$$
   Where $\text{total\_len} = \text{trans\_len} + \text{config\_len}$.

---

## 8. Cisco Packet Tracer Demonstration Procedure

1. Run the system via the Web UI (`python run.py --ui`) or CLI.
2. Select or enter any scenario (e.g., *VLAN 10 HR & VLAN 20 Accounts*).
3. The system automatically creates a ready-to-run automation script in `output/PacketTracer_Exports/`.
4. Open **Cisco Packet Tracer**.
5. Drag and drop a **Cisco Catalyst 2960 Switch** (or 2911 Router) onto the workspace.
6. Click the switch $\rightarrow$ click the **CLI** tab.
7. Open the generated script (`output/PacketTracer_Exports/..._pt_script.txt`), copy all lines, and paste into the CLI.
8. Type `show vlan brief` or `show ip interface brief` in Packet Tracer to observe the verified configuration running live!

---

## 9. 50% Review Demonstration Checklist

During the 50% review, demonstrate the following working sequence:
- **Demo 1 (Single VLAN):** Input `Create VLAN 10 named HR.` $\rightarrow$ Output: `vlan 10`, `name HR`, status APPROVED.
- **Demo 2 (Dynamic Adaptation):** Input `Create VLAN 20 named Accounts and assign Fa0/1 to VLAN 20.` $\rightarrow$ Output dynamically adapts to VLAN 20, Accounts, and Fa0/1.
- **Demo 3 (Error Detection):** Input `switchport mode acces` $\rightarrow$ System catches the syntax typo, flags line number, and marks FAILED.
- **Demo 4 (Error Correction):** System explains why `acces` is invalid and suggests `switchport mode access`, auto-correcting the configuration.
- **Demo 5 (Architecture & Test Evidence):** Show `IMPLEMENTATION_STATUS.md` and `docs/TEST_RESULTS.md` demonstrating that 12/12 automated test cases pass.

---

## 10. Viva Questions and Answers

**Q1: Why use a Small Language Model (SLM) instead of a large LLM like GPT-4?**  
*Answer:* Network configurations contain sensitive topological data, IP subnets, and credentials. Sending them to external cloud LLMs violates enterprise privacy. Furthermore, large LLMs require cloud GPUs, introduce high latency (3-20 minutes in base paper benchmarks), and frequently hallucinate non-existent CLI keywords. A fine-tuned SLM (e.g., Llama-3.2-1B / Qwen2.5-Coder-1.5B) runs completely on-premise, executes in $< 1.5$ seconds, and generates concise, deterministic commands.

**Q2: What is the 3-prompt strategy implemented in your agent?**  
*Answer:* As defined in Section IV-B of our IEEE 2026 base paper:
1. *Requirement Classifier Prompt:* Categorizes intent (VLAN, OSPF, ACL, DHCP, etc.).
2. *Steps Generator Prompt:* Decomposes multiplex requirements into ordered subtasks (e.g., interface setup, mode selection, IP assignment).
3. *Configuration Generator Prompt:* Positions the model as a virtual network administrator outputting strict Cisco IOS CLI without conversational filler, using `~~~` as device delimiters.

**Q3: How does the closed-loop verification cycle work?**  
*Answer:* Rather than outputting unverified code, the Agent passes generated CLI to the 3-tier Verifier. If syntax or semantic violations occur, the Verifier generates a structured feedback report. The Agent uses this report to either execute safe deterministic auto-correction or re-prompt the model. Only configurations reaching `PASSED` status are stored in `ConfigsRepo`.

**Q4: How do you evaluate the system?**  
*Answer:* We evaluate using the 4 mathematical metrics from Section VII-B of the base paper: Syntax Accuracy, Goal Accuracy, Translation Latency, and Complexity Score across an isolated 150-scenario benchmark dataset.
