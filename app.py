import math
import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

# ============================================================
# PAGE SETUP
# ============================================================
st.set_page_config(
    page_title="Nurse Roster Optimizer V4",
    page_icon="🏥",
    layout="wide"
)

st.markdown(
    """
    <style>
    h1, h2, h3 { color: #234E70; }
    [data-testid="stCheckbox"] div[data-baseweb="checkbox"] > div:first-child {
        background-color: #7BB7D9 !important;
        border-color: #7BB7D9 !important;
    }
    [data-testid="stCheckbox"] div[data-baseweb="checkbox"] svg {
        fill: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHIFTS = ["Morning", "Evening", "Night"]
TARGET_SHIFTS_PER_TYPE = 2
MAX_NIGHT_SHIFTS_PER_WEEK = 2

if "roster" not in st.session_state:
    st.session_state["roster"] = None
if "roster_departments" not in st.session_state:
    st.session_state["roster_departments"] = {}

# ============================================================
# OPTIMIZER
# ============================================================


def generate_roster(nurses, availability_df, nurse_departments, department_staffing_requirements):
    """Create a weekly roster allowing nurses to work in ICU, Ward, or both."""

    model = cp_model.CpModel()
    departments = ["ICU", "Ward"]
    x = {}
    workday = {}

    # Create assignment variables.
    for nurse in nurses:
        for department in departments:
            for di, day in enumerate(DAYS):
                for si, shift in enumerate(SHIFTS):
                    x[nurse, department, di, si] = model.NewBoolVar(
                        f"x_{nurses.index(nurse)}_{department}_{di}_{si}"
                    )

    availability_lookup = {
        (row["Nurse"], row["Day"]): row
        for _, row in availability_df.iterrows()
    }

    # --------------------------------------------------------
    # AVAILABILITY AND SHIFT CONSTRAINTS
    # --------------------------------------------------------

    for nurse in nurses:
        eligible_departments = nurse_departments.get(nurse, [])

        for di, day in enumerate(DAYS):
            row = availability_lookup[(nurse, day)]
            allowed = row["Available Shifts"]
            is_off = bool(row["Off day"])
            shift_type = row["Shift Type"]

            daily_assignments = []

            for department in departments:
                for si, shift in enumerate(SHIFTS):
                    variable = x[nurse, department, di, si]
                    daily_assignments.append(variable)

                    if department not in eligible_departments:
                        model.Add(variable == 0)

            # An Off day applies to the nurse across ALL departments.
                    if is_off:
                        model.Add(variable == 0)
                    elif shift not in allowed:
                        model.Add(variable == 0)
