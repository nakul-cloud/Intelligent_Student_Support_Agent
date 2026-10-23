"""Streamlit interactive dashboard and evaluation UI for Intelligent Student Support Agent.

Features:
- Multi-turn Agent Chat with tool observability, token usage, and latency metrics.
- Two-Tier Memory Inspector (Live Redis Hash + PostgreSQL student_memory table).
- Security & Audit Log Viewer with interactive Cross-Student Ownership attack demonstration.
- Student Academic Records Explorer (Profiles, Fees, Scholarships, Support Tickets).
- System Infrastructure Health Monitor (PostgreSQL, Redis, Qdrant).
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
from sqlalchemy import select, text

from app.config.database import AsyncSessionLocal, engine
from app.config.redis import ping_redis, redis_client
from app.config.settings import settings
from app.models.audit_log import AuditLog
from app.models.student_records import FeeRecord, Scholarship, Student, SupportTicket
from app.models.student_memory import StudentMemory
from app.services.chat_service import ChatService
from app.services.auth_service import AuthService
from app.schemas.auth_schema import LoginRequest, SignupRequest
from app.memory.memory_manager import MemoryManager


# ==============================================================================
# Page Configuration & Modern Theme Styling
# ==============================================================================
st.set_page_config(
    page_title="Intelligent Student Support Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

code, pre, .stCodeBlock {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Glassmorphism card utility */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
    backdrop-filter: blur(10px);
}

.metric-pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 6px;
}
.pill-allowed { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }
.pill-blocked { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }
.pill-approved { background: rgba(59, 130, 246, 0.2); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.4); }
.pill-tool { background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.4); }

.agent-header {
    background: linear-gradient(135deg, #1e1e38 0%, #0f172a 100%);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 24px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# Async Execution Helper
# ==============================================================================
def run_async(coroutine):
    """Executes an async coroutine safely inside Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)


# ==============================================================================
# Backend Data Helpers
# ==============================================================================
async def check_infrastructure_status() -> Dict[str, bool]:
    """Pings PostgreSQL, Redis, and Qdrant to determine service health."""
    status = {"postgres": False, "redis": False, "qdrant": False}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            status["postgres"] = True
    except Exception:
        status["postgres"] = False

    try:
        status["redis"] = await ping_redis()
    except Exception:
        status["redis"] = False

    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.qdrant_url}/collections")
            if resp.status_code == 200:
                status["qdrant"] = True
    except Exception:
        status["qdrant"] = False

    return status


async def fetch_student_records(student_id: str) -> Dict[str, Any]:
    """Fetches full student profile, fees, scholarship, and tickets."""
    async with AsyncSessionLocal() as session:
        # Profile
        res_stu = await session.execute(select(Student).where(Student.student_id == student_id))
        student = res_stu.scalar_one_or_none()

        # Fees
        res_fee = await session.execute(
            select(FeeRecord).where(FeeRecord.student_id == student_id).order_by(FeeRecord.created_at.desc())
        )
        fees = res_fee.scalars().all()

        # Scholarship
        res_sch = await session.execute(
            select(Scholarship).where(Scholarship.student_id == student_id).order_by(Scholarship.created_at.desc())
        )
        scholarships = res_sch.scalars().all()

        # Tickets
        res_tkt = await session.execute(
            select(SupportTicket).where(SupportTicket.student_id == student_id).order_by(SupportTicket.created_at.desc())
        )
        tickets = res_tkt.scalars().all()

        return {
            "student": student,
            "fees": fees,
            "scholarships": scholarships,
            "tickets": tickets,
        }


