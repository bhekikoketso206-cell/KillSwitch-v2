import streamlit as st
import requests

st.set_page_config(
    page_title="AI Safety Monitor",
    page_icon="🛡️",
    layout="centered",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
  }

  .stApp {
    background-color: #0d0f14;
    color: #e2e8f0;
  }

  .header-block {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid #1e2330;
    margin-bottom: 2rem;
  }
  .header-block h1 {
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 2rem;
    letter-spacing: -0.03em;
    color: #f1f5f9;
    margin: 0 0 0.25rem;
  }
  .header-block p {
    color: #64748b;
    font-size: 0.85rem;
    font-weight: 300;
    margin: 0;
  }
  .shield-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    display: block;
  }

  .input-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
  }

  .stTextArea textarea {
    background-color: #141720 !important;
    border: 1px solid #1e2a3a !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.875rem !important;
    caret-color: #38bdf8;
  }

  .stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #6366f1);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 2.2rem;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    width: 100%;
    cursor: pointer;
  }

  .result-card {
    border-radius: 12px;
    padding: 1.6rem 1.8rem;
    margin-top: 1.8rem;
    border: 1px solid transparent;
  }
  .result-allow {
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.35);
  }
  .result-block {
    background: rgba(239, 68, 68, 0.08);
    border-color: rgba(239, 68, 68, 0.35);
  }

  .verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: 999px;
    padding: 0.35rem 1rem;
    font-weight: 700;
    font-size: 0.9rem;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
  }
  .badge-allow {
    background: rgba(16, 185, 129, 0.18);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.4);
  }
  .badge-block {
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.4);
  }

  .field-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  .field-item {
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
    padding: 0.8rem 1rem;
  }
  .field-key {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.25rem;
  }
  .field-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.92rem;
    font-weight: 600;
    color: #e2e8f0;
  }

  .score-bar-container {
    background: rgba(255,255,255,0.06);
    border-radius: 999px;
    height: 6px;
    width: 100%;
    margin-top: 0.4rem;
    overflow: hidden;
  }

  .field-item-full {
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
    padding: 0.8rem 1rem;
  }

  .error-card {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #f87171;
    font-size: 0.85rem;
    margin-top: 1.2rem;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-block">
  <span class="shield-icon">🛡️</span>
  <h1>AI Safety Monitor</h1>
  <p>Real-time prompt risk analysis · Powered by KillSwitch v2</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="input-label">Prompt to evaluate</div>', unsafe_allow_html=True)
user_prompt = st.text_area(
    label="",
    placeholder="Enter any prompt to analyse its risk level…",
    height=130,
    label_visibility="collapsed",
)

analyze_clicked = st.button("⚡  Analyse Prompt", use_container_width=True)

API_BASE = "https://bheki21-killswitch-v2.hf.space/v1/decide?input="

if analyze_clicked:
    if not user_prompt.strip():
        st.markdown('<div class="error-card">⚠️ Please enter a prompt before analysing.</div>', unsafe_allow_html=True)
    else:
        with st.spinner("Contacting safety API…"):
            try:
                url = API_BASE + requests.utils.quote(user_prompt.strip())
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                action = str(data.get("action", "UNKNOWN")).upper()
                risk_score = data.get("risk_score", "—")
                risk_level = data.get("risk_level", "—")
                category = data.get("category", "—")
                reason = data.get("reason", "—")

                is_allow = action == "ALLOW"
                card_cls = "result-allow" if is_allow else "result-block"
                badge_cls = "badge-allow" if is_allow else "badge-block"
                icon = "✅" if is_allow else "🚫"

                try:
                    score_val = float(risk_score)
                    bar_color = f"hsl({max(0, int((1 - score_val) * 120))}, 80%, 55%)"
                    bar_width = f"{int(score_val * 100)}%"
                    score_display = f"{score_val:.2f}"
                except (TypeError, ValueError):
                    bar_width = "0%"
                    bar_color = "#475569"
                    score_display = str(risk_score)

                st.markdown(f"""
                <div class="result-card {card_cls}">
                  <div class="verdict-badge {badge_cls}">
                    {icon} &nbsp; {action}
                  </div>
                  <div class="field-grid">
                    <div class="field-item">
                      <div class="field-key">Risk Score</div>
                      <div class="field-value">{score_display}</div>
                      <div class="score-bar-container">
                        <div style="height:100%; width:{bar_width}; background:{bar_color}; border-radius:999px;"></div>
                      </div>
                    </div>
                    <div class="field-item">
                      <div class="field-key">Risk Level</div>
                      <div class="field-value">{risk_level}</div>
                    </div>
                    <div class="field-item">
                      <div class="field-key">Action</div>
                      <div class="field-value">{action}</div>
                    </div>
                    <div class="field-item">
                      <div class="field-key">Category</div>
                      <div class="field-value">{category}</div>
                    </div>
                  </div>
                  <div class="field-item-full">
                    <div class="field-key">Reason</div>
                    <div class="field-value">{reason}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.markdown(f'<div class="error-card">❌ Error: {e}</div>', unsafe_allow_html=True)
