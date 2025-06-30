import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import beta
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import arviz as az

st.set_page_config(page_title="Bayesian A/B Testing", layout="wide")
st.title("🧪 Bayesian A/B Testing (Bayes > p-values)")

# Sidebar Inputs
with st.sidebar:
    st.header("🔧 Experiment Settings")

    data_mode = st.radio("Choose data source", ["Sample data", "Upload CSV", "Manual entry"])

    if data_mode == "Sample data":
        df = pd.DataFrame({
            'group': ['control', 'variant'],
            'conversions': [300, 320],
            'trials': [1000, 1000]
        })

    elif data_mode == "Upload CSV":
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
        else:
            st.stop()

    elif data_mode == "Manual entry":
        a_conversions = st.number_input("Control conversions", min_value=0, value=300)
        a_trials = st.number_input("Control trials", min_value=1, value=1000)
        b_conversions = st.number_input("Variant conversions", min_value=0, value=320)
        b_trials = st.number_input("Variant trials", min_value=1, value=1000)
        df = pd.DataFrame({
            'group': ['control', 'variant'],
            'conversions': [a_conversions, b_conversions],
            'trials': [a_trials, b_trials]
        })

    st.markdown("###  Data Requirements")
    st.markdown(
        "- CSV must contain columns: `group`, `conversions`, `trials`\n"
        "- Example:\n"
        "```csv\n"
        "group,conversions,trials\n"
        "control,130,1000\n"
        "variant,140,1020\n"
        "```"
    )

    # Show group mapping selectors
    unique_groups = df['group'].dropna().unique()
    if len(unique_groups) != 2:
        st.error(f"Expected exactly 2 groups, found: {unique_groups}")
        st.stop()

    st.markdown("### Map Groups to A/B")

    default_a = 'control' if 'control' in unique_groups else unique_groups[0]
    default_b = 'variant' if 'variant' in unique_groups else [g for g in unique_groups if g != default_a][0]

    group_a_label = st.selectbox("Assign to A", unique_groups, index=list(unique_groups).index(default_a))
    group_b_label = st.selectbox("Assign to B", [g for g in unique_groups if g != group_a_label])

    if group_a_label == group_b_label:
        st.error("Groups A and B must be distinct.")
        st.stop()

    label_map = {group_a_label: 'A', group_b_label: 'B'}
    df['group'] = df['group'].replace(label_map)
    group_label_display = {'A': group_a_label, 'B': group_b_label}

    st.markdown(f"Mapped: **{group_a_label} → A**, **{group_b_label} → B**")

    st.divider()
    st.header("Priors & Analysis Settings")

    alpha_prior = st.slider("Alpha prior", 0.5, 10.0, 1.0)
    beta_prior = st.slider("Beta prior", 0.5, 10.0, 1.0)

    hdi_level = st.slider("HDI Level", 0.80, 0.99, 0.95)

    with st.expander("📏 Advanced: ROPE Settings"):
        st.markdown(
            "The **Region of Practical Equivalence (ROPE)** defines a range of values around 0 that are considered "
            "**practically negligible**. If the posterior distribution of the difference (B − A) lies entirely within "
            "this range, it suggests there's no meaningful difference between A and B.\n\n"
            "**Decision rule**:\n"
            "- If most of the posterior is **outside** the ROPE: there is likely a meaningful effect.\n"
            "- If most of the posterior is **inside** the ROPE: the effect is likely negligible.\n"
            "- If the posterior **straddles** the ROPE: the result is inconclusive.\n\n"
            "Use ROPE to incorporate your practical or business context into the decision — not just statistical significance."
        )

        use_rope = st.checkbox(
            "Use ROPE?",
            help="Enable to define a range of values around zero where differences are considered practically equivalent."
        )

        if use_rope:
            rope_min = st.number_input("ROPE min", value=-0.01, format="%.4f")
            rope_max = st.number_input("ROPE max", value=0.01, format="%.4f")
            rope = (rope_min, rope_max)
        else:
            rope = None

    update = st.button("Update Posterior")

# Data validation and mapping already done above

# Preview Data
with st.expander("Data Used in Analysis", expanded=False):
    #st.write("Data summary used for this analysis:")
    #st.dataframe(df)
    rates = df.copy()
    rates['conversion rate'] = (rates['conversions'] / rates['trials']).round(4)
    #st.markdown("**Per-group Conversion Summary:**")
    st.dataframe(rates)

# Posterior computation and plotting
if update or data_mode in ["Sample data", "Manual entry"]:
    grouped = df.groupby('group').agg(dict(conversions='sum', trials='sum'))
    summary = grouped.to_dict()
    if 'A' not in summary['conversions'] or 'B' not in summary['conversions']:
        st.error("Mapped group labels to A and B are not present in the data.")
        st.stop()

    samples = {}
    for group in ['A', 'B']:
        conv = summary['conversions'][group]
        trials = summary['trials'][group]
        samples[group] = beta(alpha_prior + conv, beta_prior + trials - conv).rvs(100_000)

    samples['delta'] = samples['B'] - samples['A']
    samples['B > A'] = (samples['delta'] > 0).astype(int)
    idata = az.from_dict(posterior=samples)
    prob_b_better = np.mean(samples['delta'] > 0)

    tab1, tab2, tab3 = st.tabs(["📈 Posterior Distributions", "📋 Summary Table", "✅ Decision Metrics"])

    with tab1:
        fontdict={'color': 'white', 'size': 16}
        fig = plt.figure(figsize=(12, 8), facecolor='black')
        spec = gridspec.GridSpec(nrows=2, ncols=2, figure=fig, hspace=0.3, wspace=0.1)

        ax1 = fig.add_subplot(spec[0, 0])
        az.plot_posterior(idata, var_names=["A"], hdi_prob=hdi_level, ax=ax1)
        ax1.set_title(f"Posterior of p(A) ({group_label_display['A']})", fontdict=fontdict)
        ax1.set_facecolor("#f8f9fa")

        ax2 = fig.add_subplot(spec[0, 1])
        az.plot_posterior(idata, var_names=["B"], hdi_prob=hdi_level, ax=ax2)
        ax2.set_title(f"Posterior of p(B) ({group_label_display['B']})", fontdict=fontdict)
        ax2.set_facecolor("#f8f9fa")

        ax3 = fig.add_subplot(spec[1, 0])
        az.plot_posterior(idata, var_names=["delta"], hdi_prob=hdi_level, rope=rope if use_rope else None, ax=ax3, ref_val=0)
        ax3.set_title("Posterior of p(B − A)", fontdict=fontdict)
        ax3.set_facecolor("#f8f9fa")

        fig.add_subplot(spec[1, 1]).axis('off')

        st.pyplot(fig)

    with tab2:
        st.dataframe(az.summary(idata, hdi_prob=hdi_level, round_to=4))

    with tab3:
        st.metric(label="P(B > A)", value=f"{prob_b_better:.3f}")
        if use_rope:
            rope_pct = np.mean((samples['delta'] > rope_min) & (samples['delta'] < rope_max))
            st.metric(label="P(delta ∈ ROPE)", value=f"{rope_pct:.3f}")
