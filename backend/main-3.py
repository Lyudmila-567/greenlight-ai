"""
Greenlight AI — MVP backend (FastAPI + Google ADK + ClickHouse MCP, Vertex AI)

Pipeline:
  1. Deterministic feasibility check (no LLM call — fast, free)
  2. Agent 1 "Bob" (Financial & Data) — queries ClickHouse via MCPToolset,
     writes a financial viability statement (free text, since it uses tools)
  2b. Bob Verdict Agent — a second, tool-free agent that reads Bob's text and
      extracts a structured APPROVED/REJECTED verdict. If REJECTED, the
      pipeline stops here (matches the original architecture: Agent 1 can
      halt the whole conveyor).
  3. Agent 2 (Narrative Architect) — writes Genre / Title / Logline / Synopsis
  4. Agent 4 (Bio-Feedback QA) — simulates an attention-retention score;
     if REJECTED (<40%), sends feedback back to Agent 2 for a rewrite
     (capped at MAX_REWRITES attempts to control cost)
  5. Agent 3 (Marketing & VFX) — writes production/marketing bullets

Run locally:
  uvicorn main:app --reload --port 8000
"""

import os
from dotenv import load_dotenv
load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0594850756"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GEMINI_MODEL"] = "gemini-3.1-flash-lite"
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", r"C:\Users\HP\Desktop\Greenlight_AI\backend\gen-lang-client-0594850756-913e146a877d.json")
print("FILE EXISTS:", os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]))
print("DEBUG VERTEX:", os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"), os.environ.get("GOOGLE_CLOUD_PROJECT"), os.environ.get("GOOGLE_CLOUD_LOCATION"))

import uuid
import asyncio
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
APP_NAME = "greenlight_ai"

MIN_BUDGET_BY_GENRE = {
    "Sci-Fi": 5_000_000,
    "Action": 5_000_000,
    "Horror": 500_000,
    "Drama": 250_000,
}
MAX_REALISTIC_ROI = 15
MAX_REWRITES = 1

# ---------------------------------------------------------------------------
# ClickHouse MCP tool (shared by Agent 1)
# ---------------------------------------------------------------------------

def build_clickhouse_toolset() -> MCPToolset:
    env = {
        "CLICKHOUSE_HOST": os.environ.get("CLICKHOUSE_HOST", "muykicrksu.europe-west2.gcp.clickhouse.cloud"),
        "CLICKHOUSE_PORT": os.getenv("CLICKHOUSE_PORT", "8443"),
        "CLICKHOUSE_USER": os.getenv("CLICKHOUSE_USER", "default"),
        "CLICKHOUSE_PASSWORD": os.getenv("CLICKHOUSE_PASSWORD", ""),
        "CLICKHOUSE_SECURE": os.getenv("CLICKHOUSE_SECURE", "true"),
    }
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uv",
                args=[
                    "run", "--with", "mcp-clickhouse",
                    "--python", "3.11",
                    "mcp-clickhouse",
                ],
                env=env,
            ),
            timeout=60,
        ),
    )


# ---------------------------------------------------------------------------
# Structured outputs
# ---------------------------------------------------------------------------

class FinancialVerdict(BaseModel):
    verdict: Literal["APPROVED", "REJECTED"]
    reasoning: str


