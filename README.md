# Bayesian A/B Testing Web App

A fully interactive web application for Bayesian A/B testing, built with [Streamlit](https://streamlit.io/) and deployed on AWS EC2. Users can analyze A/B test results using a Bayesian framework, upload custom CSV data or use built-in sample data, visualize posterior distributions, and view summary statistics and decision metrics.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Interface Overview](#interface-overview)
- [Built-in Dataset](#built-in-dataset)
- [Uploading Custom Data](#uploading-custom-data)
- [Statistical Model](#statistical-model)
- [Deployment on AWS EC2](#deployment-on-aws-ec2)
- [Development Notes](#development-notes)
- [Planned Features](#planned-features)
- [License](#license)

---

## Features

- ✅ Bayesian inference for binary outcome A/B tests  
- ✅ Adjustable Beta prior parameters (α and β)  
- ✅ Support for both built-in and user-uploaded CSV files  
- ✅ Posterior probability and decision summaries  
- ✅ ArviZ plots from sampled posterior distributions  
- ✅ Optional ROPE interval and HDI-level control  
- ✅ Streamlit app layout using tabs and responsive grid  
- ✅ Deployed on AWS EC2 with HTTPS access (no Docker required)  
- ✅ Lightweight — no PyMC or MCMC backend required  

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/bayesian-ab-testing-app.git
cd bayesian-ab-testing-app
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

To launch the Streamlit app locally:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Interface Overview

- **Dataset Loader**  
  Choose between a sample dataset hosted on S3, uploading a CSV, or manual entry.  
  Expected CSV format: `group`, `conversions`, `trials`.

- **Bayesian Posterior Calculation**  
  Uses the conjugate Beta posterior for binomial likelihoods.  
  Posterior samples are drawn using `scipy.stats.beta.rvs`.

- **Visualization & Output**  
  - Posterior distributions for each group (ArviZ plots)  
  - Posterior of the delta (B − A)  
  - Decision metric: P(B > A)  
  - Optional ROPE analysis  
  - Adjustable HDI level

---

## Built-in Dataset

The built-in dataset includes synthetic A/B test data:

```csv
group,conversions,trials
A,300,1000
B,320,1000
```

This is stored in a public S3 bucket and useful for quick demos.

---

## Uploading Custom Data

You may upload a CSV file with the following required columns:

- `group`: string or category label (e.g., A, B)
- `conversions`: number of observed successes (integer)
- `trials`: total number of trials (integer)

The app automatically validates the columns and runs the Bayesian analysis.

---

## Statistical Model

This app uses a **Beta-Binomial conjugate model**, computed analytically:

- **Prior**: `Beta(α, β)` — set via sidebar sliders (default `α=1`, `β=1`)  
- **Likelihood**: Binomial for observed conversions  
- **Posterior**: `Beta(α + conversions, β + trials − conversions)`  
- **Sampling**: 100,000 posterior draws via `scipy.stats.beta.rvs`  
- **Delta Distribution**: Difference of sampled posteriors, `p_B − p_A`  
- **Inference**:  
  - P(B > A): proportion of draws where `p_B > p_A`  
  - ROPE (optional): proportion of draws where `delta` ∈ [min, max]  
  - ArviZ summaries and HDI intervals

No MCMC, PyMC, or sampling infrastructure is required — it is fast and interpretable.

---

## Deployment on AWS EC2

The app is deployed on a t2.micro EC2 instance with:

- Ubuntu 22.04  
- Python 3.10  
- Streamlit and dependencies installed via `venv`  
- Nginx reverse proxy (optional)  
- UFW firewall (ports 22 and 443 allowed)  
- No Docker or container orchestration used

To deploy:

1. SSH into your EC2 instance  
2. Clone the repo and set up the environment  
3. Start the app with `streamlit run app.py --server.port 443`  
4. Use `nohup` or `tmux` to keep the app running persistently  
5. (Optional) Configure HTTPS with Nginx or Cloudflare

---

## Development Notes

- Sampling is vectorized using `scipy.stats.beta.rvs`  
- All visuals rendered via ArviZ using `az.from_dict()`  
- ROPE support and HDI levels are configurable  
- Layout uses `st.tabs()` and `st.columns()` for clarity  
- App runs efficiently even on low-resource instances

---

## Planned Features

- Support for more than two groups (A/B/C tests)  
- Prior sensitivity visualization  
- CSV export of sampled posteriors  
- Support for click-through rate or other metrics  
- Authentication or API keys for access control

---

## License

This project is open source and available under the [MIT License](LICENSE).
