
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import streamlit as st
from pathlib import Path

# ---- App/Theming ----
st.set_page_config(
    page_title="Round Pakenham • Calorie Calculator",
    page_icon="🥊",
    layout="centered",
)

# Custom CSS to reinforce branding
st.markdown(
    """
    <style>
      /* Layout tweaks */
      .block-container { padding-top: 2rem; max-width: 900px; }
      /* Headings */
      h1, h2, h3 { letter-spacing: 0.2px; }
      /* Accent classes */
      .brand-title { font-weight: 900; font-size: 2rem; }
      .brand-red { color: #E4002B; } /* 9Round-like red */
      .badge { display: inline-block; font-weight: 700; padding: 2px 8px; border-radius: 999px;
               background: #E4002B; color: #fff; font-size: 0.85rem; vertical-align: middle; }
      /* Cards */
      .kpi { border: 1px solid #2a2a2a; border-radius: 12px; padding: 14px 16px; background: #111; }
      .kpi .value { font-size: 1.6rem; font-weight: 800; }
      .kpi .label { color: #cfd6de; font-size: 0.95rem; }
      /* Footer */
      .footer { color: #cfd6de; font-size: 0.9rem; margin-top: 1.5rem; }
      /* Button emphasis */
      .stButton>button { font-weight: 800; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- Constants/Types ----
ActivityKey = Literal["sedentary", "light", "moderate", "very", "extra"]
BodyTypeKey = Literal["ectomorph", "mesomorph", "endomorph"]
GoalKey = Literal["lose", "maintain", "gain"]
SexKey = Literal["male", "female"]
UnitsKey = Literal["metric", "imperial"]

ACTIVITY_MULTIPLIER: dict[ActivityKey, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very": 1.725,
    "extra": 1.9,
}

BODYTYPE_MULTIPLIER: dict[BodyTypeKey, float] = {
    "ectomorph": 1.05,    # gentle nudge
    "mesomorph": 1.00,
    "endomorph": 0.95,
}

@dataclass
class CalcResult:
    bmr: float
    tdee: float
    calories: float
    activity_multiplier: float
    bodytype_multiplier: float
    goal_pct: float

# ---- Calculators ----
def mifflin_st_jeor(sex: SexKey, age: float, weight_kg: float, height_cm: float) -> float:
    if sex == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def convert_units(units: UnitsKey, weight: float, height: float) -> tuple[float, float]:
    if units == "imperial":
        return weight * 0.453592, height * 2.54  # lb->kg, in->cm
    return weight, height

def calculate_intake(
    *, sex: SexKey, age: float, weight: float, height: float, units: UnitsKey,
    activity: ActivityKey, body_type: BodyTypeKey, goal: GoalKey, intensity_pct: float
) -> CalcResult:
    w_kg, h_cm = convert_units(units, weight, height)
    bmr = mifflin_st_jeor(sex, age, w_kg, h_cm)
    activity_x = ACTIVITY_MULTIPLIER[activity]
    bodytype_x = BODYTYPE_MULTIPLIER[body_type]
    tdee = bmr * activity_x * bodytype_x

    if goal == "lose":
        pct = -abs(intensity_pct)
    elif goal == "gain":
        pct = abs(intensity_pct)
    else:
        pct = 0.0

    calories = tdee * (1.0 + pct)

    return CalcResult(
        bmr=bmr,
        tdee=tdee,
        calories=calories,
        activity_multiplier=activity_x,
        bodytype_multiplier=bodytype_x,
        goal_pct=pct,
    )

# ---- Header / Branding ----
logo_path = Path("assets/9round_logo.png")
left, right = st.columns([1, 3])
with left:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown('<div class="badge">ROUND</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="brand-title">Round <span class="brand-red">Pakenham</span> • Calorie Calculator</div>', unsafe_allow_html=True)
    st.caption("Estimate your daily calories using Mifflin–St Jeor × activity × body type, aligned to your goal.")

# ---- Form ----
with st.form("calc_form"):
    c1, c2 = st.columns(2)
    with c1:
        sex = st.selectbox("Sex", ["male", "female"], index=0)
        age = st.number_input("Age (years)", min_value=10, max_value=120, value=30, step=1)
        units = st.selectbox("Units", ["metric", "imperial"], index=0)
        weight = st.number_input("Weight (kg or lb)", min_value=20.0, max_value=600.0, value=70.0, step=0.1)
        height = st.number_input("Height (cm or in)", min_value=80.0, max_value=300.0, value=175.0, step=0.1)
    with c2:
        activity = st.selectbox(
            "Activity level",
            ["sedentary", "light", "moderate", "very", "extra"],
            index=2,
            help="Sedentary=little/no exercise; Light=1-3 days/wk; Moderate=3-5; Very=6-7; Extra=hard training/physical job.",
        )
        body_type = st.selectbox("Body type", ["mesomorph", "ectomorph", "endomorph"], index=0)
        goal = st.selectbox("Goal", ["lose", "maintain", "gain"], index=1)
        intensity_pct = st.slider("Goal intensity (%)", 5, 25, 15)

    submitted = st.form_submit_button("Calculate")

# ---- Results ----
if submitted:
    res = calculate_intake(
        sex=sex, age=float(age), weight=float(weight), height=float(height), units=units, activity=activity,
        body_type=body_type, goal=goal, intensity_pct=float(intensity_pct) / 100.0
    )

    k1, k2 = st.columns(2)
    with k1:
        st.markdown('<div class="kpi"><div class="value">{:,.0f} kcal/day</div><div class="label">Suggested intake</div></div>'.format(res.calories), unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi"><div class="value">{:,.0f} kcal/day</div><div class="label">Estimated TDEE</div></div>'.format(res.tdee), unsafe_allow_html=True)

    with st.expander("Method & breakdown"):
        st.write(
            f"**BMR:** {res.bmr:.0f} kcal  \n"
            f"**Activity ×:** {res.activity_multiplier}  \n"
            f"**Body type adj:** {(res.bodytype_multiplier - 1.0) * 100:.1f}%  \n"
            f"**Goal adj:** {res.goal_pct * 100:.0f}%"
        )
        st.caption(
            "Method: Mifflin–St Jeor for BMR. Activity multipliers: 1.2 / 1.375 / 1.55 / 1.725 / 1.9. "
            "Body type nudge: ecto +5%, meso 0%, endo −5%. Goal: ±(5–25%). These are estimates only."
        )
else:
    st.info("Enter your details and press **Calculate** to see your results.")

# ---- Footer ----
st.markdown('<div class="footer">© Round Pakenham. For educational purposes and general guidance — not medical advice.</div>', unsafe_allow_html=True)