async def fetch_student_memory(student_id: str) -> Dict[str, Any]:
    """Fetches Tier 1 (Redis) and Tier 2 (PostgreSQL) memory records."""
    # Tier 1: Redis
    redis_key = f"{settings.redis_memory_key_prefix}{student_id}"
    redis_facts = {}
    redis_ttl = -1
    try:
        redis_facts = await redis_client.hgetall(redis_key)
        redis_ttl = await redis_client.ttl(redis_key)
    except Exception:
        pass

    # Tier 2: PostgreSQL
    pg_facts = []
    async with AsyncSessionLocal() as session:
        stmt = (
            select(StudentMemory)
            .where(StudentMemory.student_id == student_id)
            .order_by(StudentMemory.created_at.desc())
        )
        res = await session.execute(stmt)
        pg_facts = res.scalars().all()

    return {
        "redis_facts": redis_facts,
        "redis_ttl": redis_ttl,
        "pg_facts": pg_facts,
    }


async def fetch_audit_logs(limit: int = 40) -> List[AuditLog]:
    """Fetches recent security audit trail entries."""
    async with AsyncSessionLocal() as session:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())


# ==============================================================================
# Session State Initialization
# ==============================================================================
if "student_id" not in st.session_state:
    st.session_state["student_id"] = "STU001"
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None
if "pending_approval" not in st.session_state:
    st.session_state["pending_approval"] = None
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None


