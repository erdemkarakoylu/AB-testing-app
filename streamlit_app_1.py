import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import beta
import matplotlib.pyplot as pp
import arviz as az

st.set_page_config(page_title="Bayesian A/B Testing", layout="wide")
st.title("🧪 Bayesian A/B Testing (Bayes > p-values)")

# Sidebar Inputs
with st.sidebar:
    st.header("🔧 Experiment Settings")

    data_mode = st.radio("Choose data source", ["Sample data", "Upload CSV", "Manual entry"])

    if data_mode == "Sample data":
        df = pd.DataFrame({
            'group': ['A', 'B'],
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
        a_conversions = st.number_input("A conversions", min_value=0, value=300)
        a_trials = st.number_input("A trials", min_value=1, value=1000)
        b_conversions = st.number_input("B conversions", min_value=0, value=320)
        b_trials = st.number_input("B trials", min_value=1, value=1000)
        df = pd.DataFrame({
            'group': ['A', 'B'],
            'conversions': [a_conversions, b_conversions],
            'trials': [a_trials, b_trials]
        })

    st.divider()
    st.header("📌 Priors & Analysis Settings")

    alpha_prior = st.slider("Alpha prior", 0.5, 10.0, 1.0)
    beta_prior = st.slider("Beta prior", 0.5, 10.0, 1.0)

    hdi_level = st.slider("HDI Level", 0.80, 0.99, 0.95)

    use_rope = st.checkbox("Use ROPE?")
    if use_rope:
        rope_min = st.number_input("ROPE min", value=-0.01, format="%.4f")
        rope_max = st.number_input("ROPE max", value=0.01, format="%.4f")
        rope = (rope_min, rope_max)
    else:
        rope = None

    update = st.button("Update Posterior")

# Ensure valid input
required_cols = {'group', 'conversions', 'trials'}
if not required_cols.issubset(df.columns):
    st.error(f"Data must have columns: {required_cols}")
    st.stop()

# Triggered posterior update
if update or data_mode in ["Sample data", "Manual entry"]:
    summary = df.set_index('group').to_dict()
    samples = {}
    for group in ['A', 'B']:
        conv = summary['conversions'][group]
        trials = summary['trials'][group]
        samples[group] = beta(alpha_prior + conv, beta_prior + trials - conv).rvs(100_000)

    samples['delta'] = samples['B'] - samples['A']
    idata = az.from_dict(posterior=samples)
    prob_b_better = np.mean(samples['delta'] > 0)

    # Main area: Visuals & Stats
    tab1, tab2, tab3 = st.tabs(["📈 Posterior Plots", "📋 Summary Table", "✅ Decision Metric"])

    with tab1:
        fig, axs = pp.subplots(2, 2, figsize=(8, 6))
        #fig.subplots_adjust(hspace=0.4)

        az.plot_posterior(idata, var_names=["A"], hdi_prob=hdi_level, ax=axs[0, 0])
        axs[0, 0].set_title("Posterior of p(A)")

        az.plot_posterior(idata, var_names=["B"], hdi_prob=hdi_level, ax=axs[0, 1])
        axs[0, 1].set_title("Posterior of p(B)")

        az.plot_posterior(idata, var_names=["delta"], hdi_prob=hdi_level, rope=rope if use_rope else None, ax=axs[1, 0])
        axs[1, 0].set_title("Posterior of p(B − A)")

        fig.delaxes(axs[1, 1])
        fig.tight_layout()
        st.pyplot(fig)

    with tab2:
        st.subheader("ArviZ Posterior Summary")
        st.dataframe(az.summary(idata, hdi_prob=hdi_level, round_to=4))

    with tab3:
        st.metric(label="P(B > A)", value=f"{prob_b_better:.3f}")
        if use_rope:
            rope_pct = np.mean((samples['delta'] > rope_min) & (samples['delta'] < rope_max))
            st.metric(label="P(delta ∈ ROPE)", value=f"{rope_pct:.3f}")

