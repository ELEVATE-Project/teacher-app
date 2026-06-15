"""
lesson_planner_routes.py — Flask Blueprint: /api/lesson/*

Lesson Planner feature for Guru-Sikshan.

Handles:
  - Lesson plan generation (Gemini + RAGFlow context)
  - Saved lesson plan CRUD (Supabase)
  - Teacher-level history / retrieval
  - Assignment sheet generation
  - Quick topic retrieval (RAG-only, no LLM)

All write routes require JWT. Generation requires admin or higher.
Saved-plan reads are scoped to the requesting teacher.
"""
# TODO : Still working on all of these , a base defination has been set and WILL need updates.
import json
import traceback
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from flask import Blueprint, Response, jsonify, request, stream_with_context, g
import jwt as pyjwt
import os

import ragflow_client as rf
from supabase_client import db

# ─────────────────────────────────────────────────────────────────────────────
# Blueprint setup
# ─────────────────────────────────────────────────────────────────────────────

lesson_bp = Blueprint("lesson", __name__, url_prefix="/api/lesson")

JWT_SECRET = os.getenv("JWT_SECRET")
DEFAULT_DATASET_NAME = os.getenv("RAGFLOW_DEFAULT_DATASET", "gurusikshan-ncert")
DEFAULT_CHAT_ID = os.getenv("RAGFLOW_CHAT_ID", "")

if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ─────────────────────────────────────────────────────────────────────────────
# Auth decorators 
# ─────────────────────────────────────────────────────────────────────────────

from functools import wraps