class QAVerdict(BaseModel):
    attention_score_pct: int
    verdict: Literal["APPROVED", "REJECTED"]
    reasoning: str


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def build_agents():
    clickhouse_toolset = build_clickhouse_toolset()

    agent_financial = LlmAgent(
        model=GEMINI_MODEL,
        name="bob_cfo_agent",
        instruction=(
            "You are 'Bob', the strict corporate CFO & data analyst for a film "
            "greenlight boardroom. You have access to a ClickHouse database via "
            "your tools. Query the `historical_movies` table "
            "(columns: title, genre, budget_usd, revenue_usd) and the "
            "`audience_reviews` table (columns: movie_title, genre, "
            "review_text, review_type) — joined by movie TITLE, not an ID. "
            "IMPORTANT: different tables use slightly different genre "
            "naming (e.g. 'Sci-Fi' vs 'Science Fiction' vs 'Science Fiction "
            "& Fantasy'). Never filter genre with an exact match — always "
            "use a partial/fuzzy match, e.g. `genre ILIKE '%Sci%'` for "
            "Sci-Fi, `genre ILIKE '%Action%'` for Action, `genre ILIKE "
            "'%Horror%'` for Horror, `genre ILIKE '%Drama%'` for Drama. "
            "Base every number you state on actual query results — never "
            "invent statistics. If a query fails, a table is empty, or the "
            "data looks unreliable, say so plainly instead of guessing. "
            "End with a clear statement of whether you support or oppose "
            "greenlighting this project."
        ),
        tools=[clickhouse_toolset],
    )

    # Tool-free agent that just reads Bob's free-text statement and extracts
    # a structured verdict. Kept separate from agent_financial because ADK's
    # output_schema is unreliable when combined with tools on the same agent.
    agent_financial_verdict = LlmAgent(
        model=GEMINI_MODEL,
        name="bob_verdict_extractor",
        instruction=(
            "You will be given a CFO's financial viability statement about a "
            "film project. Read it and decide: did the CFO ultimately support "
            "(APPROVED) or oppose/refuse (REJECTED) greenlighting the "
            "project? Base this strictly on what the statement actually "
            "concludes, not on how confident or detailed it sounds. "
            "Summarize the CFO's core reason in 1-2 sentences."
        ),
        output_schema=FinancialVerdict,
    )

    agent_writer = LlmAgent(
        model=GEMINI_MODEL,
        name="narrative_architect_agent",
        instruction=(
            "You are the Narrative Architect. Given a budget constraint and a "
            "list of audience complaints/clichés to avoid, write an original "
            "movie concept. IMPORTANT: the story's theme, setting, and plot "
            "must NOT be about finance, accounting, auditing, ledgers, CFOs, "
            "or corporate/office life - those are production constraints "
            "only, never creative material. Draw the story's work and "
            "conflict from the genre and target audience instead. "
            "Output exactly these headers: "
            "### GENRE (output it exactly as given, do not rename or reinterpret it)\n"
            "### TITLE\n### LOGLINE\n### SYNOPSIS (3 short paragraphs, with a "
            "clear midpoint climax around the story's halfway point).\n"
            "If you receive QA feedback about a previously rejected draft, "
            "revise the concept to directly address that feedback."
        ),
    )

    agent_qa = LlmAgent(
        model=GEMINI_MODEL,
        name="bio_feedback_qa_agent",
        instruction=(
            "You are a Bio-Feedback QA simulator for a film boardroom. Given a "
            "movie synopsis, genre, and target audience, SIMULATE an estimated "
            "audience attention-retention score (0-100%) based on pacing, "
            "originality, and genre fit. This is a simulated estimate, not a "
            "real biometric reading. A score below 40 means verdict REJECTED, "
            "40 or above means verdict APPROVED. Always explain your "
            "reasoning briefly."
        ),
        output_schema=QAVerdict,
    )

    agent_marketing = LlmAgent(
        model=GEMINI_MODEL,
        name="marketing_vfx_agent",
        instruction=(
            "You are Marketing + VFX + QA combined. Given a movie synopsis, "
            "output exactly 3 concise bullet points: "
            "(1) estimated Focus Group Attention % with 1-sentence reasoning, "
            "(2) estimated VFX Load % with 1-sentence reasoning, "
            "(3) a 3-step digital ad-kit rollout timeline."
        ),
    )

    return agent_financial, agent_financial_verdict, agent_writer, agent_qa, agent_marketing


(
    AGENT_FINANCIAL,
    AGENT_FINANCIAL_VERDICT,
    AGENT_WRITER,
    AGENT_QA,
    AGENT_MARKETING,
) = build_agents()
SESSION_SERVICE = InMemorySessionService()


async def run_agent(agent: LlmAgent, prompt: str, user_id: str) -> str:
    session_id = str(uuid.uuid4())
    runner = Runner(app_name=APP_NAME, agent=agent, session_service=SESSION_SERVICE)
    await SESSION_SERVICE.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    content = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = "(no response)"
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or final_text
    return final_text


