import os
import re

import streamlit as st

from career_chain import career_chain
from rag_chain import create_rag_chain
from document_processor import process_pdf
from retriever import get_retriever
from faiss_store import create_vectorstore
from output_parser import parser as roadmap_parser


st.set_page_config(
    page_title="AI Career Copilot",
    layout="wide",
)

st.markdown(
    """
<style>
.main {
    background-color: #0E1117;
    color: white;
}

h1, h2, h3 {
    color: white;
}

.stButton button {
    width: 100%;
    border-radius: 10px;
    background-color: #FF4B4B;
    color: white;
    height: 3em;
    border: none;
    font-size: 16px;
}

.stTextInput input {
    border-radius: 10px;
}

.stTextArea textarea {
    border-radius: 10px;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("🧠 AI Career Copilot")
st.write(
    "Generate a personalized AI learning roadmap "
    "based on your skills, goals, and resume."
)

st.sidebar.header("📌 Inputs")
uploaded_file = st.sidebar.file_uploader(
    "Upload Resume PDF (Optional)",
    type="pdf",
)
skills = st.sidebar.text_area(
    "Skills",
    placeholder="Python, Flask, SQL",
)
goal = st.sidebar.text_input(
    "Career Goal",
    placeholder="AI Engineer",
)

generate = st.sidebar.button("🚀 Generate Roadmap")


def _extract_section_after_heading(text: str, heading: str, max_chars: int = 6000) -> str:
    """Return the raw text that appears after a heading until next major section."""
    m = re.search(
        rf"{re.escape(heading)}\s*:?\s*(?:\r?\n)",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return ""

    tail = text[m.end() : m.end() + max_chars]

    cutoff_markers = [
        r"\n\s*=+\s*\n",
        r"\n\s*STEP\s+\d+\s*:?}",
        r"\n\s*FINAL\s+RESUME\s+PROJECTS\s*:?}",
        r"\n\s*INTERVIEW\s+PREPARATION\s*:?}",
        r"\n\s*CURRENT\s+ANALYSIS\s*",
    ]

    for marker in cutoff_markers:
        parts = re.split(marker, tail, maxsplit=1, flags=re.IGNORECASE)
        if parts and parts[0] != tail:
            return parts[0]

    return tail


def extract_missing_skills(roadmap_response: str) -> list[str]:
    """Extract bullet items from the model's Missing Skills section."""
    if not roadmap_response:
        return []

    section = _extract_section_after_heading(str(roadmap_response), "Missing Skills")
    if not section:
        return []

    skills_out: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("-"):
            val = line[1:].strip()
        elif line.startswith("•"):
            val = line[1:].strip()
        else:
            val = re.sub(r"^\d+\.\s*", "", line).strip()

        if not val:
            continue

        if re.match(
            r"^(WHY THIS IS IMPORTANT|WHAT TO LEARN|FREE RESOURCES|MINI PROJECT|ESTIMATED TIME)$",
            val,
            flags=re.IGNORECASE,
        ):
            continue

        skills_out.append(val)

    seen = set()
    deduped: list[str] = []
    for s in skills_out:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    return deduped


def _safe_list(value):
    """Normalize model output into a list without iterating strings into chars."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        lines = [ln.strip() for ln in value.splitlines() if ln.strip()]
        return lines if lines else [value.strip()]
    return [str(value)]


resume_context = ""

if uploaded_file:
    os.makedirs("data/resumes", exist_ok=True)
    pdf_path = os.path.join("data/resumes", uploaded_file.name)

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    chunks = process_pdf(pdf_path)
    vector_db = create_vectorstore(chunks)
    retriever = get_retriever(vector_db)
    resume_rag_chain = create_rag_chain(retriever)
    resume_context = resume_rag_chain.run("Summarize the uploaded resume")


if generate:
    if not skills or not goal:
        st.warning("Please enter skills and career goal.")
        st.stop()

    with st.spinner("Generating personalized AI roadmap..."):
        roadmap_response = career_chain.run(
            {
                "skills": skills,
                "goal": goal,
                "resume_context": resume_context,
            }
        )

    st.subheader("📊 Current Analysis")

    missing_skills: list[str] = []
    parsed_roadmap = None

    try:
        parsed_roadmap = roadmap_parser.parse(str(roadmap_response))
    except Exception:
        parsed_roadmap = None

    if isinstance(parsed_roadmap, dict):
        missing_from_model = parsed_roadmap.get("roadmap", "") or ""
        if missing_from_model:
            missing_skills = extract_missing_skills(str(missing_from_model))

    if not missing_skills:
        missing_skills = extract_missing_skills(str(roadmap_response))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
### ✅ Current Skills

{skills}
"""
        )

    with col2:
        st.markdown(
            f"""
### 🎯 Target Role

{goal}
"""
        )

    with col3:
        st.markdown("### ❌ Missing Skills")

        model_missing = None
        if isinstance(parsed_roadmap, dict):
            model_missing = parsed_roadmap.get("missing_skills")

        if model_missing:
            items = _safe_list(model_missing)
            if isinstance(model_missing, str):
                items = [ln.strip() for ln in model_missing.splitlines() if ln.strip()]

            shown = False
            for s in items:
                s_str = s if isinstance(s, str) else str(s)
                if len(s_str.strip()) < 3:
                    continue
                if s_str.lstrip().startswith("-"):
                    s_str = s_str.lstrip()[1:].strip()
                if s_str.lower().startswith("missing skills"):
                    continue

                if s_str:
                    st.markdown(
                        f"""<div style="border:1px solid #374151; border-radius:10px; padding:10px; margin-bottom:10px;">
<strong>• {s_str}</strong>
</div>""",
                        unsafe_allow_html=True,
                    )
                    shown = True

            if not shown:
                st.write("Not detected from model output.")
        else:
            if missing_skills:
                for s in missing_skills:
                    st.markdown(
                        f"""<div style="border:1px solid #374151; border-radius:10px; padding:10px; margin-bottom:10px;">
<strong>• {s}</strong>
</div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.write("Not detected from model output.")

    if resume_context:
        st.subheader("📄 Resume Analysis")
        st.write(resume_context)

    st.subheader("🚀 Personalized Learning Roadmap")

    if isinstance(parsed_roadmap, dict):
        roadmap_markdown = parsed_roadmap.get("roadmap", "") or ""
        if roadmap_markdown:
            steps = re.split(r"STEP \d+:", str(roadmap_markdown))
            if len(steps) > 1:
                for i, step in enumerate(steps[1:], start=1):
                    with st.expander(f"STEP {i}", expanded=(i == 1)):
                        st.write(step)
            else:
                st.write(roadmap_markdown)

        projects = _safe_list(parsed_roadmap.get("projects", []))
        projects_items = []
        if isinstance(parsed_roadmap.get("projects"), str):
            projects_items = [
                ln.strip()
                for ln in str(parsed_roadmap.get("projects", "")).splitlines()
                if ln.strip()
            ]
        elif projects:
            projects_items = [str(x).strip() for x in projects if str(x).strip()]

        if projects_items:
            st.subheader("💼 Recommended Projects")
            for p in projects_items:
                st.markdown(
                    f"""<div style="border:1px solid #374151; border-radius:10px; padding:10px; margin-bottom:10px;">
<strong>• {p}</strong>
</div>""",
                    unsafe_allow_html=True,
                )

        timeline = parsed_roadmap.get("timeline", [])
        timeline_list = _safe_list(timeline)
        st_timeline_rendered = False

        if isinstance(timeline, list) and timeline and all(
            isinstance(x, (list, tuple)) and len(x) == 2 for x in timeline
        ):
            st.subheader("⏳ Suggested Timeline")
            for week, topic in timeline:
                if str(week).strip() and str(topic).strip():
                    st.markdown(f"✅ **{week}** → {topic}")
                    st_timeline_rendered = True

        if not st_timeline_rendered and timeline_list:
            st.subheader("⏳ Suggested Timeline")
            for item in timeline_list:
                if str(item).strip():
                    st.markdown(f"✅ {str(item).strip()}")

        interview_questions = _safe_list(parsed_roadmap.get("interview_questions", []))
        if interview_questions:
            st.subheader("🎯 Interview Preparation")
            for q in interview_questions:
                q_str = q if isinstance(q, str) else str(q)
                if len(q_str.strip()) < 3:
                    continue
                st.markdown(
                    f"""<div style="border:1px solid #374151; border-radius:10px; padding:10px; margin-bottom:10px;">
<strong>• {q_str.strip()}</strong>
</div>""",
                    unsafe_allow_html=True,
                )

        resources = _safe_list(parsed_roadmap.get("resources", []))
        if resources:
            st.subheader("📚 Recommended Resources")
            for r in resources:
                r_str = r if isinstance(r, str) else str(r)
                if len(r_str.strip()) < 3:
                    continue
                st.markdown(
                    f"""<div style="border:1px solid #374151; border-radius:10px; padding:10px; margin-bottom:10px;">
<strong>• {r_str.strip()}</strong>
</div>""",
                    unsafe_allow_html=True,
                )
    else:
        st.write(str(roadmap_response))
