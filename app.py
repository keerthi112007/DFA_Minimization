
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="DFA Minimization Visualizer",
    page_icon="🔀",
    layout="wide"
)

st.title("🔀 DFA Minimization Visualizer")
st.write(
    "Enter your DFA details below. "
    "The dashboard will use your inputs to build the automaton."
)

# ---------- USER INPUTS ----------
st.sidebar.header("DFA Configuration")

states_input = st.sidebar.text_input(
    "Enter states (comma-separated)",
    value="q0, q1, q2, q3"
)

alphabet_input = st.sidebar.text_input(
    "Enter alphabet (comma-separated)",
    value="0, 1"
)

# Convert text into lists
states = [
    s.strip()
    for s in states_input.split(",")
    if s.strip()
]

alphabet = [
    s.strip()
    for s in alphabet_input.split(",")
    if s.strip()
]

# Remove duplicate entries while preserving order
states = list(dict.fromkeys(states))
alphabet = list(dict.fromkeys(alphabet))

# Select start state from the user-defined states
if states:
    start_state = st.sidebar.selectbox(
        "Select start state",
        options=states
    )
else:
    start_state = None
    st.sidebar.warning("Enter at least one state.")

# User decides which states are final
final_states = st.sidebar.multiselect(
    "Select final states",
    options=states,
    default=[],
    help="Select all accepting states. You can leave this empty."
)

# ---------- TRANSITION TABLE ----------
st.subheader("1. Enter Transition Table")

if states and alphabet:
    default_table = pd.DataFrame({
        "State": states,
        **{
            symbol: ["" for _ in states]
            for symbol in alphabet
        }
    })

    st.caption(
        "For every state and input symbol, enter the destination "
        "state. You can edit the cells directly."
    )

    transition_table = st.data_editor(
        default_table,
        num_rows="fixed",
        use_container_width=True,
        key="transition_editor"
    )

    st.info(
        "Example: if q0 moves to q1 on input 0, "
        "enter q1 in the row q0 under column 0."
    )

else:
    st.warning("Enter at least one state and one alphabet symbol.")

# ---------- SUMMARY ----------
st.subheader("2. DFA Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Number of States", len(states))
col2.metric("Alphabet Size", len(alphabet))
col3.metric("Number of Final States", len(final_states))

st.write("**States:**", states)
st.write("**Alphabet:**", alphabet)
st.write("**Start State:**", start_state)
st.write("**Final States:**", final_states)

# ---------- VALIDATION ----------
if states and alphabet and start_state is not None:
    if not final_states:
        st.warning(
            "No final states selected. "
            "This is allowed, but the DFA will reject every string."
        )

    if (
        "transition_table" in locals()
        and list(transition_table["State"]) == states
    ):
        destinations = []

        for symbol in alphabet:
            destinations.extend(
                transition_table[symbol].tolist()
            )

        missing = [
            str(value).strip()
            for value in destinations
            if pd.isna(value) or not str(value).strip()
        ]

        if missing:
            st.warning(
                "Some transitions are empty. "
                "Fill in every transition before minimization."
            )
        else:
            known_states = set(states)
            unknown = sorted({
                str(value).strip()
                for value in destinations
                if str(value).strip() not in known_states
            })

            if unknown:
                st.error(
                    "Unknown destination states: "
                    + ", ".join(unknown)
                )
            else:
                st.success(
                    "DFA inputs look valid. "
                    "You can proceed to the minimization algorithm."
                )

# ---------- DFA MINIMIZATION ----------
if states and alphabet and start_state is not None:
    if (
        "transition_table" in locals()
        and list(transition_table["State"]) == states
    ):
        try:
            delta = {}

            for _, row in transition_table.iterrows():
                q = str(row["State"]).strip()
                delta[q] = {}

                for symbol in alphabet:
                    dest = str(row[symbol]).strip()

                    if not dest or dest == "nan":
                        raise ValueError(
                            f"Missing transition for {q} on {symbol}"
                        )

                    if dest not in states:
                        raise ValueError(
                            f"Unknown destination state: {dest}"
                        )

                    delta[q][symbol] = dest

            if st.button("🚀 Minimize DFA", type="primary"):

                # Step 1: Find reachable states
                reachable = {start_state}
                stack = [start_state]

                while stack:
                    q = stack.pop()

                    for symbol in alphabet:
                        nxt = delta[q][symbol]

                        if nxt not in reachable:
                            reachable.add(nxt)
                            stack.append(nxt)

                active_states = [
                    q for q in states if q in reachable
                ]
                active_finals = set(final_states) & reachable

                # Step 2: Initial partition
                partitions = []

                accepting = active_finals
                rejecting = set(active_states) - accepting

                if accepting:
                    partitions.append(set(accepting))

                if rejecting:
                    partitions.append(set(rejecting))

                history = [
                    ("Initial partition P0",
                     [set(g) for g in partitions])
                ]

                # Step 3: Refine partitions
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
                            signature = tuple(
                                group_id[delta[q][symbol]]
                                for symbol in alphabet
                            )

                            buckets.setdefault(
                                signature, set()
                            ).add(q)

                        refined.extend(buckets.values())

                        if len(buckets) > 1:
                            changed = True

                    if not changed:
                        break

                    partitions = refined

                    history.append((
                        f"Refinement round {len(history)}",
                        [set(g) for g in partitions]
                    ))

                history.append((
                    "Final partition",
                    [set(g) for g in partitions]
                ))

                # Step 4: Create minimized DFA
                group_id = {
                    q: i
                    for i, group in enumerate(partitions)
                    for q in group
                }

                names = {
                    i: "{" + ", ".join(sorted(group)) + "}"
                    for i, group in enumerate(partitions)
                }

                min_states = list(names.values())
                min_start = names[group_id[start_state]]

                min_finals = {
                    names[i]
                    for i, group in enumerate(partitions)
                    if group & active_finals
                }

                min_delta = {}

                for i, group in enumerate(partitions):
                    representative = next(iter(group))

                    min_delta[names[i]] = {
                        symbol: names[
                            group_id[delta[representative][symbol]]
                        ]
                        for symbol in alphabet
                    }

                # Step 5: Display results
                st.divider()
                st.header("3. DFA Minimization Results")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Original reachable states",
                    len(active_states)
                )
                c2.metric(
                    "Minimized states",
                    len(min_states)
                )
                c3.metric(
                    "States reduced",
                    len(active_states) - len(min_states)
                )

                st.subheader("Partition Refinement Steps")

                for label, groups in history:
                    st.markdown(f"**{label}**")

                    st.write([
                        sorted(group) for group in groups
                    ])

                st.subheader("Equivalent States")

                merged = [
                    sorted(group)
                    for group in partitions
                    if len(group) > 1
                ]

                if merged:
                    for group in merged:
                        st.success(
                            "Merged states: " + ", ".join(group)
                        )
                else:
                    st.info("No equivalent states were found.")

                st.subheader("Minimized Transition Table")

                min_table = pd.DataFrame([
                    {
                        "State": (
                            "→ " if q == min_start else ""
                        ) + (
                            "* " if q in min_finals else ""
                        ) + q,
                        **min_delta[q]
                    }
                    for q in min_states
                ])

                st.dataframe(
                    min_table,
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "→ denotes the start state; "
                    "* denotes a final state."
                )

        except (ValueError, KeyError) as error:
            st.error(str(error))