def _parse_json_response(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return cleaned


async def run_financial_verdict(prompt: str, user_id: str) -> FinancialVerdict:
    raw = await run_agent(AGENT_FINANCIAL_VERDICT, prompt, user_id)
    return FinancialVerdict.model_validate_json(_parse_json_response(raw))


async def run_qa_agent(prompt: str, user_id: str) -> QAVerdict:
    raw = await run_agent(AGENT_QA, prompt, user_id)
    return QAVerdict.model_validate_json(_parse_json_response(raw))


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Greenlight AI MVP Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BoardroomRequest(BaseModel):
    budget_usd: int
    expected_revenue: int
    genre: str
    target_audience: str


class BoardroomResponse(BaseModel):
    status: str  # "rejected" | "approved" | "approved_with_warning"
    reason: Optional[str] = None
    financial_analysis: Optional[str] = None
    synopsis: Optional[str] = None
    marketing: Optional[str] = None
    attention_score_pct: Optional[int] = None
    qa_verdict: Optional[str] = None
    rewrite_count: Optional[int] = None


def deterministic_precheck(req: BoardroomRequest) -> Optional[str]:
    min_budget = MIN_BUDGET_BY_GENRE.get(req.genre, 250_000)
    if req.budget_usd < min_budget:
        return (
            f"Budget ${req.budget_usd:,} is below the realistic minimum of "
            f"${min_budget:,} for {req.genre}."
        )
    roi = req.expected_revenue / max(req.budget_usd, 1)
    if roi > MAX_REALISTIC_ROI:
        return (
            f"Expected ROI of {roi:.1f}x (${req.expected_revenue:,} on a "
            f"${req.budget_usd:,} budget) is outside a realistic range "
            f"(cap: {MAX_REALISTIC_ROI}x)."
        )
    return None


@app.post("/api/boardroom", response_model=BoardroomResponse)
async def boardroom(req: BoardroomRequest):
    rejection = deterministic_precheck(req)
    if rejection:
        return BoardroomResponse(status="rejected", reason=rejection)

    user_id = str(uuid.uuid4())

    try:
        financial_text = await run_agent(
            AGENT_FINANCIAL,
            (
                f"Genre: {req.genre}. Target audience: {req.target_audience}. "
                f"Budget: ${req.budget_usd:,}. Expected revenue: "
                f"${req.expected_revenue:,}. Query the database for lookalike "
                f"movies in this genre (top 10 by revenue_usd) and the top "
                f"negative audience complaints for this genre, then write a "
                f"financial viability statement grounded in that data."
            ),
            user_id,
        )

        # --- Agent 1 gate: does Bob actually support this? ------------
        financial_verdict = await run_financial_verdict(financial_text, user_id)
        if financial_verdict.verdict == "REJECTED":
            return BoardroomResponse(
                status="rejected",
                reason=financial_verdict.reasoning,
                financial_analysis=financial_text,
            )
        # -----------------------------------------------------------------

        writer_text = await run_agent(
            AGENT_WRITER,
            (
                f"Approved budget: ${req.budget_usd:,}."
                f"Target audience: {req.target_audience}. Genre: {req.genre}. "
                f"Write the movie concept now."
            ),
            user_id,
        )

        # --- Agent 4: Bio-Feedback QA loop -----------------------------
        qa_result: Optional[QAVerdict] = None
        rewrite_count = 0
        for attempt in range(MAX_REWRITES + 1):
            qa_result = await run_qa_agent(
                (
                    f"Genre: {req.genre}\nTarget audience: {req.target_audience}\n"
                    f"Synopsis:\n{writer_text}"
                ),
                user_id,
            )
            if qa_result.verdict == "APPROVED" or attempt == MAX_REWRITES:
                break
            rewrite_count += 1
            writer_text = await run_agent(
                AGENT_WRITER,
                (
                    f"Your previous draft was REJECTED by QA "
                    f"(attention score {qa_result.attention_score_pct}%, "
                    f"reason: {qa_result.reasoning}). Revise it to fix this. "
                    f"Genre: {req.genre}. Target audience: {req.target_audience}. "
                    f"Original draft:\n{writer_text}"
                ),
                user_id,
            )
        # -----------------------------------------------------------------

        marketing_text = await run_agent(
            AGENT_MARKETING,
            f"Synopsis:\n{writer_text}",
            user_id,
        )

    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    final_status = "approved" if qa_result.verdict == "APPROVED" else "approved_with_warning"

    return BoardroomResponse(
        status=final_status,
        financial_analysis=financial_text,
        synopsis=writer_text,
        marketing=marketing_text,
        attention_score_pct=qa_result.attention_score_pct,
        qa_verdict=qa_result.verdict,
        rewrite_count=rewrite_count,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}