# ==============================================================================
# Sidebar: Identity & System Control
# ==============================================================================
with st.sidebar:
    st.title("🎓 Agent Portal")
    st.caption("Intelligent Student Support Architecture")

    # Infrastructure status badges
    infra = run_async(check_infrastructure_status())
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**PG**<br>{'🟢' if infra['postgres'] else '🔴'}", unsafe_allow_html=True)
    with c2:
        st.markdown(f"**Redis**<br>{'🟢' if infra['redis'] else '🔴'}", unsafe_allow_html=True)
    with c3:
        st.markdown(f"**Qdrant**<br>{'🟢' if infra['qdrant'] else '🔴'}", unsafe_allow_html=True)

    st.divider()

    st.subheader("👤 Student Identity & Auth")

    auth_tab_login, auth_tab_signup, auth_tab_demo = st.tabs([
        "🔑 Login",
        "📝 Sign Up",
        "⚡ Quick Switch",
    ])

    with auth_tab_login:
        login_sid = st.text_input("Student ID:", value=st.session_state["student_id"], key="login_sid_input").strip().upper()
        login_pw = st.text_input("Password:", value="Student@123", type="password", key="login_pw_input")
        if st.button("Sign In", use_container_width=True, key="login_btn"):
            async def _do_login(sid: str, pw: str):
                async with AsyncSessionLocal() as session:
                    srv = AuthService(session)
                    return await srv.login(LoginRequest(student_id=sid, password=pw))

            try:
                tok_resp = run_async(_do_login(login_sid, login_pw))
                st.session_state["jwt_token"] = tok_resp.access_token
                st.session_state["student_id"] = login_sid
                st.session_state["messages"] = []
                st.session_state["conversation_id"] = None
                st.success(f"Authenticated as {login_sid}!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with auth_tab_signup:
        st.caption("Enroll a new student or register password:")
        new_sid = st.text_input("New Student ID:", value="", placeholder="e.g. STU007", key="new_sid_input").strip().upper()
        new_name = st.text_input("Full Name:", value="", placeholder="e.g. Ananya Sen", key="new_name_input")
        new_prog = st.selectbox(
            "Programme:",
            ["PGDM AI and DS", "MBA Marketing", "B.Tech CSE", "M.Tech Data Science", "BBA", "PGDM General"],
            key="new_prog_input"
        )
        new_batch = st.text_input("Batch:", value="2025-27", key="new_batch_input")
        new_pw = st.text_input("Set Password (min 8 chars):", type="password", placeholder="Secret@123", key="new_pw_input")

        if st.button("Create Account & Enroll", use_container_width=True, key="signup_btn"):
            if not new_sid or not new_pw or len(new_pw) < 8:
                st.warning("Please provide a valid Student ID and password (min 8 characters).")
            else:
                async def _do_signup(sid: str, name: str, prog: str, batch: str, pw: str):
                    async with AsyncSessionLocal() as session:
                        # 1. Enroll in students directory if not already present
                        res_stu = await session.execute(select(Student).where(Student.student_id == sid))
                        stu = res_stu.scalar_one_or_none()
                        if not stu:
                            stu = Student(
                                student_id=sid,
                                name=name or f"Student {sid}",
                                programme=prog,
                                batch=batch,
                                status="Enrolled",
                            )
                            session.add(stu)
                            await session.flush()

                        # 2. Register credentials
                        srv = AuthService(session)
                        await srv.signup(SignupRequest(student_id=sid, password=pw))
                        # 3. Log them in immediately and issue JWT
                        return await srv.login(LoginRequest(student_id=sid, password=pw))

                try:
                    tok_resp = run_async(_do_signup(new_sid, new_name, new_prog, new_batch, new_pw))
                    st.session_state["jwt_token"] = tok_resp.access_token
                    st.session_state["student_id"] = new_sid
                    st.session_state["messages"] = []
                    st.session_state["conversation_id"] = None
                    st.success(f"Enrolled & authenticated as {new_sid}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign up error: {e}")

    with auth_tab_demo:
        preset_students = {
            "STU001": "STU001 — Rahul Sharma (PGDM AI and DS)",
            "STU002": "STU002 — Priya Patel (MBA Marketing)",
            "STU003": "STU003 — Amit Verma (B.Tech CSE)",
            "STU004": "STU004 — Sneha Gupta (M.Tech Data Science)",
            "STU005": "STU005 — Vikram Singh (BBA)",
        }
        idx = list(preset_students.keys()).index(st.session_state["student_id"]) if st.session_state["student_id"] in preset_students else 0
        selected_preset = st.selectbox(
            "Quick Demo Persona:",
            options=list(preset_students.keys()),
            format_func=lambda x: preset_students[x],
            index=idx,
            key="preset_select_box"
        )
        if selected_preset != st.session_state["student_id"]:
            st.session_state["student_id"] = selected_preset
            st.session_state["jwt_token"] = None
            st.session_state["messages"] = []
            st.session_state["conversation_id"] = None
            st.rerun()

    # Active Auth Status Card
    if st.session_state.get("jwt_token"):
        st.markdown(
            f"""
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 10px; margin-top: 10px;">
                <span style="color: #10b981; font-weight: 600;">🔒 JWT Active Session</span><br>
                <span style="font-size: 0.8rem; color: #94a3b8;">Signed in as <strong>{st.session_state['student_id']}</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", use_container_width=True, key="logout_btn"):
            st.session_state["jwt_token"] = None
            st.session_state["messages"] = []
            st.session_state["conversation_id"] = None
            st.rerun()
    else:
        st.markdown(
            f"""
            <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 8px; padding: 8px; margin-top: 10px;">
                <span style="color: #f59e0b; font-size: 0.82rem; font-weight: 600;">⚡ Active Caller: {st.session_state['student_id']}</span><br>
                <span style="font-size: 0.75rem; color: #94a3b8;">Use Login / Sign Up tabs above for JWT credentials</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("⚙️ Session Controls")
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["conversation_id"] = None
        st.session_state["pending_approval"] = None
        st.success("New conversation started!")
        st.rerun()

    if st.button("🧹 Clear Student Memory (Cache + DB)", use_container_width=True):
        async def _clear_mem(sid: str):
            async with AsyncSessionLocal() as s:
                await s.execute(text(f"DELETE FROM student_memory WHERE student_id = '{sid}'"))
                await s.commit()
            await redis_client.delete(f"{settings.redis_memory_key_prefix}{sid}")

        run_async(_clear_mem(st.session_state["student_id"]))
        st.warning(f"Memory wiped for {st.session_state['student_id']}.")
        st.rerun()

    st.divider()
    st.caption("Agentic AI Engineering End-Term Project")


# ==============================================================================
# Main View: Tabs for Agent Chat, Memory, Security, and Student Records
# ==============================================================================
tab_chat, tab_memory, tab_security, tab_records = st.tabs([
    "💬 Multi-Turn Agent Chat",
    "🧠 Two-Tier Memory Inspector",
    "🛡️ Security & Audit Trail",
    "📊 Student Records Explorer",
])


# ------------------------------------------------------------------------------
# TAB 1: Multi-Turn Agent Chat
# ------------------------------------------------------------------------------
with tab_chat:
    st.markdown(
        f"""
        <div class="agent-header">
            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700;">Student Assistant</h2>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.95rem;">
                Active Caller: <span style="color: #38bdf8; font-weight: 600;">{st.session_state['student_id']}</span> 
                | Model: <span style="color: #a78bfa;">{settings.groq_model}</span>
                | Memory: <span style="color: #34d399;">Hybrid Redis + PostgreSQL</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prompt suggestions
    st.caption("Quick Scenario Prompts:")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    suggested_prompt = None
    with col_p1:
        if st.button("💳 What is my fee status?", use_container_width=True):
            suggested_prompt = "What is my current fee status?"
    with col_p2:
        if st.button("📖 Handbook Payment Policy", use_container_width=True):
            suggested_prompt = "The payment portal failed. Can I pay on the next working day according to the handbook?"
    with col_p3:
        if st.button("🏆 Scholarship Check", use_container_width=True):
            suggested_prompt = "Check if I have any active scholarships or merit grants."
    with col_p4:
        if st.button("🎫 Open Support Ticket", use_container_width=True):
            suggested_prompt = "I need to open a support ticket for portal login failure and payment retry."

    # Render chat conversation history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "trace" in msg and msg["trace"]:
                t = msg["trace"]
                tools_used = [s.get("tool_name") for s in t.get("steps", []) if s.get("type") == "tool_call"]
                duration = t.get("duration_ms", 0)
                tokens = t.get("total_tokens", 0)
                turns = t.get("turn_count", 1)

                badge_html = f"""
                <div style="margin-top: 8px;">
                    <span class="metric-pill pill-tool">⏱️ {duration:.0f} ms</span>
                    <span class="metric-pill pill-tool">🔄 {turns} turns</span>
                    <span class="metric-pill pill-tool">🪙 {tokens} tokens</span>
                """
                for tool in tools_used:
                    badge_html += f'<span class="metric-pill pill-approved">🛠️ {tool}</span>'
                badge_html += "</div>"
                st.markdown(badge_html, unsafe_allow_html=True)

                with st.expander("🔍 View Turn Execution Trace"):
                    st.json(t)

    # User input handler
    chat_input = st.chat_input("Ask a question about fees, handbook policy, tickets, or scholarships...")
    active_query = suggested_prompt or chat_input

    if active_query:
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": active_query})
        with st.chat_message("user"):
            st.markdown(active_query)

        # Execute agent turn
        with st.chat_message("assistant"):
            with st.spinner("Agent deliberating and selecting tools..."):
                async def _send_chat(sid: str, q: str, cid: Optional[str]):
                    async with AsyncSessionLocal() as session:
                        srv = ChatService(session)
                        return await srv.chat(
                            student_id=sid,
                            message=q,
                            conversation_id=cid,
                            debug=True,
                        )

                try:
                    resp = run_async(_send_chat(
                        st.session_state["student_id"],
                        active_query,
                        st.session_state["conversation_id"],
                    ))
                    st.session_state["conversation_id"] = resp.conversation_id

                    # Render response
                    st.markdown(resp.reply)

                    # Observability badges
                    if resp.trace:
                        t = resp.trace
                        tools_used = [s.get("tool_name") for s in t.get("steps", []) if s.get("type") == "tool_call"]
                        badge_html = f"""
                        <div style="margin-top: 8px;">
                            <span class="metric-pill pill-tool">⏱️ {t.get('duration_ms', 0):.0f} ms</span>
                            <span class="metric-pill pill-tool">🔄 {t.get('turn_count', 1)} turns</span>
                            <span class="metric-pill pill-tool">🪙 {t.get('total_tokens', 0)} tokens</span>
                        """
                        for tool in tools_used:
                            badge_html += f'<span class="metric-pill pill-approved">🛠️ {tool}</span>'
                        badge_html += "</div>"
                        st.markdown(badge_html, unsafe_allow_html=True)

                        with st.expander("🔍 View Turn Execution Trace"):
                            st.json(t)

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": resp.reply,
                        "trace": resp.trace,
                    })

                except Exception as ex:
                    st.error(f"Execution Error: {ex}")


# ------------------------------------------------------------------------------
# TAB 2: Two-Tier Memory Inspector
# ------------------------------------------------------------------------------
with tab_memory:
    st.subheader(f"🧠 Memory System for {st.session_state['student_id']}")
    st.caption("Visualizing Tier 1 (Fast In-Memory Redis Hash) and Tier 2 (Persistent PostgreSQL Facts Table).")

    mem_data = run_async(fetch_student_memory(st.session_state["student_id"]))

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("#### ⚡ Tier 1: In-Memory Redis Cache")
        st.markdown(f"`student_memory:{st.session_state['student_id']}`")
        if mem_data["redis_facts"]:
            ttl_info = f"Expires in: **{mem_data['redis_ttl']}s**" if mem_data["redis_ttl"] > 0 else "TTL: None"
            st.info(ttl_info)
            st.json(mem_data["redis_facts"])
        else:
            st.warning("Redis cache miss (Empty or expired). Facts will be loaded from PostgreSQL on next query.")

    with col_m2:
        st.markdown("#### 🗄️ Tier 2: Persistent PostgreSQL Records")
        st.markdown(f"`student_memory` Table (Filtered by `{st.session_state['student_id']}`)")
        if mem_data["pg_facts"]:
            table_records = []
            for fact in mem_data["pg_facts"]:
                table_records.append({
                    "Fact Key": fact.fact_key,
                    "Fact Value": fact.fact_value,
                    "Created At": fact.created_at.strftime("%Y-%m-%d %H:%M:%S") if fact.created_at else "",
                    "Updated At": fact.updated_at.strftime("%Y-%m-%d %H:%M:%S") if fact.updated_at else "",
                })
            st.dataframe(table_records, use_container_width=True)
        else:
            st.info("No long-term facts recorded in PostgreSQL yet.")

    st.divider()

    st.subheader("🧪 Interactive Safety Filter & Memory Tester")
    st.caption("Test how the agent extracts academic facts while strictly scrubbing sensitive credentials (OTP, passwords, cards).")
    test_input = st.text_input(
        "Enter sample student phrase to test fact extraction:",
        value="I am studying PGDM AI and DS in batch 2025-27 and my temporary OTP is 894102",
    )

    if st.button("Run Memory Ingestion Test"):
        async def _test_save(sid: str, txt: str):
            async with AsyncSessionLocal() as session:
                mm = MemoryManager(session)
                await mm.save_memory(sid, txt)
                return await mm.load_memory(sid)

        res_prompt_snippet = run_async(_test_save(st.session_state["student_id"], test_input))
        st.success("Extraction executed! Updated system prompt memory snippet:")
        st.code(res_prompt_snippet, language="markdown")
        st.rerun()


# ------------------------------------------------------------------------------
# TAB 3: Security & Audit Trail
# ------------------------------------------------------------------------------
with tab_security:
    st.subheader("🛡️ Enterprise Security & Audit Trail")
    st.caption("Immutable PostgreSQL audit records tracking every tool invocation, ownership check, and approval.")

    # Cross-Student Hijack Attack Simulator
    st.markdown("#### ⚔️ Attack Simulation: Cross-Student ID Hijack")
    st.write(
        f"Simulate caller **{st.session_state['student_id']}** attempting to query private fee status "
        f"for a different student **STU002 / STU001**."
    )

    col_atk1, col_atk2 = st.columns([2, 1])
    with col_atk1:
        target_victim_id = st.text_input("Target Student ID to attack:", value="STU002" if st.session_state["student_id"] != "STU002" else "STU001")
    with col_atk2:
        st.write("")
        st.write("")
        if st.button("💥 Execute Hijack Attempt", use_container_width=True):
            from app.tools.fee_tool import get_fee_status

            async def _run_attack(caller_id: str, victim_id: str):
                return await get_fee_status(
                    student_id=victim_id,
                    requesting_student_id=caller_id,
                )

            res = run_async(_run_attack(st.session_state["student_id"], target_victim_id))
            st.error(f"Agent Interceptor: {res}")
            st.rerun()

    st.divider()

    # Real-time Audit Trail Table
    logs = run_async(fetch_audit_logs(limit=30))
    total_events = len(logs)
    allowed_count = sum(1 for l in logs if l.status == "ALLOWED")
    blocked_count = sum(1 for l in logs if l.status == "BLOCKED")
    approved_count = sum(1 for l in logs if l.status == "APPROVED")

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    c_m1.metric("Recent Audit Events", total_events)
    c_m2.metric("Allowed Actions", allowed_count)
    c_m3.metric("Blocked Breaches", blocked_count)
    c_m4.metric("Approved Actions", approved_count)

    audit_table = []
    for l in logs:
        audit_table.append({
            "Timestamp": l.created_at.strftime("%H:%M:%S") if l.created_at else "",
            "Caller Student": l.student_id,
            "Target Student": l.target_student_id,
            "Action / Tool": l.action,
            "Status": l.status,
            "Details": l.details,
        })

    if audit_table:
        st.dataframe(audit_table, use_container_width=True)
    else:
        st.info("No audit logs found.")


# ------------------------------------------------------------------------------
# TAB 4: Student Records Explorer
# ------------------------------------------------------------------------------
with tab_records:
    st.subheader(f"📊 Student Ledger & Records: {st.session_state['student_id']}")
    records = run_async(fetch_student_records(st.session_state["student_id"]))

    student = records["student"]
    if student:
        st.markdown(
            f"""
            <div class="glass-card">
                <h3 style="margin: 0; color: #38bdf8;">{student.name} ({student.student_id})</h3>
                <p style="margin: 4px 0; color: #94a3b8;">
                    <strong>Programme:</strong> {student.programme} | 
                    <strong>Batch:</strong> {student.batch} | 
                    <strong>Status:</strong> {student.status}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("#### 💳 Fee Ledger")
            if records["fees"]:
                fee_rows = []
                for f in records["fees"]:
                    fee_rows.append({
                        "Total Fee (INR)": f.total_fee,
                        "Paid (INR)": f.paid,
                        "Pending (INR)": f.pending,
                        "Due Date": f.due_date,
                        "Status": f.status,
                        "Receipt": f.receipt or "N/A",
                    })
                st.dataframe(fee_rows, use_container_width=True)
            else:
                st.info("No fee records found.")

        with col_r2:
            st.markdown("#### 🏆 Scholarships & Grants")
            if records["scholarships"]:
                sch_rows = []
                for s in records["scholarships"]:
                    sch_rows.append({
                        "Scholarship Scheme": s.scholarship_type,
                        "Coverage": f"{s.percentage}%",
                        "Semester Grant (INR)": s.amount_per_semester,
                        "Status": s.status,
                    })
                st.dataframe(sch_rows, use_container_width=True)
            else:
                st.info("No scholarship records found.")

        st.divider()
        st.markdown("#### 🎫 Support Tickets")
        if records["tickets"]:
            tkt_rows = []
            for t in records["tickets"]:
                tkt_rows.append({
                    "Ticket ID": t.ticket_id,
                    "Category": t.category,
                    "Description": t.description,
                    "Priority": t.priority,
                    "Status": t.status,
                    "Created": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
                })
            st.dataframe(tkt_rows, use_container_width=True)
        else:
            st.info("No support tickets on record.")

    else:
        st.warning(f"Student ID '{st.session_state['student_id']}' not found in the student database.")
