"""
SLM-Based Intelligent Network Configuration
Interactive Web Dashboard & Demonstration Interface (Streamlit)
Connects directly to the backend Agent, Knowledge Base, SLM Engine,
Validator, Error Corrector, Network Simulator, and Evaluation modules.
"""

import os
import sys
import time
import json
import streamlit as st
import pandas as pd

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.agent import NetworkConfigAgent
from knowledge_base.kb_manager import KnowledgeBaseManager
from simulation.packet_tracer_exporter import PacketTracerExporter
from dataset.dataset_loader import DatasetLoader
from evaluation.evaluator import BenchmarkEvaluator


# Page Setup
st.set_page_config(
    page_title="SLM Network Configurator | MEA CSE Group 11",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .badge-vlan { background-color: #DBEAFE; color: #1E40AF; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-ospf { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-acl { background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-dhcp { background-color: #D1FAE5; color: #065F46; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_agent_instance():
    """Cache agent instance to avoid re-initializing resources."""
    return NetworkConfigAgent(load_model_weights=False)


@st.cache_resource
def get_kb_instance():
    return KnowledgeBaseManager()


agent = get_agent_instance()
kb = get_kb_instance()
loader = DatasetLoader()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/network-switch.png", width=64)
    st.title("SLM NetConfig")
    st.caption("B.Tech CSE Main Project • MEA Engineering College")
    st.markdown("**Group 11:**\n- Muhammed Rishal K\n- Muhammed Shahil K\n- Rifa\n- Riza Parveen T\n\n**Guide:** Prof. Nusna Khalid CK")
    
    st.divider()
    st.subheader("📚 Quick Test Scenarios")
    
    preset = st.selectbox(
        "Choose a Preset Requirement:",
        [
            "Custom Input",
            "VLAN 10 HR & VLAN 20 Accounts",
            "Trunk Port dot1q on Gi0/1",
            "Interface IP & SVI Gateway",
            "OSPF Routing Area 0",
            "DHCP Office Pool & Exclusions",
            "ACL Deny HTTP Port 80",
            "Multiplex Branch Configuration",
            "Invalid Command Typo (switchport mode acces)"
        ]
    )

    preset_texts = {
        "VLAN 10 HR & VLAN 20 Accounts": "Create VLAN 10 named HR and VLAN 20 for Accounts on Switch1, and assign Fa0/1 to VLAN 10.",
        "Trunk Port dot1q on Gi0/1": "Configure GigabitEthernet0/1 as an 802.1Q trunk port allowing VLANs 10, 20, and 30.",
        "Interface IP & SVI Gateway": "Enable IP routing, create SVI interface Vlan10 with IP 192.168.10.1 255.255.255.0, and bring it up.",
        "OSPF Routing Area 0": "Enable OSPF process 1, advertise network 192.168.10.0 0.0.0.255 in area 0, and set Gi0/2 as passive.",
        "DHCP Office Pool & Exclusions": "Configure DHCP pool OFFICE_NET for 192.168.10.0 255.255.255.0 with gateway 192.168.10.1 and DNS 8.8.8.8, excluding 192.168.10.1 to 192.168.10.10.",
        "ACL Deny HTTP Port 80": "Create an extended access list 101 to block TCP traffic on port 80 from 192.168.10.0/24 to any destination and apply it in on Gi0/1.",
        "Multiplex Branch Configuration": "Configure Switch1: Create VLAN 50 named Operations, set Fa0/5 to access VLAN 50, enable IP routing, assign SVI Vlan50 IP 10.50.1.1 255.255.255.0, and advertise in OSPF process 1 area 0.",
        "Invalid Command Typo (switchport mode acces)": "Configure interface FastEthernet0/1 with switchport mode acces and assign vlan 10."
    }

    st.divider()
    st.markdown("### ⚙️ System Engine")
    st.info("SLM Engine: **Llama-3.2-1B / Qwen2.5-Coder**\n\nMethod: **LoRA (r=64, α=16)**\n\nExecution: **Deterministic + On-Device**")


# Main Body
st.markdown('<div class="main-title">SLM-Based Intelligent Network Configuration</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Zero-Touch Autonomous Network Configuration with Small Language Models and Closed-Loop Verification</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Configuration Pipeline",
    "🛡️ Validation & Error Detection",
    "🧪 Network Simulation & Verification",
    "📊 Benchmark Evaluation",
    "📖 Knowledge Base & Docs"
])

# ----------------- TAB 1: PIPELINE -----------------
with tab1:
    default_text = preset_texts.get(preset, "") if preset != "Custom Input" else ""
    
    col_input, col_meta = st.columns([3, 1])
    with col_input:
        user_query = st.text_area(
            "Natural Language Network Requirement / Question:",
            value=default_text,
            placeholder="e.g. Create VLAN 10 for HR and assign FastEthernet0/1 to VLAN 10.",
            height=100
        )
    with col_meta:
        device_name = st.text_input("Target Device Name:", value="Switch1")
        run_btn = st.button("Generate & Verify Configuration", type="primary", use_container_width=True)

    if run_btn and user_query.strip():
        with st.spinner("Executing Agent Closed-Loop Pipeline..."):
            t_start = time.time()
            record = agent.process_request(user_query, device_name=device_name)
            latency = time.time() - t_start

        # Store in session state
        st.session_state["latest_record"] = record

    if "latest_record" in st.session_state:
        rec = st.session_state["latest_record"]
        
        st.success(f"Pipeline executed in {rec['total_duration_sec']}s • Closed-loop iterations: {rec['iterations_count']}")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Detected Intent Category", rec["detected_category"])
        with col_m2:
            st.metric("Input Format", rec["input_format"].capitalize())
        with col_m3:
            v_status = "Approved (PASSED)" if rec["verified"] else "Refinement Required"
            st.metric("Verification Status", v_status)
        with col_m4:
            st.metric("Saved in Repo", "Yes" if rec["saved_in_repo"] else "Pending")

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("1. Decomposed Subtasks (Steps Generator)")
            for s in rec["decomposed_steps"]:
                st.markdown(f"- {s}")

            st.subheader("2. Agent Closed-Loop History")
            for h in rec["cycle_history"]:
                st.markdown(f"**Iteration {h['iteration']}:** `{h['action']}` (Status: `{h['status']}`, Latency: `{h.get('duration_sec', 0)}s`)")
                if "correction" in h and h["correction"].get("corrections"):
                    for c in h["correction"]["corrections"]:
                        st.warning(f"Fault: `{c['detected']}`\nSuggestion: {c['suggestion']}")

        with col_right:
            st.subheader("3. Device Configuration (Cisco IOS)")
            st.code(rec["final_config"], language="cisco")
            if rec.get("saved_in_repo"):
                st.caption(f"📁 Transferred to ConfigsRepo: `{rec['saved_in_repo']}`")


# ----------------- TAB 2: VALIDATION & ERRORS -----------------
with tab2:
    st.subheader("Multi-Tier Configuration Validation (IEEE OJCOMS 2026)")
    st.markdown("Implements 3-tier validation: **Syntax** (Cisco CLI grammar), **Semantic** (mode/resource bounds), and **Intent** (entity fulfillment).")

    if "latest_record" in st.session_state:
        rec = st.session_state["latest_record"]
        val = rec["last_validation"]

        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            st.metric("Syntax Parse Status", val.get("syntax_status", "UNKNOWN"))
        with c_v2:
            st.metric("Syntax Accuracy Score", val.get("syntax_score", 0))
        with c_v3:
            st.metric("Goal Accuracy Score", val.get("goal_score", 0))

        if val.get("errors"):
            st.error(f"Detected {len(val['errors'])} Error(s):")
            for err in val["errors"]:
                st.markdown(f"- ❌ `{err}`")
        else:
            st.success("✅ Zero syntax or semantic errors detected in approved configuration.")

        if val.get("warnings"):
            st.warning(f"Warnings ({len(val['warnings'])}):")
            for w in val["warnings"]:
                st.markdown(f"- ⚠️ `{w}`")

        # Intent details
        intent_info = val.get("intent_details", {})
        if intent_info.get("fulfilled_goals"):
            st.markdown("#### Intent Fulfillment Verification:")
            for g in intent_info["fulfilled_goals"]:
                st.markdown(f"- ✔️ {g}")

        # Correction Recommendations
        corr = rec.get("last_correction", {})
        if corr.get("corrections"):
            st.divider()
            st.subheader("Automated Error Diagnostics & Correction")
            for item in corr["corrections"]:
                st.info(
                    f"**Detected:** `{item['detected']}`\n\n"
                    f"**Reason:** {item['reason']}\n\n"
                    f"**Suggested Correction:** {item['suggestion']}\n\n"
                    f"**Auto-Correctable:** {'Yes' if item['auto_correctable'] else 'No (requires user guidance)'}"
                )
    else:
        st.info("Run a configuration pipeline from Tab 1 to inspect validation results.")


# ----------------- TAB 3: NETWORK SIMULATION -----------------
with tab3:
    st.subheader("Discrete Network State Simulator & Verification")
    st.markdown("Models Cisco IOS device operational tables and runs functional policy assertions.")

    if "latest_record" in st.session_state:
        rec = st.session_state["latest_record"]
        verif = rec.get("verification_report", {})
        sim = rec.get("simulation_snapshot", {})

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("#### Functional Verification Probes")
            assertions = verif.get("assertions", [])
            if assertions:
                for a in assertions:
                    icon = "✅" if a["passed"] else "❌"
                    st.markdown(f"{icon} **{a['test']}**: {a['detail']}")
            else:
                st.info("No specific functional assertions required for this scenario.")

        with col_s2:
            st.markdown("#### Simulated Device Operational State")
            if sim:
                st.markdown("**VLAN Database:**")
                st.json(sim.get("vlan_database", {}))
                st.markdown("**Configured Interfaces:**")
                st.json(sim.get("interfaces", {}))
                if sim.get("routing_table"):
                    st.markdown("**Routing Table:**")
                    st.json(sim.get("routing_table", []))

        st.divider()
        st.subheader("Cisco Packet Tracer Automation Integration")
        pt_exp = rec.get("packet_tracer_export", {})
        if pt_exp and "txt_path" in pt_exp:
            st.success("Configuration exported for Cisco Packet Tracer / GNS3!")
            st.text(pt_exp.get("instructions", ""))
            
            with open(pt_exp["txt_path"], "r", encoding="utf-8") as f:
                st.download_button(
                    "📥 Download Packet Tracer Script (.txt)",
                    data=f.read(),
                    file_name=os.path.basename(pt_exp["txt_path"]),
                    mime="text/plain"
                )
    else:
        st.info("Run a configuration from Tab 1 to trigger network state simulation.")


# ----------------- TAB 4: EVALUATION BENCHMARK -----------------
with tab4:
    st.subheader("150-Scenario Research Benchmark & Metrics")
    st.markdown("Computes exact IEEE OJCOMS 2026 Equations (1)-(9): Syntax Accuracy, Goal Accuracy, Translation Latency, and Complexity Score.")

    col_bench, col_bench_stats = st.columns([1, 2])
    with col_bench:
        sample_count = st.slider("Number of benchmark scenarios to evaluate:", 5, 150, 20, step=5)
        run_bench_btn = st.button("Run Benchmark Evaluation", type="primary")

    if run_bench_btn:
        with st.spinner(f"Evaluating {sample_count} benchmark scenarios..."):
            evaluator = BenchmarkEvaluator(agent=agent)
            report = evaluator.run_benchmark(sample_limit=sample_count)
            st.session_state["bench_report"] = report

    if "bench_report" in st.session_state:
        rep = st.session_state["bench_report"]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Syntax Correctness", f"{rep['syntax_accuracy']['correct_pct']}%")
        m2.metric("Goal Accuracy", f"{rep['goal_accuracy']['correct_pct']}%")
        m3.metric("Average Latency", f"{rep['average_latency_sec']}s")
        m4.metric("Mean Complexity", f"{rep['mean_complexity_score']}")

        st.markdown("#### Evaluation Results Table (Sample)")
        df = pd.DataFrame(rep["individual_results"])
        st.dataframe(df[["benchmark_id", "category", "syntax_score", "goal_score", "duration_sec", "complexity_score", "verified"]].head(25), use_container_width=True)


# ----------------- TAB 5: KNOWLEDGE BASE -----------------
with tab5:
    st.subheader("Networking Domain Knowledge Base")
    st.markdown("Ground-truth context for Cisco IOS XE command validation, reserved entities, and subnet rules.")

    kb_tab1, kb_tab2, kb_tab3 = st.tabs(["Supported Commands", "Networking Rules", "Typo Dictionary"])
    
    with kb_tab1:
        st.json(kb.commands_data.get("commands", []))

    with kb_tab2:
        st.markdown("**Reserved VLANs:**")
        st.json(kb.rules_data.get("vlan_rules", {}).get("reserved_vlans", {}))
        st.markdown("**Subnet CIDR Table:**")
        st.json(kb.rules_data.get("cidr_to_masks", {}))

    with kb_tab3:
        st.markdown("**Auto-Correctable CLI Typo Mappings:**")
        st.json(kb.rules_data.get("typo_dictionary", {}))
