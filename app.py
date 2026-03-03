# app.py - FINAL FIXED VERSION WITH REMINDER PERSISTENCE
import streamlit as st
from agents.goal_planner import GoalPlannerAgent
from agents.concept_explainer import ConceptExplainerAgent
from agents.performance_tracker import PerformanceTracker
from tools.quiz_generator import QuizGenerator
from utils.document_processor import chunk_text
from utils.pdf_processor import chunk_pdf_text
from utils.vector_store import create_vector_store
from utils.pdf_export import export_plan_to_pdf
from utils.reminder_manager import ReminderManager
from utils.auth import UserAuth
from utils.todo_manager import TodoManager
import os
import re
import os 
from utils.plan_manager import list_user_plans, load_plan_from_file, delete_plan_file
from datetime import datetime,timedelta
import json
import pandas as pd
import glob





def clean_string(s):
    # Lowercase and remove non-alphanumeric for flexible matching
    return ''.join(c.lower() if c.isalnum() else ' ' for c in s).strip()


# ============================================================================
# SESSION STATE INIT
# ============================================================================
if "scheduled_reminders" not in st.session_state:
    st.session_state.scheduled_reminders = []

# Page config
st.set_page_config(
    page_title="Balu's Study Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for a Clean & Professional "Balu's Edition"
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-family: 'Montserrat', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #f8fafc;
        text-align: center;
        padding: 2rem 0;
        letter-spacing: -0.5px;
    }

    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }

    .stSidebar {
        background-color: #1e293b !important;
        border-right: 1px solid #334155;
    }

    /* Professional Card Style */
    .st-emotion-cache-1ky8h6r, .st-emotion-cache-ke7v6m {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    .stButton>button {
        border-radius: 8px;
        background-color: #10b981;
        color: white;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
        width: 100%;
    }

    .stButton>button:hover {
        background-color: #059669;
        border-color: #059669;
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.2);
    }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }

    .footer-text {
        text-align: center;
        font-size: 0.85rem;
        color: #94a3b8;
        padding: 2rem 0;
    }
    
    /* Clean Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #94a3b8;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        color: #10b981 !important;
        border-bottom-color: #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

if "auth" not in st.session_state:
    st.session_state.auth = UserAuth()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None


# # ============================================================================
# # REMINDER NOTIFICATION POPUP SYSTEM (MODERN)
# # ============================================================================
# if "reminder_manager" in st.session_state:
#     notifications = st.session_state.reminder_manager.get_active_notifications()
#     if notifications:
#         for i, notif in enumerate(notifications):
#             st.markdown(
#                 f"<div class='reminder-popup'>🔔 <b>{notif['message']}</b></div>",
#                 unsafe_allow_html=True
#             )
#             if st.button(f"✖ Dismiss", key=f"dismiss_{i}"):
#                 st.session_state.reminder_manager.clear_notification(i)
#                 st.rerun()
#         st.markdown("---")

# ============================================================================
# LOGIN/REGISTER PAGE
# ============================================================================
if not st.session_state.logged_in:
    st.markdown('<p class="main-header">🎓 Virtual Study Assistant</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        # st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Login to Your Account")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary", use_container_width=True):
            success, message = st.session_state.auth.login_user(login_username, login_password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.session_state.performance_tracker = PerformanceTracker(user_id=login_username)
                st.session_state.todo_manager = TodoManager(user_id=login_username)
                st.session_state.reminder_manager = ReminderManager()
                # LOAD PERSISTED REMINDERS HERE!
                st.session_state.scheduled_reminders = st.session_state.reminder_manager.load_scheduled_reminders(login_username)
                st.session_state.reminder_manager.schedule_reminders_from_file(login_username)
                st.success(f"✅ Welcome back, {login_username}!")
                st.rerun()
            else:
                st.error(f"❌ {message}")
        # st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        # st.markdown('<div class="card">', unsafe_allow_html=True)   
        st.subheader("Create New Account")
        reg_username = st.text_input("Username", key="reg_user")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_pass")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.button("Register", type="primary", use_container_width=True):
            if not reg_username or not reg_email or not reg_password:
                st.error("❌ All fields are required")
            elif reg_password != reg_confirm:
                st.error("❌ Passwords do not match")
            elif len(reg_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                success, message = st.session_state.auth.register_user(reg_username, reg_password, reg_email)
                if success:
                    st.success(f"✅ {message}! Please login.")
                else:
                    st.error(f"❌ {message}")
        # st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================================
# MAIN APP (After Login)
# ============================================================================
if "planner" not in st.session_state:
    st.session_state.planner = GoalPlannerAgent()
if "concept_agent" not in st.session_state:
    st.session_state.concept_agent = None
if "quiz_generator" not in st.session_state:
    st.session_state.quiz_generator = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "reminder_manager" not in st.session_state:
    st.session_state.reminder_manager = ReminderManager()
if "current_plan" not in st.session_state:
    st.session_state.current_plan = None
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

# ============================================================================
# NOTIFICATION POPUP SYSTEM
# ============================================================================
# Enhanced Notification Banner with Card & Animation
if "reminder_manager" in st.session_state:
    notifications = st.session_state.reminder_manager.get_active_notifications()
    if notifications:
        for i, notif in enumerate(notifications):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.warning(f"🔔 **Reminder:** {notif['message']}")
            with col2:
                if st.button("✖", key=f"dismiss_{i}"):
                    st.session_state.reminder_manager.clear_notification(i)
                    st.rerun()
        st.markdown("---")

# Sidebar
st.sidebar.title(f"👤 {st.session_state.username}")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate:",
    ["🏠 Home", "📚 Upload Material", "🎯 Goal Planning",
     "✅ My Tasks", "💬 Ask Questions", "📝 Take Quiz",
     "📊 Performance", "⏰ Reminders"],
    label_visibility="collapsed"
)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

st.sidebar.markdown("---")
if "todo_manager" in st.session_state:
    stats = st.session_state.todo_manager.get_completion_stats()
    st.sidebar.metric("✅ Tasks Done", f"{stats['completed']}/{stats['total']}")

# Unique Feature: Daily Motivation
st.sidebar.markdown("### 💡 Daily Spark")
quotes = [
    "Success is the sum of small efforts, repeated day in and day out.",
    "The expert in anything was once a beginner.",
    "Believe you can and you're halfway there.",
    "Your future self will thank you for studying today.",
    "Don't stop until you're proud."
]
import random
st.sidebar.info(random.choice(quotes))

st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='text-align: center; padding: 20px; color: #94a3b8; font-size: 0.9rem;'>
        Designed by <b>Balu</b> with ❤️
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# HOME PAGE
# ============================================================================
if page == "🏠 Home":
    st.markdown(f'<p class="main-header">Welcome back, {st.session_state.username}! 🎓</p>', unsafe_allow_html=True)
    tracker = st.session_state.performance_tracker
    quiz_count = len(tracker.performance_data.get("quiz_scores", []))
    st.subheader("📈 Your Progress Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📝 Quizzes Taken", quiz_count)
    with col2:
        if "todo_manager" in st.session_state:
            stats = st.session_state.todo_manager.get_completion_stats()
            st.metric("✅ Tasks Done", f"{stats['completed']}/{stats['total']}")
        else:
            st.metric("✅ Tasks Done", 0)

    st.markdown("---")
    st.markdown("""
    ### 🚀 Features Available:
    - **📚 Upload Material** - PDF & TXT support with RAG
    - **🎯 Goal Planning** - AI study plans with PDF export
    - **✅ My Tasks** - Track & complete your study tasks
    - **💬 Ask Questions** - AI-powered Q&A from your materials
    - **📝 Take Quiz** - Auto-generated quizzes with instant feedback
    - **📊 Performance** - Track progress with analytics
    - **⏰ Reminders** - Never miss a study session
    ---
    **Tech:** GPT-4 + LangChain + FAISS + Streamlit
    """)

# ============================================================================
# UPLOAD MATERIAL
# ============================================================================
elif page == "📚 Upload Material":
    st.title("📚 Upload Study Material")
    st.markdown("Upload **PDF** or **TXT** files")
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf"])
    if uploaded_file:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with st.spinner(f"🔄 Processing..."):
            file_path = os.path.join("data", "study_materials", uploaded_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            progress = st.progress(0)
            progress.progress(25, text="Reading...")
            if file_extension == "pdf":
                docs = chunk_pdf_text(file_path)
            else:
                docs = chunk_text(file_path)
            progress.progress(50, text="Embeddings...")
            vs = create_vector_store(docs)
            progress.progress(75, text="AI setup...")
            st.session_state.vector_store = vs
            st.session_state.concept_agent = ConceptExplainerAgent(vs)
            st.session_state.quiz_generator = QuizGenerator(vs)
            progress.progress(100, text="Done!")
            st.success(f"✅ Processed: **{uploaded_file.name}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Chunks", len(docs))
            with col2:
                st.metric("🤖 Q&A", "✓")
            with col3:
                st.metric("📝 Quiz", "✓")

# ============================================================================
# GOAL PLANNING (with persistent multi-alert reminders)
# ============================================================================
elif page == "🎯 Goal Planning":
    st.title("🎯 Create Study Plan")

    def clean_string(s):
        # Lowercase and remove non-alphanumeric for flexible matching
        return ''.join(c.lower() if c.isalnum() else ' ' for c in s).strip()

    username = st.session_state.username

    # ==== 1. FULL PAGE SUGGESTIONS OVERLAY ====
    # ==== 1. FULL PAGE SUGGESTIONS OVERLAY ====
    if st.session_state.get('show_full_suggestions', False):
        suggestions = st.session_state['full_suggestions']

        # Attempt to load as structured JSON dict (new style)
        try:
            if isinstance(suggestions, str):
                suggestions = json.loads(suggestions)
        except Exception:
            pass

        st.markdown(
            "<div style='background:#f7fff4; border:3px solid #55A867;padding:32px 40px;margin:40px 0 60px 0;"
            "border-radius:16px;box-shadow: 0 4px 24px #a4c69f80;text-align:center;'>"
            "<h2 style='color:#137547;font-size:2rem;margin-bottom:28px'>🌟 <b>Study Plan Improvement Suggestions</b></h2>",
            unsafe_allow_html=True
        )

        # Show recommendations if present (from previous-like logic)
        if isinstance(suggestions, dict):
            if "recommendations" in suggestions:
                st.markdown("#### Top Tips:")
                for tip in suggestions["recommendations"]:
                    st.markdown(f"- {tip}")

            if "focus_topics" in suggestions and suggestions["focus_topics"]:
                st.info("**Focus Topics:** " + ", ".join(suggestions["focus_topics"]))

            if "adjusted_hours" in suggestions and suggestions["adjusted_hours"]:
                st.markdown("#### ⏰ Suggested Time Adjustments")
                st.dataframe(pd.DataFrame(suggestions["adjusted_hours"]))

            if "motivational_tips" in suggestions and suggestions["motivational_tips"]:
                st.markdown("#### 💡 Motivation")
                for tip in suggestions["motivational_tips"]:
                    st.success(f"{tip}")

        # fallback for plain string
        elif isinstance(suggestions, str):
            import re
            tips = re.split(r'\.\s+|\n', suggestions)
            tips = [t.strip() for t in tips if len(t.strip()) > 10]
            for tip in tips:
                st.markdown(f"- {tip}")

        if st.button("🔙 Back to Goal Planning", type="primary", use_container_width=True):
            st.session_state['show_full_suggestions'] = False
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()







    # ==== 2. PREVIOUS PLANS (Expandable) ====
    prev_plans = list_user_plans(username)
    if prev_plans:
        st.markdown("## 📜 Your Previous Study Plans")
        last_5_plans = prev_plans[:5]
        for i, (plan_file, label) in enumerate(last_5_plans):
            plan_obj = load_plan_from_file(username, plan_file)
            goal_name = plan_obj.get('main_goal', f"Plan {i+1}")
            with st.expander(f"{goal_name}", expanded=False):
                st.info(f"**Goal:** {plan_obj.get('main_goal','N/A')}\n\n**Hours:** {plan_obj.get('total_hours','-')}\n\n**Days:** {plan_obj.get('days_available','-')}")
                st.markdown("#### 📋 Tasks")
                for t in plan_obj.get('subtasks', []):
                    st.markdown(f"- **{t.get('task','(No task)')}** ({t.get('estimated_hours','-')}h)")
                st.markdown("#### 🎯 Milestones")
                for m in plan_obj.get('milestones', []):
                    st.markdown(f"{m.get('milestone','')} → {m.get('due_date','')}")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("🗑️ Delete This Plan", key=f"delete_{plan_file}"):
                        if delete_plan_file(username, plan_file):
                            st.session_state.reminder_manager.remove_all()
                            st.success("Plan deleted (and reminders cleared).")
                            st.rerun()
                with col2:
                    if st.button("🤖 Adapt Plan Based on Performance", key=f"adapt_{plan_file}"):
                        plan_topic = clean_string(plan_obj.get('main_goal', ''))
                        all_quizzes = st.session_state.performance_tracker.performance_data['quiz_scores']
                        quizzes = [
                            q for q in all_quizzes
                            if (
                                plan_topic in clean_string(q['topic']) or
                                clean_string(q['topic']) in plan_topic or
                                any(word in clean_string(q['topic']) for word in plan_topic.split() if len(word) > 3)
                            )
                        ]
                        if quizzes:
                            perf_data = {"quiz_scores": quizzes}
                            # Call your agent (returns a plain string)
                            adapted = st.session_state.planner.adapt_plan(plan_obj, perf_data)
                            # For overlay, always store as string for JSON parsing
                            if isinstance(adapted, dict):
                                st.session_state['full_suggestions'] = json.dumps(adapted)
                            else:
                                st.session_state['full_suggestions'] = adapted
                            st.session_state['show_full_suggestions'] = True
                            st.rerun()

                        else:
                            st.warning("No quizzes found matching this plan's topic. Complete some quizzes for this plan before adapting!")

                with col3:
                    if st.button("📄 Download PDF", key=f"pdf_{plan_file}"):
                        pdf_filename = plan_file.replace(".json", ".pdf")
                        pdf_path = export_plan_to_pdf(plan_obj, pdf_filename)
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                f"Download PDF: {pdf_filename}",
                                data=pdf_file.read(),
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )
                with col4:
                    if st.button("Set As Current Plan", key=f"set_{plan_file}"):
                        st.session_state.current_plan = plan_obj
                        st.success("Plan is now set as current. You can schedule reminders and manage tasks below.")
        st.markdown("---")
    else:
        st.info("No previous plans found for your account. Create a new study plan below! 👇")

    # ==== 3. NEW PLAN CREATION ====
    st.markdown("## ✍️ Create a New Study Plan")
    col1, col2 = st.columns(2)
    with col1:
        goal = st.text_input("📝 Goal", placeholder="Master Data Structures")
        deadline = st.date_input("📅 Deadline", datetime.now())
    with col2:
        daily_hours = st.slider("⏰ Daily Hours", 1, 10, 3)
        level = st.selectbox("📊 Level", ["beginner", "intermediate", "advanced"])

    if st.button("🚀 Generate Plan", type="primary", use_container_width=True):
        if not goal:
            st.error("⚠️ Enter a goal!")
        else:
            with st.spinner("🤖 Creating plan..."):
                plan = st.session_state.planner.create_study_plan(
                    goal=goal,
                    deadline=deadline.strftime("%Y-%m-%d"),
                    daily_hours=int(daily_hours),
                    current_knowledge=level,
                )
                if "error" not in plan:
                    fname = f"{username}_plan_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                    with open(f"data/user_data/{fname}", "w") as f:
                        json.dump(plan, f, indent=2)
                    st.session_state.current_plan = plan
                    st.balloons()
                    st.success("✅ Plan created and saved!")

    # ==== 4. CURRENT PLAN MANAGEMENT ====
    plan = st.session_state.get("current_plan")
    if plan:
        st.markdown("## 📖 Current Study Plan Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏰ Hours", plan.get('total_hours', 'N/A'))
        with col2:
            st.metric("📅 Days", plan.get('days_available', 'N/A'))
        with col3:
            st.metric("📋 Tasks", len(plan.get('subtasks', [])))

        st.markdown("### 📋 Study Tasks")
        for task in plan.get('subtasks', []):
            with st.expander(f"{task['task_id']}. {task['task']} ({task['estimated_hours']}h)"):
                st.write(f"**Priority:** {task['priority']}")
                st.write(f"**Description:** {task['description']}")
                if 'resources' in task and task['resources']:
                    st.write("**📚 Recommended Resources:**")
                    for resource in task['resources']:
                        st.write(f"- {resource}")

        st.markdown("### 🎯 Milestones")
        for m in plan.get('milestones', []):
            st.info(f"**{m['milestone']}** → {m['due_date']}")

        st.markdown("### ✔️ Plan Reminders")
        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("Set reminders\n(3 days before milestone)", key="rem_3day"):
                milestones = plan.get('milestones', [])
                reminders = []
                for m in milestones:
                    due = m.get('due_date')
                    desc = m.get('milestone')
                    if due and desc:
                        pre_dt = datetime.strptime(due, "%Y-%m-%d") - timedelta(days=3)
                        pre_dt = pre_dt.replace(hour=9, minute=0)
                        if pre_dt > datetime.now():
                            msg = f"Milestone in 3 days: {desc}"
                            st.session_state.reminder_manager.add_reminder(msg, pre_dt)
                            reminders.append({"message": msg, "datetime": pre_dt.isoformat()})
                st.session_state.scheduled_reminders = reminders
                st.session_state.reminder_manager.save_scheduled_reminders(username, reminders)
                st.success("Reminders set for 3 days before each milestone!")
        with colB:
            if st.button("Set reminders\n(1 day before milestone)", key="rem_1day"):
                milestones = plan.get('milestones', [])
                reminders = []
                for m in milestones:
                    due = m.get('due_date')
                    desc = m.get('milestone')
                    if due and desc:
                        pre_dt = datetime.strptime(due, "%Y-%m-%d") - timedelta(days=1)
                        pre_dt = pre_dt.replace(hour=9, minute=0)
                        if pre_dt > datetime.now():
                            msg = f"Milestone Tomorrow: {desc}"
                            st.session_state.reminder_manager.add_reminder(msg, pre_dt)
                            reminders.append({"message": msg, "datetime": pre_dt.isoformat()})
                st.session_state.scheduled_reminders = reminders
                st.session_state.reminder_manager.save_scheduled_reminders(username, reminders)
                st.success("Reminders set for 1 day before each milestone!")
        with colC:
            if st.button("Set reminders\n(on milestone day)", key="rem_on_day"):
                milestones = plan.get('milestones', [])
                reminders = []
                for m in milestones:
                    due = m.get('due_date')
                    desc = m.get('milestone')
                    if due and desc:
                        due_dt = datetime.strptime(due, "%Y-%m-%d").replace(hour=9, minute=0)
                        if due_dt > datetime.now():
                            msg = f"Milestone Today: {desc}"
                            st.session_state.reminder_manager.add_reminder(msg, due_dt)
                            reminders.append({"message": msg, "datetime": due_dt.isoformat()})
                st.session_state.scheduled_reminders = reminders
                st.session_state.reminder_manager.save_scheduled_reminders(username, reminders)
                st.success("Reminders set on the milestone day!")

        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            pdf_filename = f"{username}_plan_{datetime.now().strftime('%Y%m%d')}.pdf"
            pdf_path = export_plan_to_pdf(plan, pdf_filename)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    "📥 Download Plan as PDF",
                    data=pdf_file.read(),
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
        with colB:
            if st.button("✅ Add Tasks to My To-Do List", use_container_width=True):
                st.session_state.todo_manager.import_from_study_plan(plan)
                st.success("✅ Tasks added to My Tasks!")

        st.markdown("### 🤖 Adaptive Planning")
        if st.button("Adapt This Plan Based on Performance", key="adapt_btn_current"):
            plan_topic = clean_string(plan.get('main_goal', ''))
            all_quizzes = st.session_state.performance_tracker.performance_data['quiz_scores']
            quizzes = [
                q for q in all_quizzes
                if (
                    plan_topic in clean_string(q['topic']) or
                    clean_string(q['topic']) in plan_topic or
                    any(word in clean_string(q['topic']) for word in plan_topic.split() if len(word) > 3)
                )
            ]
            if quizzes:
                perf_data = {"quiz_scores": quizzes}
                adapted = st.session_state.planner.adapt_plan(plan, perf_data)
                st.session_state['full_suggestions'] = adapted
                st.session_state['show_full_suggestions'] = True
                st.rerun()
            else:
                st.warning("No quizzes found matching this plan's topic. Complete some quizzes for this plan before adapting!")

    else:
        st.info("📝 Generate a plan to see details and actions.")

# ============================================================================
# MY TASKS (FIXED - Added Manual Add Task)
# ============================================================================
elif page == "✅ My Tasks":
    st.title("✅ My Tasks")
    
    todo_mgr = st.session_state.todo_manager
    stats = todo_mgr.get_completion_stats()
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Total", stats['total'])
    with col2:
        st.metric("✅ Done", stats['completed'])
    with col3:
        st.metric("⏳ Pending", stats['pending'])
    
    st.progress(stats['percentage']/100, text=f"Progress: {stats['percentage']}%")
    
    st.markdown("---")
    
    # Add Manual Task
    with st.expander("➕ Add New Task Manually"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_task_name = st.text_input("Task Name", placeholder="e.g., Review Chapter 5")
        with col2:
            new_task_hours = st.number_input("Estimated Hours", 1, 20, 2)
        with col3:
            new_task_priority = st.selectbox("Priority", ["high", "medium", "low"])
        
        if st.button("➕ Add Task", use_container_width=True):
            if new_task_name:
                todo_mgr.add_task(new_task_name, new_task_hours, new_task_priority)
                st.success(f"✅ Added: {new_task_name}")
                st.rerun()
    
    st.markdown("---")
    
    # Pending tasks
    st.subheader("⏳ Pending Tasks")
    pending = todo_mgr.get_pending_tasks()

    if pending:
        for task in pending:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"""
                <div class="todo-item">
                    <b>{task['name']}</b><br>
                    <small>⏰ {task['estimated_hours']}h | Priority: {task['priority']}</small>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✓", key=f"complete_{task['id']}"):
                    todo_mgr.complete_task(task['id'])
                    st.session_state.performance_tracker.record_task_completion(
                        task['id'],
                        task['name'],
                        task['estimated_hours']
                    )
                    st.success(f"✅ Completed!")
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{task['id']}"):
                    todo_mgr.delete_task(task['id'])
                    st.success(f"🗑️ Deleted!")
                    st.rerun()
    else:
        st.info("No pending tasks!")

    
    # Completed tasks
    st.markdown("---")
    with st.expander("✅ Completed Tasks"):
        completed = todo_mgr.get_completed_tasks()
        if completed:
            for task in completed:
                st.success(f"✓ {task['name']} ({task['estimated_hours']}h)")
        else:
            st.info("No completed tasks yet")


# ============================================================================
# ASK QUESTIONS (FIXED - Added Chat History)
# ============================================================================
elif page == "💬 Ask Questions":
    st.title("💬 AI Assistant")
    
    if st.session_state.concept_agent is None:
        st.warning("⚠️ Upload material first!")
    else:
        st.success("✅ Ready to answer!")
        
        question = st.text_input("🤔 Your Question:", placeholder="What is...?")
        
        if st.button("Ask", type="primary") and question:
            with st.spinner("🤖 Thinking..."):
                answer = st.session_state.concept_agent.explain_concept(question)
            
            st.markdown("### 📝 Answer:")
            st.markdown(f"> {answer}")
        
        # Chat History
        if hasattr(st.session_state.concept_agent, 'chat_history'):
            history = st.session_state.concept_agent.chat_history
            if history:
                st.markdown("---")
                st.markdown("### 💬 Recent Conversations")
                for i, chat in enumerate(reversed(history[-5:]), 1):
                    with st.expander(f"Q{i}: {chat['question'][:60]}..."):
                        st.markdown(f"**Question:** {chat['question']}")
                        st.markdown(f"**Answer:** {chat['answer']}")


# ============================================================================
# TAKE QUIZ (FIXED - Reset after submission)
# ============================================================================
# ============================================================================
# TAKE QUIZ - FIXED VERSION
# ============================================================================
elif page == "📝 Take Quiz":
    st.title("📝 Auto-Generated Quiz")

    if st.session_state.quiz_generator is None:
        st.warning("⚠️ Upload material first!")
    else:
        # Initialization for quiz submitted state
        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False

        # Show quiz generation form
        if st.session_state.current_quiz is None:
            st.markdown("### 🎯 Generate New Quiz")
            col1, col2, col3 = st.columns(3)
            with col1:
                topic = st.text_input("📚 Topic", placeholder="e.g., Machine Learning")
            with col2:
                num_q = st.number_input("Questions", 3, 10, 5)
            with col3:
                difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])

            if st.button("Generate Quiz", type="primary", use_container_width=True):
                if topic:
                    with st.spinner("Creating quiz..."):
                        quiz = st.session_state.quiz_generator.generate_quiz(topic, num_q, difficulty)
                        if "error" not in quiz:
                            st.session_state.current_quiz = quiz
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_submitted = False
                            st.rerun()
                else:
                    st.error("⚠️ Enter a topic!")

        # Show quiz questions (if not submitted)
        elif not st.session_state.quiz_submitted:
            quiz = st.session_state.current_quiz
            st.success(f"📝 Quiz: {quiz['topic']} ({quiz['difficulty']})")

            for q in quiz['questions']:
                st.markdown(f"**Question {q['id']}:** {q['question']}")
                answer = st.radio(
                    f"Select answer:",
                    options=list(q['options'].keys()),
                    format_func=lambda x: f"{x}: {q['options'][x]}",
                    key=f"q_{q['id']}",
                    label_visibility="collapsed"
                )
                st.session_state.quiz_answers[q['id']] = answer
                st.markdown("---")

            # Prevent double save with state guard
            if st.button("✅ Submit Quiz", type="primary", use_container_width=True) and not st.session_state.quiz_submitted:
                st.session_state.quiz_submitted = True
                st.rerun()

        # Show quiz results (after submission)
        else:
            quiz = st.session_state.current_quiz

            # Calculate score
            score = sum(1 for q in quiz['questions'] 
                        if st.session_state.quiz_answers.get(q['id']) == q['correct_answer'])
            total = len(quiz['questions'])
            percentage = (score / total) * 100

            st.markdown("### 📊 Quiz Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{score}/{total}")
            with col2:
                st.metric("Percentage", f"{percentage}%")
            with col3:
                if percentage >= 70:
                    st.metric("Status", "✅ Pass", delta="Good!")
                else:
                    st.metric("Status", "⚠️ Review", delta="Keep trying!")

            # Only save result if not already recorded in this view
            if "quiz_result_saved" not in st.session_state or not st.session_state.quiz_result_saved:
                st.session_state.performance_tracker.record_quiz_score(
                    quiz['topic'], score, total
                )
                st.session_state.quiz_result_saved = True
                st.success("✅ Results saved to Performance Dashboard!")

            # Reset quiz_result_saved when starting a new quiz
            if st.session_state.current_quiz is None:
                st.session_state.quiz_result_saved = False

            # Show detailed answers
            st.markdown("---")
            st.markdown("### 📖 Detailed Answers")
            for q in quiz['questions']:
                user = st.session_state.quiz_answers.get(q['id'])
                correct = q['correct_answer']

                if user == correct:
                    st.success(f"**Q{q['id']}: {q['question']}**")
                    st.write(f"✅ Your answer: **{user}** - {q['options'][user]}")
                else:
                    st.error(f"**Q{q['id']}: {q['question']}**")
                    st.write(f"❌ Your answer: **{user}** - {q['options'][user]}")
                    st.write(f"✅ Correct answer: **{correct}** - {q['options'][correct]}")
                st.info(f"💡 **Explanation:** {q['explanation']}")
                st.markdown("---")

            # Reset button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_result_saved = False
                    st.rerun()
            with col2:
                if st.button("📊 View Performance", use_container_width=True):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_result_saved = False


# ============================================================================
# PERFORMANCE
# ============================================================================
elif page == "📊 Performance":
    st.title("📊 Your Performance")
    
    tracker = st.session_state.performance_tracker
    report = tracker.generate_performance_report(total_tasks=10)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 Quizzes", report['total_quizzes'])
    with col2:
        comp = report['completion_stats']
        st.metric("✅ Tasks", f"{comp['completed']}/{comp['total']}")
    with col3:
        st.metric("⚠️ Weak", len(report['weak_topics']))
    
    rate = report['completion_stats']['completion_rate']
    st.progress(rate/100, text=f"{rate}%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Quiz Performance")
        topic_perf = report['quiz_performance']
        if topic_perf:
            df = pd.DataFrame([
                {"Topic": t, "Score": d['average_score']}
                for t, d in topic_perf.items()
            ])
            st.bar_chart(df.set_index("Topic"))
        else:
            st.info("Take quizzes to see data!")
    
    with col2:
        st.markdown("### ⚠️ Focus On")
        weak = report['weak_topics']
        if weak:
            for topic in weak:
                st.error(f"❌ {topic}")
        else:
            st.success("🎉 All good!")
    
    st.markdown("---")
    st.markdown("### 💡 Recommendations")
    for i, rec in enumerate(report['recommendations'], 1):
        st.info(f"{i}. {rec}")


# ============================================================================
# REMINDERS
# ============================================================================
elif page == "⏰ Reminders":
    st.title("⏰ Reminders")
    
    st.markdown("### 📋 Active Reminders")
    jobs = st.session_state.reminder_manager.scheduler.get_jobs()
    
    if jobs:
        for job in jobs:
            task = job.args[0] if job.args else "Task"
            next_run = job.next_run_time
            
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"🔔 {task}")
            with col2:
                st.caption(f"{next_run}")
            with col3:
                if st.button("🗑️", key=f"del_{job.id}"):
                    job.remove()
                    st.rerun()
    else:
        st.info("No reminders")
    
    st.markdown("---")
    st.markdown("### ➕ New Reminder")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        task = st.text_input("📝 Task")
    with col2:
        date = st.date_input("📅 Date")
    with col3:
        time = st.time_input("⏰ Time")
    
    if st.button("🔔 Set", type="primary", use_container_width=True):
        if task:
            dt = datetime.combine(date, time)
            st.session_state.reminder_manager.add_reminder(
                task, dt, lambda t: print(f"🛎️ {t}")
            )
            st.success("✅ Reminder set!")
            st.rerun()
