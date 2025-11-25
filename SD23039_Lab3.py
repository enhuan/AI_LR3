import json
from typing import List, Dict, Any, Tuple
import operator
import streamlit as st

# --- 1. MINIMAL RULE ENGINE LOGIC ---

# Operator dictionary (for robust evaluation)
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

# --- KNOWLEDGE BASE: RULES (EXACTLY as specified in Lab Report 3) ---
SCHOLARSHIP_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Low CGPA not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        }
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        }
    },
    {
        "name": "Good candidate partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
]


def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate a single condition: [field, op, value]."""
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        # Convert values to float for accurate comparison, crucial for CGPA and income
        return OPS[op](float(facts[field]), float(value))
    except Exception:
        return False


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """All conditions must be true (AND)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))


def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns (best_action, fired_rules)
    - best_action: chosen by highest priority among fired rules
    - fired_rules: list of rule dicts that matched
    """
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return ({"decision": "REJECT", "reason": "No rule criteria matched for an award or review"}, [])

    # Sort in descending order of priority
    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best = fired_sorted[0].get("action", {"decision": "REVIEW", "reason": "Matched rule has no defined action"})
    return best, fired_sorted


# --- Helper function for clean output ---
def display_simple_conditions(conditions: List[List[Any]]):
    """Prints conditions in a simple, readable list format."""
    st.markdown("##### Conditions")
    for cond in conditions:
        field, op, value = cond
        # Use markdown list item and code styling for clarity
        st.markdown(f"* `{field}` **{op}** `{value}`")


# ----------------------------
# 2) STREAMLIT UI
# ----------------------------
st.set_page_config(page_title="Scholarship Advisory Rule-Based System", page_icon="🎓", layout="wide")
st.title("🎓 Scholarship Advisory Rule-Based System")
st.markdown("A transparent decision support tool based on the university's criteria for scholarship eligibility.")
st.info("""
    This application is a **Rule-Based System (RBS)** designed to automate transparent scholarship eligibility decisions.
    It evaluates applicant facts (CGPA, income, co-curricular score, and disciplinary actions) against a prioritized 
    Knowledge Base of IF-THEN rules to instantly determine the appropriate decision (AWARD FULL/PARTIAL, REJECT, or REVIEW).
""")

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.header("Applicant Facts")

    cgpa = st.number_input("Cumulative GPA (CGPA)", min_value=0.0, max_value=4.0, step=0.01, value=3.5)
    family_income = st.number_input("Monthly Family Income (RM)", min_value=0, step=500, value=6500)
    co_curricular_score = st.number_input("Co-curricular Score (0-100)", min_value=0, max_value=100, step=1, value=75)
    disciplinary_actions = st.number_input("Disciplinary Actions on Record", min_value=0, step=1, value=0)

    st.divider()
    st.header("Rules Configuration")
    st.caption("The system runs on the mandated rule set from the lab case study.")
    default_json = json.dumps(SCHOLARSHIP_RULES, indent=2)
    rules_text = st.text_area("Edit rules here (Optional)", value=default_json, height=300)

    run = st.button("Evaluate Eligibility", type="primary")

# --- FACTS DICTIONARY (Input for the engine) ---

# FIX APPLIED: Explicitly round float inputs to prevent excessive decimal places in display.
rounded_cgpa = round(float(cgpa), 2)
rounded_family_income = round(float(family_income))

facts = {
    # Key names MUST match the field names in the rules precisely
    "cgpa": rounded_cgpa,
    "family_income": rounded_family_income,
    "co_curricular score": int(co_curricular_score),
    "disciplinary_actions": int(disciplinary_actions),
}

# Display Applicant Facts in the main pane
st.subheader("Applicant Facts for Evaluation")
st.json(facts)

# --- RULE LOADING ---
try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rules must be a JSON array"
except Exception as e:
    st.error(f"Invalid rules JSON. Using defaults. Details: {e}")
    rules = SCHOLARSHIP_RULES

st.subheader("Active Knowledge Base")

# FIX APPLIED: Sort the list explicitly BEFORE using json.dumps() to avoid TypeError
sorted_rules_for_display = sorted(rules, key=lambda r: r.get('priority', 0), reverse=True)

with st.expander("Show all rules (Sorted by Priority)", expanded=False):
    # Use the pre-sorted list and ONLY include the 'indent' argument
    st.code(json.dumps(sorted_rules_for_display, indent=2), language="json")

st.divider()

# --- EVALUATION AND RESULTS ---
if run:
    # Use the rules array (unedited or edited) for evaluation
    action, fired = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Decision")
        decision = action.get("decision", "REVIEW")
        reason = action.get("reason", "-")

        # Display Decision Badge
        if "AWARD" in decision:
            st.success(f"✅ {decision}")
        elif decision == "REJECT":
            st.error(f"❌ {decision}")
        else:  # REVIEW or any default
            st.warning(f"⚠️ {decision}")

        st.markdown(f"**Reason**: {reason}")

    with col2:
        st.subheader("Matched Rules (by priority)")
        if not fired:
            st.info("No defined scholarship rule criteria were matched.")
        else:
            # Display the best match
            best_match_name = fired[0].get('name', '(unnamed)')
            best_match_priority = fired[0].get('priority', 0)
            st.markdown(f"**Best Match**: **{best_match_name}** | Priority: {best_match_priority}")
            st.caption(f"Chosen Action: {action.get('decision', '-')}")

            # Display all matched rules in detail using the cleaner format
            with st.expander("Show All Matched Rules and Details"):
                for i, r in enumerate(fired):
                    st.markdown(f"---")
                    st.write(f"**{i + 1}. {r.get('name', '(unnamed)')}** | Priority={r.get('priority', 0)}")
                    st.caption(f"Action: {r.get('action', {})}")

                    # Call the helper function to display conditions cleanly
                    display_simple_conditions(r.get('conditions', []))

else:

    st.info("Set applicant details in the sidebar and click **Evaluate Eligibility** to run the advisory system.")