def require_jwt(auth_required: bool = True):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                if auth_required:
                    return jsonify(error="Missing or invalid authorization token"), 401
                g.user = None
                return f(*args, **kwargs)

            token = auth_header.split(" ")[1]
            try:
                payload = pyjwt.decode(
                    token, JWT_SECRET, algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                g.user = payload
            except pyjwt.ExpiredSignatureError:
                if auth_required:
                    return jsonify(error="Token expired"), 401
                g.user = None
            except pyjwt.InvalidTokenError as e:
                if auth_required:
                    return jsonify(error=f"Invalid token: {e}"), 401
                g.user = None
            return f(*args, **kwargs)
        return wrapped
    return decorator


def require_admin_or_higher():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = getattr(g, "user", None)
            if not user:
                return jsonify(error="Authentication required"), 401
            if user.get("role") not in ("admin", "super_admin"):
                return jsonify(error="Admin access required"), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean_gemini_json(text: str) -> Dict[str, Any]:
    """Strip markdown fences and parse JSON from Gemini output."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:].strip()
    return json.loads(raw)

#WORKS
def _resolve_dataset_id(board: str = "CBSE", explicit_dataset_id: str = "") -> str:
    """
    Dynamically maps the requested school board to a live RAGFlow dataset UUID
    using the resource_source_routing database table.
    """
    if explicit_dataset_id:
        return explicit_dataset_id

    try:
        result = (
            db.client.table("resource_source_routing")
            .select("ragflow_dataset_id")
            .eq("board", board)
            .eq("is_active", True)
            .order("priority", desc=True) 
            .execute()
        )
        
        if result.data and len(result.data) > 0:
            resolved_id = result.data[0].get("ragflow_dataset_id")
            if resolved_id:
                return resolved_id
    except Exception as err:
        print(f"[WARN] Database lookup on resource_source_routing failed: {err}")

    fallback_id = os.getenv("RAGFLOW_DEFAULT_DATASET_ID")
    if not fallback_id:
        raise ValueError(f"No active RAGFlow dataset mapped for board '{board}' and no default fallback configured.")
        
    return fallback_id

#Depricated for now 
def _teacher_cluster(teacher_id: str) -> str:
    try:
        result = (
            db.client.table("teachers")
            .select("cluster")
            .eq("id", teacher_id)
            .single()
            .execute()
        )
        return (result.data or {}).get("cluster", "") or ""
    except Exception:
        return ""

#WORKS , base prompt for a all in one response
def _build_lesson_prompt(
    class_name: str,
    subject: str,
    topic: str,
    duration_minutes: int,
    chunk_context: str,
    language: str = "English",
    board: str = "CBSE",
    learning_objectives: Optional[List[str]] = None,
) -> str:
    objectives_hint = ""
    if learning_objectives:
        objectives_hint = (
            "\nUse these teacher-provided learning objectives as a starting guide:\n"
            + "\n".join(f"- {o}" for o in learning_objectives)
        )

    return f"""You are an expert curriculum designer for Indian school teachers ({board} board).
Create a detailed, practical lesson plan.

Class: {class_name}
Subject: {subject}
Topic: {topic}
Duration: {duration_minutes} minutes
Language of instruction: {language}
{objectives_hint}
{chunk_context}

Return ONLY valid JSON (no markdown fences) with this exact structure:
{{
  "lesson": {{
    "title": "...",
    "class_name": "{class_name}",
    "subject": "{subject}",
    "topic": "{topic}",
    "board": "{board}",
    "language": "{language}",
    "duration_minutes": {duration_minutes},
    "learning_objectives": ["...", "..."],
    "materials_needed": ["...", "..."],
    "sections": [
      {{"name": "Introduction",  "duration_minutes": 5,  "content": "...", "activities": ["..."]}},
      {{"name": "Main Content",  "duration_minutes": 25, "content": "...", "activities": ["..."]}},
      {{"name": "Practice",      "duration_minutes": 10, "content": "...", "activities": ["..."]}},
      {{"name": "Summary",       "duration_minutes": 5,  "content": "...", "activities": ["..."]}}
    ],
    "differentiation": {{
      "struggling": "...",
      "advanced": "..."
    }},
    "zero_resource_tips": ["...", "..."],
    "homework": "..."
  }},
  "assignment": {{
    "title": "...",
    "type": "worksheet",
    "estimated_minutes": 20,
    "questions": [
      {{"type": "mcq",          "question": "...", "options": ["A", "B", "C", "D"], "answer": "A"}},
      {{"type": "short_answer", "question": "..."}},
      {{"type": "activity",     "question": "..."}}
    ]
  }},
  "rag_context_used": {"true" if chunk_context else "false"}
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. Generate a lesson plan (Gemini + RAGFlow context) ─────────────────────
# WORKS
@lesson_bp.route("/generate", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def generate_lesson():
    """
    Generate a lesson plan for a class/subject/topic.

    Request body:
      class_name       str  required
      subject          str  required
      topic            str  required
      teacher_id       str  optional  — for personalisation & saving history
      dataset_name     str  optional  — RAGFlow dataset to pull context from
      dataset_id       str  optional  — explicit dataset UUID
      duration_minutes int  optional  default 45
      language         str  optional  default "English"
      board            str  optional  default "CBSE"
      learning_objectives list[str] optional
      save             bool optional  default False — auto-save to Supabase
    """
    try:
        data = request.json or {}
        class_name = (data.get("class_name") or "").strip()
        subject    = (data.get("subject")    or "").strip()
        topic      = (data.get("topic")      or "").strip()

        if not all([class_name, subject, topic]):
            return jsonify(error="class_name, subject, and topic are required"), 400

        teacher_id       = data.get("teacher_id", "") or ""
        dataset_name     = (data.get("dataset_name") or DEFAULT_DATASET_NAME).strip()
        dataset_id_param = (data.get("dataset_id")   or "").strip()
        duration_minutes = int(data.get("duration_minutes", 45))
        language         = (data.get("language", "English") or "English").strip()
        board            = (data.get("board",    "CBSE")    or "CBSE").strip()
        learning_objectives: List[str] = data.get("learning_objectives") or []
        auto_save        = bool(data.get("save", False))

        # Pull RAG context
        dataset_id = ""
        chunks: List[Dict[str, Any]] = []
        try:
            dataset_id = _resolve_dataset_id(
                board=board,
                explicit_dataset_id=dataset_id_param
            )
            
            # Execute the raw vector lookup against the determined dataset UUID
            chunks = rf.retrieve_chunks(
                question=f"{class_name} {subject} {topic}",
                dataset_ids=[dataset_id],
                top_k=5,
                similarity_threshold=0.2,
            )
        except Exception as rag_err:
            print(f"[WARN] RAG context fetch failed: {rag_err}")
            dataset_id = None
            chunks = []

        chunk_context = ""
        if chunks:
            chunk_context = "\n\nReference material from NCERT/dataset:\n" + "\n---\n".join(
                c.get("content", "") for c in chunks[:4] if c.get("content")
            )

        # Build prompt & call Gemini
        prompt = _build_lesson_prompt(
            class_name=class_name,
            subject=subject,
            topic=topic,
            duration_minutes=duration_minutes,
            chunk_context=chunk_context,
            language=language,
            board=board,
            learning_objectives=learning_objectives,
        )

        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "temperature": 0.7,
                "response_mime_type": "application/json",
            },
        )
        response = model.generate_content(prompt)
        result   = _clean_gemini_json(response.text)

        lesson     = result.get("lesson")
        assignment = result.get("assignment")

        # Optionally save to Supabase , normally dont ig 
        saved_id = None
        if auto_save and teacher_id and lesson:
            try:
                insert_result = (
                    db.client.table("lesson_plans")
                    .insert({
                        "teacher_id":    teacher_id,
                        "class_name":    class_name,
                        "subject":       subject,
                        "topic":         topic,
                        "board":         board,
                        "language":      language,
                        "duration_minutes": duration_minutes,
                        "lesson_json":   json.dumps(lesson),
                        "assignment_json": json.dumps(assignment) if assignment else None,
                        "dataset_id":    dataset_id or None,
                        "rag_chunks_used": len(chunks),
                        "status":        "generated",
                    })
                    .execute()
                )
                saved = insert_result.data
                if saved:
                    saved_id = (saved[0] if isinstance(saved, list) else saved).get("id")
            except Exception as save_err:
                print(f"[WARN] Auto-save to lesson_plans failed: {save_err}")

        return jsonify(
            success=True,
            lesson=lesson,
            assignment=assignment,
            dataset_id=dataset_id or None,
            dataset_name=dataset_name,
            rag_chunks_used=len(chunks),
            saved_id=saved_id,
        )

    except json.JSONDecodeError as e:
        traceback.print_exc()
        return jsonify(error=f"Gemini JSON parse error: {e}"), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


# ── Topic retrieval (RAG-only, no LLM) ───────────────────────────────────
# Not tested haha
@lesson_bp.route("/context", methods=["POST"])
@require_jwt(auth_required=True)
def get_topic_context():
    """
    Return raw RAG chunks for a topic — useful for frontend preview
    before generation, or for building custom prompts.

    Request body:
      question     str  required
      dataset_name str  optional
      dataset_id   str  optional
      top_k        int  optional  default 6
      similarity_threshold float optional default 0.2
    """
    try:
        data     = request.json or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify(error="question required"), 400

        dataset_id = _resolve_dataset_id(
            board=(data.get("dataset_name") or DEFAULT_DATASET_NAME).strip(),
            explicit_dataset_id=(data.get("dataset_id") or "").strip(),
        )        
        top_k                = int(data.get("top_k", 6))
        similarity_threshold = float(data.get("similarity_threshold", 0.2))

        chunks = rf.retrieve_chunks(
            question=question,
            dataset_ids=[dataset_id],
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        return jsonify(
            success=True,
            dataset_id=dataset_id,
            chunks=chunks,
            count=len(chunks),
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

# ── Regenerate only the assignment for an existing plan ───────────────────
# NOTE : needs to be saved
@lesson_bp.route("/plans/<plan_id>/assignment", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def regenerate_assignment(plan_id: str):
    """
    Re-generate the assignment/worksheet for a saved plan.

    Optionally pass:
      num_mcq          int  default 3
      num_short_answer int  default 2
      num_activity     int  default 1
    """
    try:
        # Fetch existing plan
        result = (
            db.client.table("lesson_plans")
            .select("class_name, subject, topic, board, language, lesson_json")
            .eq("id", plan_id)
            .single()
            .execute()
        )
        if not result.data:
            return jsonify(error="Plan not found"), 404

        plan = result.data if not isinstance(result.data, list) else result.data[0]
        data = request.json or {}

        num_mcq          = int(data.get("num_mcq", 3))
        num_short_answer = int(data.get("num_short_answer", 2))
        num_activity     = int(data.get("num_activity", 1))

        lesson_content = plan.get("lesson_json", "{}")
        if isinstance(lesson_content, str):
            try:
                lesson_content = json.loads(lesson_content)
            except Exception:
                lesson_content = {}

        prompt = f"""Create a student assignment for this lesson.

Class: {plan['class_name']}
Subject: {plan['subject']}
Topic: {plan['topic']}
Board: {plan.get('board', 'CBSE')}

Return ONLY valid JSON:
{{
  "title": "...",
  "type": "worksheet",
  "estimated_minutes": 20,
  "questions": [
    {{"type": "mcq",          "question": "...", "options": ["A","B","C","D"], "answer": "A"}},
    {{"type": "short_answer", "question": "..."}},
    {{"type": "activity",     "question": "..."}}
  ]
}}
Generate {num_mcq} MCQs, {num_short_answer} short-answer, {num_activity} activity questions."""

        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "temperature": 0.7,
                "response_mime_type": "application/json",
            },
        )
        response   = model.generate_content(prompt)
        assignment = _clean_gemini_json(response.text)

        # Persist updated assignment
        db.client.table("lesson_plans").update({
            "assignment_json": json.dumps(assignment),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }).eq("id", plan_id).execute()

        return jsonify(success=True, assignment=assignment, plan_id=plan_id)

    except json.JSONDecodeError as e:
        traceback.print_exc()
        return jsonify(error=f"Gemini JSON parse error: {e}"), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500