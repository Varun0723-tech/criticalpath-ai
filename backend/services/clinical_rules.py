from __future__ import annotations

from dataclasses import dataclass


RED_FLAG_KEYWORDS = [
    "chest pain",
    "breathing difficulty",
    "difficulty breathing",
    "shortness of breath",
    "confusion",
    "severe headache",
    "high fever",
    "vomiting blood",
    "hematemesis",
    "unconsciousness",
    "loss of consciousness",
    "severe bleeding",
]

SEVERE_SYMPTOM_KEYWORDS = [
    "chest pain",
    "breathing difficulty",
    "difficulty breathing",
    "shortness of breath",
    "confusion",
    "severe headache",
    "high fever",
    "vomiting blood",
    "hematemesis",
    "unconsciousness",
    "loss of consciousness",
    "severe bleeding",
    "rapid heartbeat",
    "wheezing",
    "fainting",
]

URGENT_CLUES = {
    "fever",
    "high fever",
    "abdominal pain",
    "vomiting",
    "dizziness",
    "confusion",
    "severe headache",
    "fainting",
    "wheezing",
    "rapid heartbeat",
    "dehydration",
    "weakness",
}

TEST_SUGGESTIONS = {
    "chest pain": ["ECG", "Cardiac enzymes", "Chest X-ray"],
    "shortness of breath": ["Pulse oximetry", "Chest X-ray", "Arterial blood gas"],
    "breathing difficulty": ["Pulse oximetry", "Chest X-ray", "Arterial blood gas"],
    "difficulty breathing": ["Pulse oximetry", "Chest X-ray", "Arterial blood gas"],
    "fever": ["CBC", "CRP", "Urinalysis"],
    "high fever": ["CBC", "Blood cultures", "Serum lactate"],
    "abdominal pain": ["CBC", "Comprehensive metabolic panel", "Abdominal ultrasound"],
    "vomiting": ["Electrolytes", "Glucose", "Hydration assessment"],
    "vomiting blood": ["CBC", "Coagulation panel", "Type and screen"],
    "hematemesis": ["CBC", "Coagulation panel", "Type and screen"],
    "headache": ["Neurological exam", "CT head if focal deficits", "Blood pressure check"],
    "severe headache": ["Neurological exam", "CT head if focal deficits", "Blood pressure check"],
    "cough": ["Chest X-ray", "CBC", "Viral panel if indicated"],
    "dizziness": ["Orthostatic vitals", "ECG", "Glucose"],
    "confusion": ["Neurological exam", "Glucose", "Basic metabolic panel"],
    "severe bleeding": ["CBC", "Coagulation panel", "Type and screen"],
}


@dataclass(frozen=True)
class ConditionProfile:
    name: str
    symptoms: tuple[str, ...]
    rationale: str


CONDITION_LIBRARY = (
    ConditionProfile(
        name="Acute coronary syndrome",
        symptoms=("chest pain", "shortness of breath", "nausea", "sweating", "arm pain"),
        rationale="The combination of chest discomfort and cardiopulmonary symptoms can represent myocardial ischemia.",
    ),
    ConditionProfile(
        name="Pulmonary embolism",
        symptoms=("shortness of breath", "chest pain", "cough", "dizziness", "rapid heartbeat"),
        rationale="Breathing difficulty with chest symptoms raises concern for an acute pulmonary cause.",
    ),
    ConditionProfile(
        name="Asthma exacerbation",
        symptoms=("shortness of breath", "wheezing", "cough", "chest tightness"),
        rationale="Wheezing with respiratory symptoms is consistent with acute bronchospasm.",
    ),
    ConditionProfile(
        name="Pneumonia",
        symptoms=("fever", "cough", "shortness of breath", "chest pain", "fatigue"),
        rationale="Respiratory symptoms plus fever often indicate a lower respiratory infection.",
    ),
    ConditionProfile(
        name="Heart failure exacerbation",
        symptoms=("shortness of breath", "chest pain", "fatigue", "rapid heartbeat", "leg swelling"),
        rationale="Breathing difficulty with cardiopulmonary symptoms can reflect acute decompensated heart failure.",
    ),
    ConditionProfile(
        name="Appendicitis",
        symptoms=("abdominal pain", "fever", "nausea", "vomiting", "loss of appetite"),
        rationale="Abdominal pain with gastrointestinal upset can fit an acute surgical abdomen pattern.",
    ),
    ConditionProfile(
        name="Gastroenteritis",
        symptoms=("vomiting", "diarrhea", "abdominal pain", "fever", "dehydration"),
        rationale="Vomiting and abdominal symptoms commonly reflect an infectious gastrointestinal syndrome.",
    ),
    ConditionProfile(
        name="Migraine",
        symptoms=("headache", "nausea", "vomiting", "sensitivity to light", "dizziness"),
        rationale="Headache with nausea and sensory sensitivity is a common migraine presentation.",
    ),
    ConditionProfile(
        name="Meningitis",
        symptoms=("severe headache", "high fever", "confusion", "vomiting", "neck stiffness"),
        rationale="Severe headache with fever and altered mental status can indicate a central nervous system infection.",
    ),
    ConditionProfile(
        name="Stroke or transient ischemic attack",
        symptoms=("weakness", "confusion", "slurred speech", "facial droop", "unconsciousness"),
        rationale="Neurologic deficits or altered consciousness must be considered cerebrovascular until proven otherwise.",
    ),
    ConditionProfile(
        name="Upper gastrointestinal bleed",
        symptoms=("vomiting blood", "hematemesis", "dizziness", "weakness", "abdominal pain"),
        rationale="Vomiting blood with hemodynamic symptoms is clinically relevant for an upper GI source of bleeding.",
    ),
    ConditionProfile(
        name="Sepsis or severe systemic infection",
        symptoms=("high fever", "fever", "confusion", "weakness", "rapid heartbeat"),
        rationale="Systemic symptoms with altered mentation or marked fever raise concern for evolving sepsis.",
    ),
    ConditionProfile(
        name="Dehydration",
        symptoms=("vomiting", "diarrhea", "dizziness", "weakness", "dry mouth"),
        rationale="Fluid losses can explain dizziness, weakness, and gastrointestinal symptoms.",
    ),
    ConditionProfile(
        name="Viral upper respiratory infection",
        symptoms=("fever", "cough", "sore throat", "runny nose", "fatigue"),
        rationale="Common viral respiratory illnesses often present with fever, cough, and upper airway complaints.",
    ),
)


