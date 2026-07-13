from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import random

import pandas as pd
import streamlit as st


DEFAULT_FORWARDS = [
    "Steve",
    "Budd",
    "James",
    "Warren",
    "Evan",
    "Zach",
    "Wolfish",
]


@dataclass(frozen=True)
class SimulationResult:
    rows: list[dict[str, float | int | str]]
    tonight_pick: list[str]


def parse_forwards(raw_names: str) -> list[str]:
    names = [line.strip() for line in raw_names.splitlines() if line.strip()]
    deduped_names = list(dict.fromkeys(names))
    return deduped_names


def run_simulation(
    forwards: list[str],
    defense_slots: int,
    runs: int,
    seed: int | None,
) -> SimulationResult:
    rng = random.Random(seed)
    pick_counter: Counter[str] = Counter()

    for _ in range(runs):
        selected = rng.sample(forwards, defense_slots)
        pick_counter.update(selected)

    tie_breakers = {name: rng.random() for name in forwards}
    rows = [
        {
            "Forward": name,
            "Times picked": pick_counter[name],
            "Pick probability": pick_counter[name] / runs,
        }
        for name in forwards
    ]

    rows.sort(
        key=lambda row: (
            -int(row["Times picked"]),
            tie_breakers[str(row["Forward"])],
        )
    )
    tonight_pick = [str(row["Forward"]) for row in rows[:defense_slots]]
    return SimulationResult(rows=rows, tonight_pick=tonight_pick)


def probability_bar(probability: float) -> str:
    filled = round(probability * 20)
    return "#" * filled + "-" * (20 - filled)


st.set_page_config(
    page_title="Beer League D Draft",
    page_icon="D",
    layout="wide",
)

st.title("Dead Kings Defense Draft")
st.caption("A Monte Carlo excuse generator for deciding which forwards are moving back tonight.")

st.subheader("Draft Setup")
setup_roster_col, setup_controls_col = st.columns([1.1, 0.9], gap="large")

with setup_roster_col:
    raw_forwards = st.text_area(
        "Forwards in the hat",
        value="\n".join(DEFAULT_FORWARDS),
        height=190,
        help="Enter one forward per line. Seven is the classic chaos setting.",
    )

    forwards = parse_forwards(raw_forwards)
    st.caption(f"{len(forwards)} unique forwards entered")

with setup_controls_col:
    st.write("")
    st.write("")
    max_slots = max(1, min(len(forwards), 4))
    defense_slots = st.number_input(
        "Defense spots to fill",
        min_value=1,
        max_value=max_slots,
        value=min(2, max_slots),
        step=1,
    )
    runs = st.slider(
        "Monte Carlo runs",
        min_value=1_000,
        max_value=100_000,
        value=25_000,
        step=1_000,
    )
    use_seed = st.checkbox("Use repeatable seed", value=False)
    seed = st.number_input("Seed", value=47, step=1, disabled=not use_seed)
    run_button = st.button("Run the draft", type="primary", use_container_width=True)

st.divider()


if len(forwards) != 7:
    st.warning(
        f"Enter exactly 7 unique forwards to match tonight's setup. "
        f"Right now there are {len(forwards)}."
    )

if len(forwards) < 2:
    st.stop()

if defense_slots > len(forwards):
    st.error("Defense spots cannot exceed the number of available forwards.")
    st.stop()

current_inputs = {
    "forwards": forwards,
    "defense_slots": int(defense_slots),
    "runs": int(runs),
    "seed": int(seed) if use_seed else None,
}

if run_button or "last_result" not in st.session_state:
    st.session_state.last_result = run_simulation(
        forwards=current_inputs["forwards"],
        defense_slots=current_inputs["defense_slots"],
        runs=current_inputs["runs"],
        seed=current_inputs["seed"],
    )
    st.session_state.last_inputs = current_inputs

result: SimulationResult = st.session_state.last_result
inputs = st.session_state.last_inputs

if current_inputs != inputs:
    st.info("Settings changed. Click Run the draft to update tonight's assignment.")

col_pick, col_stats = st.columns([0.85, 1.15], gap="large")

with col_pick:
    st.subheader("Tonight's Defense Assignment")
    if len(result.tonight_pick) == 1:
        pick_text = result.tonight_pick[0]
    else:
        pick_text = " and ".join(result.tonight_pick)

    st.metric("Assigned to defense", pick_text)
    st.metric("Defense spots", inputs["defense_slots"])
    st.metric("Forwards in the hat", len(inputs["forwards"]))

    if inputs["seed"] is not None:
        st.info(f"Top Monte Carlo result using seed {inputs['seed']}. Ties are randomized.")
    else:
        st.info("Top Monte Carlo result. Ties are broken randomly.")

with col_stats:
    st.subheader("Monte Carlo Results")
    df = pd.DataFrame(result.rows)
    df["Pick probability"] = df["Pick probability"].map(lambda value: f"{value:.2%}")
    df["Luck meter"] = [
        probability_bar(row["Times picked"] / inputs["runs"]) for row in result.rows
    ]

    st.dataframe(
        df[["Forward", "Times picked", "Pick probability", "Luck meter"]],
        hide_index=True,
        use_container_width=True,
    )

st.divider()

st.subheader("Roster Odds")
chart_df = pd.DataFrame(result.rows)
st.bar_chart(chart_df, x="Forward", y="Pick probability", use_container_width=True)

st.caption(
    f"Simulated {inputs['runs']:,} random lineups. "
    "The assignment goes to the forward or forwards picked most often."
)
