import os
import google.generativeai as genai

MODEL = "gemini-2.0-flash"
MAX_TOKENS = 1500

_TEAM_PROFILE = """
- 3-person team: Data Scientist, ML Engineer, Full-Stack Python Developer
- Strengths: Python, machine learning, NLP, data pipelines, REST APIs, Streamlit/FastAPI
- Preferred stack: Python, PyTorch/scikit-learn, FastAPI, PostgreSQL, Hugging Face
"""

_JUDGING_CRITERIA = "Innovation (30%), Technical Complexity (30%), Real-World Impact (25%), Presentation (15%)"

_IDEA_FORMAT = """
For each idea provide:
**Idea N: [Name]**
- Concept: One sentence describing the solution
- Tech Stack: Key libraries/tools
- Winning Edge: Why this wins against the judging criteria
"""

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel(
    model_name=MODEL,
    generation_config=genai.GenerationConfig(max_output_tokens=MAX_TOKENS),
)


def analyze_hackathon(hackathon: dict, past_hackathons: list[dict]) -> str:
    past_context = ""
    if past_hackathons:
        past_titles = [h.get("title", "") for h in past_hackathons if h.get("title")]
        past_context = (
            "\n\nPreviously tracked hackathons (for trend context, avoid repeating these ideas):\n"
            + "\n".join(f"- {t}" for t in past_titles[:10])
        )

    prompt = f"""You are a hackathon strategy expert helping a team win competitions.

## Hackathon Details
- **Name**: {hackathon.get('title', 'Unknown')}
- **Theme/Tracks**: {hackathon.get('theme', 'General')}
- **Prize**: {hackathon.get('prize', 'N/A')}
- **Deadline**: {hackathon.get('deadline', 'N/A')}
- **URL**: {hackathon.get('url', '')}

## Team Profile
{_TEAM_PROFILE}

## Judging Criteria
{_JUDGING_CRITERIA}
{past_context}

## Task
Generate exactly 3 specific, non-generic project ideas tailored to this hackathon's theme and the team's strengths. Each idea must have a clear "Winning Edge" that directly addresses the judging criteria.

{_IDEA_FORMAT}

Be specific — name real datasets, APIs, or techniques. Avoid vague buzzwords."""

    response = _model.generate_content(prompt)
    return response.text
