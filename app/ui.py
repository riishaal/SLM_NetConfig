"""
SLM-Based Intelligent Network Configuration
Streamlit Web Dashboard (Alternative Runner)
Builds on top of existing NetworkConfigAgent module.
"""

import os
import sys
import time
import streamlit as st

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.agent import NetworkConfigAgent

# Streamlit Page Config
st.set_page_config(
    page_title="SLM-Based Intelligent Network Configuration",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    .block-container {
        max-width: 1050px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #2563eb;
        margin-bottom: 1.5rem;
    }
    .section-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .flow-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .flow-arrow {
        text-align: center;
        font-size: 1.3rem;
        color: #64748b;
        margin: 4px 0;
    }
    .status-approved {
        background-color: #ecfdf5;
        color: #059669;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        border: 1.5px solid #a7f3d0;
        display: inline-block;
    }
    .status-refinement {
        background-color: #fffbeb;
        color: #d97706;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        border: 1.5px solid #fde68a;
        display: inline-block;
    }
    .status-error {
        background-color: #fef2f2;
        color: #dc2626;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        border: 1.5px solid #fecaca;
        display: inline-block;
    }
    .category-badge {
        background-color: #eff6ff;
        color: #1e40af;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-family: monospace;
        border: 1.5px solid #bfdbfe;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_agent_instance():
    return NetworkConfigAgent(load_model_weights=False)


agent = get_agent_instance()

# Header
st.markdown('<div class="main-title">SLM-Based Intelligent Network Configuration</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Natural Language &rarr; Network Configuration</div>', unsafe_allow_html=True)

# State initialization
if "requirement_text" not in st.session_state:
    st.session_state["requirement_text"] = ""
if "device_name" not in st.session_state:
    st.session_state["device_name"] = "Switch1"

# Callback for example buttons
def apply_example(text: str):
    st.session_state["requirement_text"] = text

# SECTION 1: Network Requirement
st.markdown("### 1. Network Requirement")
st.markdown("**Example Requirements:**")

ex_col1, ex_col2 = st.columns(2)
with ex_col1:
    if st.button("1. Create VLAN 20 named Accounts.", use_container_width=True):
        apply_example("Create VLAN 20 named Accounts.")
    if st.button("2. Configure GigabitEthernet0/1 with IP address 192.168.20.1 and subnet mask 255.255.255.0.", use_container_width=True):
        apply_example("Configure GigabitEthernet0/1 with IP address 192.168.20.1 and subnet mask 255.255.255.0.")

with ex_col2:
    if st.button("3. Configure GigabitEthernet0/1 as a trunk port and allow VLANs 10 and 20.", use_container_width=True):
        apply_example("Configure GigabitEthernet0/1 as a trunk port and allow VLANs 10 and 20.")
    if st.button("4. Configure OSPF routing using network 192.168.1.0/24 in area 0.", use_container_width=True):
        apply_example("Configure OSPF routing using network 192.168.1.0/24 in area 0.")

# Input text area
req_input = st.text_area(
    "Requirement Text:",
    value=st.session_state["requirement_text"],
    placeholder="Example: Create VLAN 20 named Accounts.",
    height=110,
    key="text_input_area"
)

# Update state if user typed directly
st.session_state["requirement_text"] = req_input

col_dev, col_btn = st.columns([1, 2])
with col_dev:
    dev_name = st.text_input("Target Device:", value=st.session_state["device_name"], key="dev_input")
    st.session_state["device_name"] = dev_name

with col_btn:
    st.write("")  # spacing
    generate_clicked = st.button("Generate Configuration", type="primary", use_container_width=True)

if generate_clicked and st.session_state["requirement_text"].strip():
    with st.spinner("Processing through SLM closed-loop pipeline..."):
        res = agent.process_request(st.session_state["requirement_text"], device_name=st.session_state["device_name"])
        st.session_state["latest_result"] = res

# Display Results if available
if "latest_result" in st.session_state:
    res = st.session_state["latest_result"]

    # Determine status
    if not res.get("success", True):
        v_status = "ERROR"
        status_class = "status-error"
    elif res.get("verified", False):
        v_status = "APPROVED (PASSED)"
        status_class = "status-approved"
    else:
        v_status = "REFINEMENT NEEDED"
        status_class = "status-refinement"

    st.divider()

    # Metrics row: Verification Result (3), Detected Category (4), Processing Time (5)
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown("#### 3. Verification Result")
        st.markdown(f'<div class="{status_class}">{v_status}</div>', unsafe_allow_html=True)

    with m_col2:
        st.markdown("#### 4. Detected Category")
        cat = res.get("detected_category", "UNKNOWN")
        st.markdown(f'<div class="category-badge">{cat}</div>', unsafe_allow_html=True)

    with m_col3:
        st.markdown("#### 5. Processing Time")
        duration = res.get("total_duration_sec", 0.0)
        st.metric(label="Duration", value=f"{duration}s")

    # Section 2: Generated Configuration (Cisco IOS) with Copy button
    st.markdown("### 2. Generated Configuration")
    st.code(res.get("final_config", "! No config"), language="cisco")

    # Section 5: Processing Information
    st.markdown("### 5. Processing Information")
    if res.get("saved_in_repo"):
        st.info(f"**Configuration Output Location:** `{res['saved_in_repo']}`")
    
    pt_export = res.get("packet_tracer_export", {})
    if isinstance(pt_export, dict) and pt_export.get("txt_path"):
        st.success(f"**Packet Tracer Export Location:** `{pt_export['txt_path']}`")

# Section: System Flow (Visual Flow at bottom)
st.divider()
st.markdown("### System Flow")
st.markdown("""
<div style="display: flex; flex-direction: column; align-items: center; max-width: 600px; margin: 0 auto;">
    <div class="flow-box" style="width: 100%;">Natural Language Requirement</div>
    <div class="flow-arrow">&darr;</div>
    <div class="flow-box" style="width: 100%;">Intent Detection</div>
    <div class="flow-arrow">&darr;</div>
    <div class="flow-box" style="width: 100%;">Configuration Generation</div>
    <div class="flow-arrow">&darr;</div>
    <div class="flow-box" style="width: 100%;">Verification</div>
    <div class="flow-arrow">&darr;</div>
    <div class="flow-box" style="width: 100%;">Cisco IOS Configuration</div>
</div>
""", unsafe_allow_html=True)
