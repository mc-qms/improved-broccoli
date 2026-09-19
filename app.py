import json
from openai import OpenAI
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="The Stranger | Mock Auditor",
    page_icon="🔍",
    layout="centered",
)

# --- CLIENT & SECRETS INITIALIZATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    SYSTEM_SPEC = st.secrets["STRANGER_MASTER_SPEC"]
    CONSULTANT_SPEC = st.secrets["CONSULTANT_SPEC"]
except KeyError as e:
    st.error(
        f"Missing configuration secret: {e}. Set this in Streamlit App Settings."
    )
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

# --- PRE-LOADED SCRUBBED DEMO SAMPLES ---
SAMPLES = {
    "Select a demo sample...": "",
    "Scope Expander & Historical Shield (Bioreactor Deviation)": (
        "During routine review of the bioreactor pH loop, a transient drop to"
        " 6.42 was observed for 18 minutes. This type of intermittent sensor"
        " fluctuation is occasionally observed during warmer months and"
        " typically self-resolves after CIP cycle completion. Product quality"
        " was determined to be acceptable based on historical batch"
        " comparability."
    ),
    "Speculative Cause & 'Trust Me' Claim (QC Lab OOS)": (
        "Potency assay testing for Lot 2026-X yielded an OOS result of 88.4%"
        " (spec 95.0-105.0%). The analyst likely misaligned the sample"
        " carousel prior to initiating the automated injection sequence. A"
        " re-test was performed in duplicate which yielded 99.1%, confirming"
        " the batch remains safe, pure, and efficacious."
    ),
    "Collateral Admission & Mismatched Remediation (Filling CAPA)": (
        "Investigation into the off-spec fill volume revealed that SOP-4022"
        " step 4.1 is poorly worded and creates confusion during line setup."
        " Operator A performed the priming step out of sequence due to this"
        " ambiguity. To remediate this issue, Operator A was retrained on"
        " general filling awareness to prevent recurrence."
    ),
    "Symptom as Cause & Arbitrary Boundary (Component Assembly)": (
        "A burst pressure failure occurred during lot release testing of"
        " silicone tubing assembly Lot T-882. The root cause was determined to"
        " be mechanical stress concentration resulting in material wall"
        " rupture. Quarantine was applied strictly to sub-lot T-882-B"
        " manufactured during the morning shift; sub-lot T-882-A from the"
        " prior shift was cleared for release as no line alarms occurred."
    ),
    "Qualitative Smokescreen & 'Trust Me' (Sterilization Change)": (
        "To optimize cycle turnaround times, autoclave dwell time was reduced"
        " from 45 minutes to 35 minutes. Post-cycle bioburden levels were"
        " nominally comparable to historical baseline runs, showing minimal"
        " difference in microbial reduction. The modified cycle is considered"
        " fully qualified based on our extensive past operating history with"
        " similar porous loads."
    ),
}

# --- STATE MANAGEMENT ---
if "findings" not in st.session_state:
    st.session_state.findings = []
if "audit_scope" not in st.session_state:
    st.session_state.audit_scope = ""
if "consultant_output" not in st.session_state:
    st.session_state.consultant_output = {}

# --- HEADER & WATERMARK ---
st.title("The Stranger 🔍")
st.caption(
    "Zero-Inference Adversarial Cold-Read Engine | Designed for"
    " Quality-Critical Investigations"
)
st.write(
    "Upload or paste investigation text below. The auditor evaluates"
    " load-bearing claims with zero unearned trust."
)

# --- INPUT UI ---
selected_sample = st.selectbox(
    "Load Scrubbed Test Record:", list(SAMPLES.keys())
)
default_text = SAMPLES[selected_sample] if selected_sample else ""

user_input = st.text_area(
    "Investigation Narrative (max 2,500 chars):",
    value=default_text,
    height=175,
    max_chars=2500,
)

col_run, col_reset = st.columns([1, 4])
run_audit = col_run.button("Run Cold Read", type="primary")

if col_reset.button("Reset Session"):
    st.session_state.findings = []
    st.session_state.audit_scope = ""
    st.session_state.consultant_output = {}
    st.rerun()

# --- BACKEND EXECUTION: MODE 1 (THE STRANGER) ---
if run_audit and user_input.strip():
    with st.spinner("Cold read in progress... scanning for evidentiary gaps."):
        prompt_payload = f"INVESTIGATION TEXT FOR AUDIT:\n{user_input}"

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                response_format={"type": "json_object"},
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_SPEC},
                    {"role": "user", "content": prompt_payload},
                ],
            )
            parsed = json.loads(response.choices[0].message.content)
            st.session_state.findings = parsed.get("findings", [])
            st.session_state.audit_scope = parsed.get(
                "audit_scope", "Scope evaluated."
            )
            st.session_state.consultant_output = {}
        except Exception as err:
            st.error(f"Inference execution failure: {err}")

# --- DISPLAY FINDINGS QUEUE ---
if st.session_state.findings:
    st.divider()
    st.subheader("Audit Findings Queue")
    st.info(st.session_state.audit_scope)

    for item in st.session_state.findings:
        item_id = item.get("id", "Finding")
        category = item.get("category", "Unspecified Flaw")

        with st.expander(f"**{item_id}: {category}**", expanded=True):
            st.markdown(f"**Excerpt:** *\"{item.get('excerpt', '')}\"*")
            st.markdown(f"**The Exposure:** {item.get('exposure', '')}")

            if item.get("evidence_gap"):
                st.warning(f"**Evidence Gap:** {item.get('evidence_gap')}")

            # Mode 2 Diagnostic Trigger
            btn_key = f"consult_{item_id}"
            if st.button("Diagnose Evidence Requirements", key=btn_key):
                with st.spinner("Consultant formulating evidence boundary..."):
                    c_payload = (
                        f"FINDING: {category}\n"
                        f"EXCERPT: {item.get('excerpt', '')}\n"
                        f"EXPOSURE: {item.get('exposure', '')}\n"
                        f"GAP: {item.get('evidence_gap', 'None specified')}"
                    )
                    c_response = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        temperature=0.1,
                        messages=[
                            {"role": "system", "content": CONSULTANT_SPEC},
                            {"role": "user", "content": c_payload},
                        ],
                    )
                    st.session_state.consultant_output[item_id] = (
                        c_response.choices[0].message.content
                    )

            # Render Consultant Mode Drawer if active
            if item_id in st.session_state.consultant_output:
                st.markdown("---")
                st.markdown("**Evidence Architect Prescription:**")
                st.markdown(st.session_state.consultant_output[item_id])