def normalize_symptom(symptom: str) -> str:
    return " ".join(symptom.strip().lower().split())


def symptom_matches(symptom: str, keyword: str) -> bool:
    return keyword in symptom


def find_matching_keywords(symptoms: list[str], keywords: list[str] | set[str] | tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for keyword in keywords:
        if any(symptom_matches(symptom, keyword) for symptom in symptoms):
            matches.append(keyword)
    return matches


def acuity_rank(level: str) -> int:
    return {"Normal": 0, "Urgent": 1, "Critical": 2}[level]


def higher_acuity(level_a: str, level_b: str) -> str:
    return level_a if acuity_rank(level_a) >= acuity_rank(level_b) else level_b


def infer_triage(symptoms: list[str], age: int) -> tuple[str, str]:
    red_flags = find_matching_keywords(symptoms, RED_FLAG_KEYWORDS)
    if red_flags:
        reasoning = (
            "Critical severity assigned because the symptom profile contains ER red flags: "
            f"{', '.join(red_flags)}."
        )
        return "Critical", reasoning

    urgent_hits = find_matching_keywords(symptoms, URGENT_CLUES)
    acuity_score = len(urgent_hits)

    if age >= 70:
        acuity_score += 1
    if age <= 5:
        acuity_score += 1
    if len(symptoms) >= 4:
        acuity_score += 1

    if acuity_score >= 2:
        reasoning = (
            "Urgent severity assigned from symptom burden and concerning features such as "
            f"{', '.join(urgent_hits) if urgent_hits else 'patient age or multi-symptom presentation'}."
        )
        return "Urgent", reasoning

    return "Normal", "No immediate ER red flags were detected and the current symptom burden appears lower acuity."


def confidence_from_overlap(overlap_count: int, triage_level: str, red_flag_count: int) -> int:
    severity_bonus = {"Critical": 10, "Urgent": 6, "Normal": 0}[triage_level]
    confidence = 38 + (overlap_count * 16) + (red_flag_count * 4) + severity_bonus
    return max(32, min(confidence, 92))


def score_condition(profile: ConditionProfile, symptoms: list[str]) -> tuple[int, list[str]]:
    hits = [candidate for candidate in profile.symptoms if any(symptom_matches(symptom, candidate) for symptom in symptoms)]
    score = len(hits)

    if score == 0 and profile.name == "Viral upper respiratory infection" and any("fever" in symptom for symptom in symptoms):
        score = 1

    return score, hits


def shortlist_conditions(symptoms: list[str]) -> list[tuple[ConditionProfile, int, list[str]]]:
    scored: list[tuple[ConditionProfile, int, list[str]]] = []
    for profile in CONDITION_LIBRARY:
        score, hits = score_condition(profile, symptoms)
        scored.append((profile, score, hits))

    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    top = [item for item in ranked if item[1] > 0][:3]

    if len(top) < 3:
        fillers = [item for item in ranked if item not in top][: 3 - len(top)]
        top.extend(fillers)

    return top[:3]


def suggested_tests(symptoms: list[str], triage_level: str) -> list[str]:
    tests: list[str] = []

    for symptom in symptoms:
        for keyword, options in TEST_SUGGESTIONS.items():
            if symptom_matches(symptom, keyword):
                for option in options:
                    if option not in tests:
                        tests.append(option)

    if triage_level == "Critical":
        for option in ["Continuous monitoring", "IV access", "Repeat vital signs"]:
            if option not in tests:
                tests.append(option)
    elif triage_level == "Urgent":
        for option in ["Full vital signs review", "Targeted imaging based on exam"]:
            if option not in tests:
                tests.append(option)

    return tests[:6]


def monitoring_guidance(triage_level: str, symptoms: list[str]) -> list[str]:
    advice: list[str] = []

    if triage_level == "Critical":
        advice.extend(
            [
                "Continuous cardiac and pulse oximetry monitoring.",
                "Repeat full vital signs frequently.",
                "Escalate immediately for worsening consciousness, breathing, or bleeding.",
            ]
        )
    elif triage_level == "Urgent":
        advice.extend(
            [
                "Reassess symptoms and vital signs during same-day evaluation.",
                "Escalate care if pain intensifies, fever rises, or new neurologic symptoms appear.",
            ]
        )
    else:
        advice.extend(
            [
                "Monitor symptoms, hydration, and temperature at home.",
                "Seek urgent review if red-flag symptoms develop or symptoms persist.",
            ]
        )

    if any(symptom_matches(symptom, "high fever") for symptom in symptoms):
        advice.append("Track temperature trends and watch for confusion or dehydration.")

    return advice[:4]
