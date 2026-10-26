import streamlit as st
import pandas as pd

# Interactive DFA graph (install with: pip install streamlit-agraph)
from streamlit_agraph import agraph, Node, Edge, Config
import html
import math

st.set_page_config(
    page_title="DFA Minimization",
    page_icon="🔀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- STYLING --------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f7f9ff 0%, #f3f7fb 55%, #f8f5ff 100%);
    }
    .block-container { padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1450px; }
    .hero {
        padding: 1.5rem 1.7rem;
        border-radius: 20px;
        background: linear-gradient(120deg, #172554, #4338ca 65%, #7c3aed);
        color: white; margin-bottom: 1.2rem;
        box-shadow: 0 10px 28px rgba(49,46,129,.18);
    }
    .hero h1 { color: white; margin: 0 0 .4rem 0; font-size: 2.1rem; }
    .hero p { color: #e0e7ff; margin: 0; font-size: 1rem; }
    .section-label {
        font-size: 1.15rem; font-weight: 750; color: #1e293b;
        margin: .5rem 0 .8rem 0;
    }
    .partition-card {
        border: 1px solid #dbe4f0; border-radius: 15px; padding: 14px;
        background: rgba(255,255,255,.92); min-height: 110px;
        box-shadow: 0 4px 14px rgba(15,23,42,.045);
        margin-bottom: 10px;
    }
    .partition-heading {
        font-size: .78rem; color: #64748b; font-weight: 750;
        text-transform: uppercase; letter-spacing: .07em; margin-bottom: 10px;
    }
    .state-chip {
        display: inline-block; padding: 7px 11px; margin: 3px 4px 3px 0;
        border-radius: 9px; background: #eef2ff; color: #3730a3;
        border: 1px solid #c7d2fe; font-weight: 700; font-size: .94rem;
    }
    .partition-index {
        display: inline-block; color: #64748b; font-size: .8rem;
        font-weight: 700; margin-right: 6px;
    }
    .result-note {
        border-left: 4px solid #6366f1; padding: 10px 14px;
        background: #eef2ff; border-radius: 0 10px 10px 0;
        color: #312e81; margin: 8px 0 14px 0;
    }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e2e8f0;
        padding: 14px 16px; border-radius: 14px;
        box-shadow: 0 3px 12px rgba(15,23,42,.04);
    }
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        border-radius: 12px; overflow: hidden;
    }
    [data-testid="stSidebar"] {
        background: #eef2ff;
        border-right: 1px solid #dbe4f0;
    }
    .small-muted { color: #64748b; font-size: .88rem; }
    .stButton button[kind="primary"] {
        border-radius: 10px; font-weight: 700; padding: .65rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🔀 DFA Minimization </h1>
  <p>Build a DFA, inspect each partition-refinement step, and view the minimized automaton.</p>
</div>
""", unsafe_allow_html=True)

# -------------------- HELPERS --------------------
def state_set_label(group):
    return "{" + ", ".join(sorted(group)) + "}"

def render_partitions(label, groups, accent="indigo"):
    st.markdown(f'<div class="section-label">{html.escape(label)}</div>',
                unsafe_allow_html=True)
    if not groups:
        st.info("No partitions to display.")
        return
    cols_per_row = 4
    for start in range(0, len(groups), cols_per_row):
        row_groups = groups[start:start + cols_per_row]
        cols = st.columns(cols_per_row)
        for offset, group in enumerate(row_groups):
            index = start + offset
            chips = "".join(
                f'<span class="state-chip">{html.escape(state)}</span>'
                for state in sorted(group)
            )
            card = f"""
            <div class="partition-card">
              <div class="partition-heading">
                <span class="partition-index">P{index}</span> Partition {index + 1}
              </div>
              <div>{chips}</div>
            </div>
            """
            cols[offset].markdown(card, unsafe_allow_html=True)

def validate_csv_items(value):
    return list(dict.fromkeys(
        item.strip() for item in value.split(",") if item.strip()
    ))


# -------------------- INTERACTIVE DIAGRAM HELPER --------------------
def show_interactive_dfa(title, graph_states, graph_alphabet, graph_delta,
                         graph_start, graph_finals, graph_key):
    st.markdown(f'<div class="section-label">{html.escape(title)}</div>',
                unsafe_allow_html=True)
    st.caption("Drag states to rearrange the diagram. Use the mouse wheel to zoom; drag the background to pan.")

    nodes = []
    # Place states on a roomy circle so they do not bunch together.
    # The start state is placed on the left; remaining states are spread evenly.
    state_count = len(graph_states)
    positions = {}
    if state_count == 1:
        positions[graph_states[0]] = (0, 0)
    else:
        radius_x = max(220, 85 * state_count)
        radius_y = max(150, 62 * state_count)
        ordered = list(graph_states)
        if graph_start in ordered:
            ordered.remove(graph_start)
            ordered.insert(0, graph_start)
        for i, state in enumerate(ordered):
            angle = math.pi + (2 * math.pi * i / state_count)
            positions[state] = (
                int(radius_x * math.cos(angle)),
                int(radius_y * math.sin(angle)),
            )

    for state in graph_states:
        is_start = state == graph_start
        is_final = state in graph_finals
        if is_start and is_final:
            color = {"background": "#a7f3d0", "border": "#047857",
                     "highlight": {"background": "#6ee7b7", "border": "#065f46"}}
        elif is_start:
            color = {"background": "#bfdbfe", "border": "#1d4ed8",
                     "highlight": {"background": "#93c5fd", "border": "#1e40af"}}
        elif is_final:
            color = {"background": "#bbf7d0", "border": "#15803d",
                     "highlight": {"background": "#86efac", "border": "#166534"}}
        else:
            color = {"background": "#ede9fe", "border": "#7c3aed",
                     "highlight": {"background": "#ddd6fe", "border": "#6d28d9"}}

        label = ("▶ " if is_start else "") + ("★ " if is_final else "") + state
        nodes.append(Node(
            id=state,
            label=label,
            title=f"State: {state}\\n"
                  f"{'Start state\\n' if is_start else ''}"
                  f"{'Final/accepting state' if is_final else 'Non-final state'}",
            size=30 if is_start or is_final else 25,
            shape="dot",
            color=color,
            borderWidth=4 if is_final or is_start else 2,
            font={"size": 20, "face": "Arial", "color": "#172554"},
            x=positions[state][0],
            y=positions[state][1],
            physics=False,
        ))

    # Combine symbols that lead between the same pair of states into one labelled edge.
    edge_labels = {}
    for source in graph_states:
        for symbol in graph_alphabet:
            target = graph_delta[source][symbol]
            edge_labels.setdefault((source, target), []).append(symbol)

    edges = []
    state_order = {state: i for i, state in enumerate(graph_states)}
    for (source, target), symbols in edge_labels.items():
        if source == target:
            curve = {"type": "curvedCW", "roundness": 0.48}
        elif (target, source) in edge_labels:
            # Opposite-direction transitions curve in opposite directions,
            # keeping both arrowheads and labels visible.
            curve_type = "curvedCW" if state_order[source] < state_order[target] else "curvedCCW"
            curve = {"type": curve_type, "roundness": 0.22}
        else:
            curve = {"type": "continuous"}
        edges.append(Edge(
            source=source,
            target=target,
            label=", ".join(symbols),
            arrows="to",
            width=2,
            font={"size": 18, "align": "middle", "background": "#ffffff"},
            color={"color": "#64748b", "highlight": "#4f46e5"},
            smooth=curve,
        ))

    config = Config(
        width="100%",
        height=650,
        directed=True,
        physics=False,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#c7d2fe",
        collapsible=False,
        staticGraph=False,
        staticGraphWithDragAndDrop=True,
        link={"color": "#64748b", "highlightColor": "#4f46e5"},
    )
    agraph(nodes=nodes, edges=edges, config=config)
    st.markdown(
        '<p class="small-muted">Legend: ▶ start state · ★ accepting/final state · '
        'Arrow labels show input symbols.</p>',
        unsafe_allow_html=True,
    )

# -------------------- SIDEBAR CONFIGURATION --------------------
with st.sidebar:
    st.markdown("## ⚙️ DFA Configuration")
    st.caption("Define the states and input symbols first.")
    states_input = st.text_input(
        "States (comma-separated)", value="A, B, C, D", key="states_input"
    )
    alphabet_input = st.text_input(
        "Alphabet (comma-separated)", value="0, 1", key="alphabet_input"
    )
    states = validate_csv_items(states_input)
    alphabet = validate_csv_items(alphabet_input)

    if not states:
        st.warning("Enter at least one state.")
        start_state = None
        final_states = []
    else:
        start_state = st.selectbox("Start state", states, key="start_state")
        final_states = st.multiselect(
            "Final / accepting states", states, default=[], key="final_states"
        )

    st.divider()
    st.markdown("### How to use")
    st.markdown(
        "1. Enter states and alphabet.\n"
        "2. Fill every transition.\n"
        "3. Select the start and final states.\n"
        "4. Click **Minimize DFA**."
    )

# -------------------- TRANSITION TABLE --------------------
st.markdown('<div class="section-label">1 · Transition table</div>', unsafe_allow_html=True)
if states and alphabet:
    default_table = pd.DataFrame({
        "State": states,
        **{symbol: [""] * len(states) for symbol in alphabet}
    })
    st.caption("For each state and symbol, enter the destination state (for example, A → B on input 0 means enter B in A's row under 0).")
    transition_table = st.data_editor(
        default_table,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key=f"transition_editor_{'|'.join(states)}_{'|'.join(alphabet)}",
        column_config={
            "State": st.column_config.TextColumn("State", disabled=True),
            **{
                symbol: st.column_config.SelectboxColumn(
                    f"Input {symbol}",
                    options=[""] + states,
                    required=True,
                    help=f"Destination state for input {symbol}"
                )
                for symbol in alphabet
            }
        },
    )
else:
    transition_table = None
    st.warning("Enter at least one state and one alphabet symbol in the sidebar.")

# -------------------- DFA SUMMARY --------------------
st.markdown('<div class="section-label">2 · DFA overview</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total states", len(states))
m2.metric("Input symbols", len(alphabet))
m3.metric("Final states", len(final_states))
m4.metric("Transition entries", len(states) * len(alphabet))
summary1, summary2, summary3 = st.columns([1.2, 1, 1.4])
with summary1:
    st.markdown("**Start state**")
    st.markdown(f"`{start_state}`" if start_state else "Not selected")
with summary2:
    st.markdown("**Final states**")
    st.markdown(", ".join(f"`{s}`" for s in final_states) if final_states else "None selected")
with summary3:
    st.markdown("**Alphabet**")
    st.markdown(", ".join(f"`{s}`" for s in alphabet) if alphabet else "None")

# -------------------- MINIMIZATION --------------------
st.markdown("---")
st.markdown('<div class="section-label">3 · Minimize the DFA</div>', unsafe_allow_html=True)
st.caption("The algorithm first removes unreachable states, then repeatedly splits groups whose transitions lead to different partitions.")

if st.button("🚀 Minimize DFA", type="primary", use_container_width=True):
    if not states or not alphabet or start_state is None:
        st.error("Please enter at least one state and one alphabet symbol.")
        st.stop()

    if transition_table is None:
        st.error("Transition table is not available.")
        st.stop()

    delta = {}
    try:
        for _, row in transition_table.iterrows():
            q = str(row["State"]).strip()
            delta[q] = {}
            for symbol in alphabet:
                value = row[symbol]
                dest = "" if pd.isna(value) else str(value).strip()
                if not dest:
                    raise ValueError(f"Missing transition: state {q}, input {symbol}.")
                if dest not in states:
                    raise ValueError(f"Unknown destination state '{dest}' in transition from {q} on {symbol}.")
                delta[q][symbol] = dest
    except (ValueError, KeyError) as error:
        st.error(str(error))
        st.stop()

    # Step 1: Find reachable states from the start state.
    reachable = {start_state}
    stack = [start_state]
    while stack:
        current = stack.pop()
        for symbol in alphabet:
            nxt = delta[current][symbol]
            if nxt not in reachable:
                reachable.add(nxt)
                stack.append(nxt)

    active_states = [q for q in states if q in reachable]
    unreachable_states = [q for q in states if q not in reachable]
    active_finals = set(final_states) & reachable

    # Step 2: Initial partition: accepting and non-accepting states.
    partitions = []
    accepting = set(active_finals)
    rejecting = set(active_states) - accepting
    if accepting:
        partitions.append(accepting)
    if rejecting:
        partitions.append(rejecting)

    history = [("Initial partition P0", [set(g) for g in partitions])]

    # Step 3: Refine until no partition splits.
    while True:
        group_id = {
            q: i
            for i, group in enumerate(partitions)
            for q in group
        }
        refined = []
        changed = False

        for group in partitions:
            buckets = {}
            for q in sorted(group):
                signature = tuple(group_id[delta[q][symbol]] for symbol in alphabet)
                buckets.setdefault(signature, set()).add(q)
            refined.extend(buckets[key] for key in sorted(buckets))
            if len(buckets) > 1:
                changed = True

        if not changed:
            break

        partitions = refined
        history.append((f"Refinement round {len(history)}", [set(g) for g in partitions]))

    history.append(("Final partition", [set(g) for g in partitions]))

    # Create minimized DFA, with stable names for display.
    group_id = {
        q: i
        for i, group in enumerate(partitions)
        for q in group
    }
    names = {
        i: state_set_label(group)
        for i, group in enumerate(partitions)
    }
    min_states = [names[i] for i in range(len(partitions))]
    min_start = names[group_id[start_state]]
    min_finals = {
        names[i]
        for i, group in enumerate(partitions)
        if group & active_finals
    }

    min_delta = {}
    for i, group in enumerate(partitions):
        representative = sorted(group)[0]
        min_delta[names[i]] = {
            symbol: names[group_id[delta[representative][symbol]]]
            for symbol in alphabet
        }

    # -------------------- RESULTS --------------------
    st.markdown("---")
    st.markdown('<div class="section-label">4 · Minimization results</div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Reachable states", len(active_states))
    r2.metric("Minimized states", len(min_states))
    r3.metric("States reduced", len(active_states) - len(min_states))
    r4.metric("Equivalent groups", sum(1 for g in partitions if len(g) > 1))

    if unreachable_states:
        st.warning("Unreachable states removed: " + ", ".join(unreachable_states))
    else:
        st.success("All states are reachable from the selected start state.")

    with st.expander("🧭 Interactive original DFA diagram", expanded=True):
        show_interactive_dfa(
            "Original DFA",
            active_states,
            alphabet,
            delta,
            start_state,
            active_finals,
            "original_dfa_graph",
        )

    st.markdown('<div class="section-label">Partition refinement steps</div>', unsafe_allow_html=True)
    st.caption("Each card represents one partition. States inside the same card are currently considered equivalent.")
    for step_number, (label, groups) in enumerate(history):
        with st.expander(f"Step {step_number + 1} · {label}", expanded=(step_number == len(history) - 1)):
            render_partitions(label, groups)

    st.markdown('<div class="section-label">Equivalent states</div>', unsafe_allow_html=True)
    merged = [sorted(group) for group in partitions if len(group) > 1]
    if merged:
        cols = st.columns(min(3, len(merged)))
        for i, group in enumerate(merged):
            with cols[i % len(cols)]:
                chips = "".join(f'<span class="state-chip">{html.escape(q)}</span>' for q in group)
                st.markdown(
                    f'<div class="partition-card"><div class="partition-heading">Equivalent group {i + 1}</div>{chips}</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("No equivalent states were found. Every reachable state remains separate.")

    with st.expander("✨ Interactive minimized DFA diagram", expanded=True):
        show_interactive_dfa(
            "Minimized DFA",
            min_states,
            alphabet,
            min_delta,
            min_start,
            min_finals,
            "minimized_dfa_graph",
        )

    st.markdown('<div class="section-label">Minimized transition table</div>', unsafe_allow_html=True)
    min_table = pd.DataFrame([
        {
            "State": ("→ " if q == min_start else "") + ("* " if q in min_finals else "") + q,
            **min_delta[q],
        }
        for q in min_states
    ])
    st.dataframe(min_table, use_container_width=True, hide_index=True)
    st.caption("→ Start state    |    * Final / accepting state")

    with st.expander("View transitions as readable rules"):
        for q in min_states:
            for symbol in alphabet:
                st.write(f"**{q}** -- `{symbol}` --> **{min_delta[q][symbol]}**")

    st.markdown(
        '<div class="result-note"><b>Result:</b> States in each final partition are equivalent and can be merged into one state in the minimized DFA.</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown(
    '<p class="small-muted">DFA Minimization Studio · Partition refinement method</p>',
    unsafe_allow_html=True,
)
