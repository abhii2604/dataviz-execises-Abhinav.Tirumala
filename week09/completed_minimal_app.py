#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""World Happiness Report 2023 interactive dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="World Happiness Report",
    page_icon="🌐",
    layout="wide",
)

st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")


@st.cache_data
def load_data():
    """Find the course dataset and load it."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "data" / "world_happiness_2023.csv",
        here / "data" / "world_happiness_2023.csv",
        Path.cwd() / "data" / "world_happiness_2023.csv",
        Path.cwd() / "world_happiness_2023.csv",
    ]
    data_file = next((path for path in candidates if path.exists()), None)
    if data_file is None:
        raise FileNotFoundError(
            "Could not find world_happiness_2023.csv. Place it in a "
            "'data' folder beside the project, or in the project root."
        )

    data = pd.read_csv(data_file)
    expected = [
        "Country", "Region", "Score", "GDP", "Social_Support",
        "Life_Expectancy", "Freedom", "Generosity", "Corruption",
    ]

    # The lecture dataset contains these nine fields in this order.
    if len(data.columns) == len(expected):
        data.columns = expected

    missing = [column for column in expected if column not in data.columns]
    if missing:
        raise ValueError(
            "The CSV does not have the expected World Happiness Report "
            f"columns. Missing: {', '.join(missing)}"
        )

    for column in expected[2:]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["Country", "Region", "Score"])
    return data


try:
    df = load_data()
except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.info(
        "Add the course file named 'world_happiness_2023.csv' to the "
        "project's data folder, then rerun the app."
    )
    st.stop()


# Sidebar controls
with st.sidebar:
    st.header("Filters")
    regions = ["All Regions"] + sorted(df["Region"].dropna().unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N countries", min_value=5, max_value=25, value=15)

filtered = (
    df.copy()
    if selected_region == "All Regions"
    else df[df["Region"] == selected_region].copy()
)

if filtered.empty:
    st.warning("There are no countries available for this filter.")
    st.stop()


# KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Countries", f"{len(filtered)}")
average_score = filtered["Score"].mean()
global_average = df["Score"].mean()
col2.metric(
    "Average happiness score",
    f"{average_score:.2f}",
    f"{average_score - global_average:+.2f} vs global",
)
happiest_country = filtered.loc[filtered["Score"].idxmax(), "Country"]
col3.metric("Happiest country", happiest_country)

st.divider()


# Chart 1: top countries by happiness score
top = filtered.nlargest(top_n, "Score").sort_values("Score")
fig_top = px.bar(
    top,
    x="Score",
    y="Country",
    orientation="h",
    labels={"Score": "Happiness score (0–10)", "Country": ""},
    title=f"Top {min(top_n, len(top))} Happiest Countries — {selected_region}",
    template="plotly_white",
)
fig_top.update_layout(
    title_font=dict(family="Arial", size=16, color="slategrey"),
    xaxis=dict(range=[0, max(8, float(top["Score"].max()) + 0.2)]),
    yaxis={"categoryorder": "total ascending"},
    margin=dict(l=10, r=20, t=60, b=30),
)
st.plotly_chart(fig_top, use_container_width=True)

st.divider()


# Chart 2 (class exercise): regional score difference from global average.
# Zero is the meaningful midpoint: regions above zero are above the
# global average, and regions below zero are below it.
regional = (
    df.groupby("Region", as_index=False)["Score"]
    .mean()
    .rename(columns={"Score": "Regional average"})
)
regional["Difference from global average"] = (
    regional["Regional average"] - global_average
)
regional = regional.sort_values("Difference from global average")
max_difference = max(
    abs(float(regional["Difference from global average"].min())),
    abs(float(regional["Difference from global average"].max())),
    0.01,
)

fig_region = px.bar(
    regional,
    x="Difference from global average",
    y="Region",
    orientation="h",
    color="Difference from global average",
    color_continuous_scale="RdBu",
    range_color=[-max_difference, max_difference],
    labels={
        "Difference from global average": "Difference in happiness score",
        "Region": "",
    },
    hover_data={"Regional average": ":.2f", "Difference from global average": ":+.2f"},
    title="Which Regions Are Above or Below the Global Happiness Average?",
    template="plotly_white",
)
fig_region.add_vline(
    x=0,
    line_dash="dash",
    line_color="black",
    line_width=2,
)
fig_region.add_annotation(
    x=0,
    y=1.08,
    xref="x",
    yref="paper",
    text="0 = global average",
    showarrow=False,
    font=dict(size=11, color="black"),
    bgcolor="white",
)
fig_region.update_layout(
    coloraxis_colorbar=dict(title="Difference<br>from global"),
    margin=dict(l=10, r=20, t=90, b=30),
)
st.plotly_chart(fig_region, use_container_width=True)

st.caption(
    "Colour midpoint: 0.00, meaning the global average happiness score. "
    "Positive values are above the global average; negative values are below it."
)

with st.expander("View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.divider()
st.caption("Built with Streamlit and Plotly")
