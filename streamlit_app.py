
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Tuple
import streamlit as st
from pathlib import Path
from io import BytesIO
from datetime import date
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

st.set_page_config(page_title="Round Pakenham • Calorie Calculator", page_icon="🥊", layout="centered")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; max-width: 980px; }
      .brand-title { font-weight: 900; font-size: 2.2rem; letter-spacing: 0.2px; }
      .brand-red { color: #E4002B; }
      .kpi { border: 1px solid #2a2a2a; border-radius: 14px; padding: 16px 18px; background: #0B0B0B; }
      .kpi .value { font-size: 1.8rem; font-weight: 900; color: #FFFFFF; }
      .kpi .label { color: #D7DBE0; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.6px; }
      .stButton>button { font-weight: 900; border-radius: 12px; text-transform: uppercase; }
      .footer { color: #D7DBE0; font-size: 0.9rem; margin-top: 1.25rem; }
      label, .stSelectbox label, .stNumberInput label, .stSlider label, .stTextInput label { text-transform: capitalize; }
    </style>
    """,
    unsafe_allow_html=True
)

ActivityKey = Literal["Sedentary", "Light", "Moderate", "Very", "Extra"]
BodyTypeKey = Literal["Ectomorph", "Mesomorph", "Endomorph"]
GoalKey = Literal["Maintain", "Lose Weight", "Gain Weight"]
SexKey = Literal["Male", "Female"]
UnitsKey = Literal["Metric", "Imperial"]

ACTIVITY_MULTIPLIER = {"Sedentary": 1.2, "Light": 1.375, "Moderate": 1.55, "Very": 1.725, "Extra": 1.9}
BODYTYPE_MULTIPLIER = {"Ectomorph": 1.05, "Mesomorph": 1.00, "Endomorph": 0.95}
KCAL_PER_KG = 7700.0

@dataclass
class CalcResult:
    bmr: float
    tdee: float
    calories: float
    activity_multiplier: float
    bodytype_multiplier: float
    daily_delta_kcal: float
    target_change_mass: float
    target_weeks: int
    protein_g: float
    fats_g: float
    carbs_g: float

def mifflin_st_jeor(sex: SexKey, age: float, weight_kg: float, height_cm: float) -> float:
    if sex == "Male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def convert_to_metric(units: UnitsKey, weight: float, height: float) -> Tuple[float, float]:
    if units == "Imperial":
        return weight * 0.453592, height * 2.54
    return weight, height

def convert_mass_to_kg(units: UnitsKey, mass: float) -> float:
    if units == "Imperial":
        return mass * 0.453592
    return mass

def macro_split(total_cal: float, weight_kg: float, protein_g_per_kg: float = 2.0, fat_percent: float = 0.25):
    protein_g = protein_g_per_kg * weight_kg
    protein_kcal = protein_g * 4.0
    fat_kcal = total_cal * fat_percent
    fats_g = fat_kcal / 9.0
    carbs_kcal = max(total_cal - protein_kcal - fat_kcal, 0)
    carbs_g = carbs_kcal / 4.0
    return protein_g, fats_g, carbs_g

def calculate_intake(sex, age, weight, height, units, activity, body_type, goal, target_change_mass, target_weeks, protein_g_per_kg, fat_percent):
    w_kg, h_cm = convert_to_metric(units, weight, height)
    target_kg = convert_mass_to_kg(units, abs(target_change_mass))
    bmr = mifflin_st_jeor(sex, age, w_kg, h_cm)
    tdee = bmr * ACTIVITY_MULTIPLIER[activity] * BODYTYPE_MULTIPLIER[body_type]
    daily_delta = (target_kg * KCAL_PER_KG) / (target_weeks * 7.0) if target_weeks > 0 else 0.0
    if goal == "Lose Weight":
        daily_delta = -daily_delta
    elif goal == "Maintain":
        daily_delta = 0.0
    calories = tdee + daily_delta
    protein_g, fats_g, carbs_g = macro_split(calories, w_kg, protein_g_per_kg, fat_percent)
    return CalcResult(bmr, tdee, calories, ACTIVITY_MULTIPLIER[activity], BODYTYPE_MULTIPLIER[body_type], daily_delta, target_kg, target_weeks, protein_g, fats_g, carbs_g)

logo_path = Path("assets/9round_logo_white.png")
left, right = st.columns([1, 3])
with left:
    st.markdown("<div style='background:#000;padding:8px;border-radius:10px;'>", unsafe_allow_html=True)
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown("<div style='color:#fff;text-align:center;font-weight:900;'>9ROUND</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with right:
    st.markdown("<div class='brand-title'>Round <span class='brand-red'>Pakenham</span> • Calorie Calculator</div>", unsafe_allow_html=True)
    st.caption("Estimate Your Daily Calories Using Mifflin–St Jeor × Activity × Body Type, Aligned To Your Goal.")

with st.expander("Body Type Descriptions", expanded=False):
    st.markdown(
        "- **Ectomorph** — Naturally Slim; Finds It Harder To Gain Weight/Muscle; Often Benefits From A Slightly Higher Intake.\n"
        "- **Mesomorph** — Naturally Athletic Build; Typically Maintains More Easily.\n"
        "- **Endomorph** — Stores Body Fat More Readily; A Slightly Lower Intake May Help."
    )

with st.form("Calc Form"):
    c1, c2 = st.columns(2)
    with c1:
        client_name = st.text_input("Client Name", value="")
        sex = st.selectbox("Sex", ["Male", "Female"], index=0)
        age = st.number_input("Age (Years)", min_value=10, max_value=120, value=30, step=1)
        units = st.selectbox("Units", ["Metric", "Imperial"], index=0)
        weight = st.number_input("Weight (Kg Or Lb)", min_value=20.0, max_value=600.0, value=70.0, step=0.1)
        height = st.number_input("Height (Cm Or In)", min_value=80.0, max_value=300.0, value=175.0, step=0.1)
        activity = st.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Very", "Extra"], index=2)
    with c2:
        body_type = st.selectbox("Body Type", ["Mesomorph", "Ectomorph", "Endomorph"], index=0)
        goal = st.selectbox("Goal", ["Maintain", "Lose Weight", "Gain Weight"], index=0)
        target_change, weeks = (0.0, 0)
        if goal != "Maintain":
            target_change = st.number_input("Target Weight Change (Kg Or Lb)", min_value=0.1, max_value=100.0, value=5.0, step=0.1)
            weeks = st.number_input("Timeframe (Weeks)", min_value=1, max_value=104, value=8, step=1)
        st.markdown("---")
        st.markdown("**Macro Preferences**")
        protein_g_per_kg = st.slider("Protein (g/Kg)", 1.2, 2.6, 2.0, 0.1)
        fat_percent = st.slider("Fats (% Of Calories)", 0.20, 0.35, 0.25, 0.01)
    submitted = st.form_submit_button("Calculate")

if submitted:
    res = calculate_intake(sex, age, weight, height, units, activity, body_type, goal, target_change, weeks, protein_g_per_kg, fat_percent)
    st.markdown(f"<h4 style='color:#fff;'>Suggested Intake: {res.calories:.0f} kcal/day</h4>", unsafe_allow_html=True)
    st.write(f"**Protein:** {res.protein_g:.0f} g  •  **Fats:** {res.fats_g:.0f} g  •  **Carbs:** {res.carbs_g:.0f} g")

    def build_report():
        doc = Document()
        header = doc.sections[0].header.paragraphs[0]
        run = header.add_run()
        banner = Path("assets/9round_banner_black.png")
        if banner.exists():
            run.add_picture(str(banner), width=Inches(6.5))
        doc.add_heading("Calorie & Macro Plan", level=1)
        doc.add_paragraph(f"Client: {client_name or '(Not Provided)'}    Date: {date.today().strftime('%d/%m/%Y')}")
        doc.add_heading("Summary", level=2)
        doc.add_paragraph(f"Estimated BMR: {res.bmr:.0f} kcal/day")
        doc.add_paragraph(f"Estimated TDEE: {res.tdee:.0f} kcal/day")
        doc.add_paragraph(f"Suggested Intake: {res.calories:.0f} kcal/day")
        doc.add_heading("Goal", level=2)
        doc.add_paragraph(f"Objective: {goal}")
        if goal != "Maintain":
            doc.add_paragraph(f"Target Weight Change: {target_change} {'lb' if units=='Imperial' else 'kg'}")
            doc.add_paragraph(f"Timeframe: {weeks} weeks")
            doc.add_paragraph(f"Implied Daily Surplus/Deficit: {res.daily_delta_kcal:+.0f} kcal/day")
        doc.add_heading("Macro Targets", level=2)
        doc.add_paragraph(f"Protein: {res.protein_g:.0f} g/day")
        doc.add_paragraph(f"Fats: {res.fats_g:.0f} g/day")
        doc.add_paragraph(f"Carbs: {res.carbs_g:.0f} g/day")
        doc.add_heading("Notes", level=2)
        doc.add_paragraph("These are estimates only and not medical advice. Adjust weekly based on progress.")
        bio = BytesIO()
        doc.save(bio)
        bio.seek(0)
        return bio

    st.download_button("Download Report (.docx)", data=build_report(), file_name=f"Round_Pakenham_Report_{date.today()}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
else:
    st.info("Enter Your Details And Press **Calculate** To See Your Results.")
