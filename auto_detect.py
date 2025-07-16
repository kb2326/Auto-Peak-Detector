# save as app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def compute_peak_auc(df):
    df.columns = ['Time', 'ms', 'intensity']
    df['seconds'] = df['ms'] / 1000
    df['intensity'] = pd.to_numeric(df['intensity'], errors='coerce')
    df.dropna(inplace=True)
    df = df.sort_values('seconds')

    # Step 1: Estimate baseline from first 10 points
    baseline = df['intensity'][:10].mean()
    threshold = baseline * 1.2

    # Step 2: Detect start of peak
    start_candidates = df[df['intensity'] > threshold]
    if start_candidates.empty:
        return None, None, None, "No peak detected above baseline threshold."

    start_idx = start_candidates.index[0]

    # Step 3: Detect end of peak
    post_peak = df[df.index > start_idx]
    end_candidates = post_peak[post_peak['intensity'] < baseline * 1.05]
    if end_candidates.empty:
        return None, None, None, "Peak doesn't return to baseline. Cannot detect end."

    end_idx = end_candidates.index[-1]

    # Step 4: Slice and calculate AUC
    df_peak = df.loc[start_idx:end_idx]
    auc = np.trapz(df_peak['intensity'], x=df_peak['seconds'])

    return auc, df, df_peak, None

# === STREAMLIT UI ===

st.set_page_config(page_title="PFAS Peak AUC Calculator", layout="centered")
st.title("📈 PFAS Destruction - Auto Peak AUC Calculator")

uploaded_file = st.file_uploader("Upload Excel File (.xlsx) with PFAS RGA data", type="xlsx")

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, skiprows=20)  # skip header metadata
        auc, df_full, df_peak, error = compute_peak_auc(df_raw)

        if error:
            st.error(error)
        else:
            st.success(f"✅ AUC (Detected Peak Only): {auc:.4e} unit·s")

            # Plot
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use("Agg")

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(df_full['seconds'], df_full['intensity'], label="Full Curve", alpha=0.5)
            ax.plot(df_peak['seconds'], df_peak['intensity'], label="Detected Peak", color='red')
            ax.fill_between(df_peak['seconds'], df_peak['intensity'], alpha=0.3)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Intensity")
            ax.set_title("Auto-Detected Peak Area")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Failed to process the file: {e}")
