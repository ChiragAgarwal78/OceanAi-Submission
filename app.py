import streamlit as st
import pandas as pd
import json
from backend import EmailAgent

# 1. SETUP
st.set_page_config(page_title="EMAIL AGENT", layout="wide", initial_sidebar_state="collapsed")

if 'agent' not in st.session_state: st.session_state.agent = EmailAgent()
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True
if 'saved_drafts' not in st.session_state: st.session_state.saved_drafts = [] # Store drafts

# 2. STYLING ENGINE
def inject_css(is_dark):
    bg, text, border = "#000000", "#FFFFFF", "#333333"
    inv_bg, inv_text = "#FFFFFF", "#000000"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
        .stApp {{ background-color: {bg}; color: {text}; font-family: 'Inter', sans-serif; }}
        .block-container {{ max_width: 1200px !important; padding-top: 2rem; }}
        h1, h2, h3, p, div, label, li, span {{ color: {text} !important; }}
        h1, h2, h3 {{ text-transform: uppercase; font-weight: 900 !important; margin: 0; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 2px; background-color: {bg}; border-bottom: 2px solid {border}; }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px; background-color: {bg}; border: 1px solid {border}; border-bottom: none;
            color: {text}; border-radius: 0px; font-weight: 700; text-transform: uppercase; flex: 1;
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: {inv_bg} !important; color: {inv_text} !important; border: none;
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] p {{ color: {inv_text} !important; }}
        .stTabs [data-baseweb="tab-highlight"] {{ display: none; }} 
        .stTextInput>div>div, .stTextArea>div>div, .stSelectbox>div>div {{
            background-color: {bg}; color: {text}; border: 2px solid {border}; border-radius: 0px;
        }}
        .stTextInput>div>div:focus-within, .stTextArea>div>div:focus-within {{
            border-color: {text} !important; box-shadow: none !important;
        }}
        .stButton>button {{
            background-color: {bg}; color: {text}; border: 2px solid {border};
            border-radius: 0px; text-transform: uppercase; font-weight: 700; width: 100%;
        }}
        .stButton>button:hover {{ border-color: {text}; background-color: {border}; }}
        div[data-testid="stDataFrame"] {{ border: 2px solid {border}; }}
        #MainMenu, footer, header {{ visibility: hidden; }}
        .stProgress > div > div > div > div {{ background-color: {inv_bg} !important; }}
    </style>
    """, unsafe_allow_html=True)

inject_css(st.session_state.dark_mode)

# 3. HEADER
c1, c2 = st.columns([8, 2])
with c1: 
    st.markdown("<h1>WE'RE GOOD.</h1>", unsafe_allow_html=True)
    st.caption("INTELLIGENT EMAIL AGENT - by Chirag Agarwal")
st.markdown("---")

# 4. TABS
t1, t2, t3, t4 = st.tabs(["GUIDE", "INBOX", "CHAT", "SETTINGS"])

# TAB 1: GUIDE
with t1:
    st.subheader("SYSTEM OPERATIONS")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("### 1. INGEST\nView emails in **INBOX**. Upload custom JSON in **SETTINGS**.")
    with c2: st.markdown("### 2. BRAIN\nPowered by **Local Ollama**. Edit logic rules in **SETTINGS**.")
    with c3: st.markdown("### 3. ACTION\nUse **'Auto-Categorize'** or ask the **CHAT** agent to draft replies.")

# TAB 2: INBOX
with t2:
    c1, c2 = st.columns([3, 1])
    with c1: st.subheader("CURRENT MESSAGES")
    with c2: 
        if st.button("RUN AUTO-CATEGORIZATION"):
            emails = st.session_state.agent.emails
            bar = st.progress(0)
            for i, email in enumerate(emails):
                email['category'] = st.session_state.agent.process_with_ollama("categorization", f"Subject: {email['subject']}\nBody: {email['body']}")
                bar.progress((i+1)/len(emails))
            st.rerun()

    df = pd.DataFrame(st.session_state.agent.emails)
    if not df.empty:
        st.dataframe(df[['category', 'sender', 'subject']], use_container_width=True, hide_index=True)
    else:
        st.info("NO EMAILS FOUND. PLEASE IMPORT DATA IN SETTINGS.")

# TAB 3: CHAT
with t3:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("CONTEXT")
        ids = [e['id'] for e in st.session_state.agent.emails]
        if ids:
            sel_id = st.selectbox("SELECT ID", ids, label_visibility="collapsed")
            email = next(e for e in st.session_state.agent.emails if e['id'] == sel_id)
            st.markdown(f"<div style='border:1px solid #333; padding:10px; margin-bottom:10px;'><b>{email['sender']}</b><br>{email['subject']}</div>", unsafe_allow_html=True)
            with st.expander("VIEW BODY"): st.write(email['body'])
            
            # SHOW SAVED DRAFTS FOR THIS EMAIL
            related_drafts = [d for d in st.session_state.saved_drafts if d['id'] == sel_id]
            if related_drafts:
                st.markdown("---")
                st.caption(f"SAVED DRAFTS ({len(related_drafts)})")
                for d in related_drafts:
                    st.text_area("Draft", d['content'], height=100, key=f"d_{d['timestamp']}")

    with c2:
        st.subheader("COMMAND")
        prompt = st.chat_input("Ex: 'Draft reply', 'Extract tasks', 'Summarize'...")
        
        # Initialize session state for last response to allow saving
        if 'last_response' not in st.session_state: st.session_state.last_response = None
        
        if prompt and ids:
            ptype = "auto_reply" if "reply" in prompt.lower() else "action_extraction" if "task" in prompt.lower() else "general"
            with st.spinner("PROCESSING..."):
                res = st.session_state.agent.process_with_ollama(ptype, email['body'], prompt)
                st.session_state.last_response = {"text": res, "type": ptype, "email_id": sel_id}
        
        # Display Agent Response
        if st.session_state.last_response:
            st.markdown(f"<div style='border-left:4px solid #fff; padding-left:10px; margin-top:10px;'><b>AGENT:</b><br>{st.session_state.last_response['text']}</div>", unsafe_allow_html=True)
            
            # SAVE DRAFT BUTTON (Requirement: Store drafts)
            if st.session_state.last_response['type'] == 'auto_reply':
                if st.button("SAVE AS DRAFT"):
                    import time
                    st.session_state.saved_drafts.append({
                        "id": st.session_state.last_response['email_id'],
                        "content": st.session_state.last_response['text'],
                        "timestamp": time.time()
                    })
                    st.toast("DRAFT SAVED")
                    st.rerun()

# TAB 4: SETTINGS
with t4:
    st.subheader("CONFIGURATION")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<b>DATA SOURCE</b>", unsafe_allow_html=True)
        count = len(st.session_state.agent.emails)
        st.caption(f"CURRENTLY LOADED: {count} EMAILS")
        
        if st.button("RESET TO DEFAULT INBOX"):
            st.session_state.agent.emails = st.session_state.agent.load_json('data/mock_inbox.json')
            st.toast("RESET TO DEFAULT DATA")
            st.rerun()
        st.write("")
        up = st.file_uploader("UPLOAD CUSTOM JSON", type="json")
        if up: 
            try:
                new_data = json.load(up)
                if st.session_state.agent.import_emails(new_data): 
                    st.toast(f"SUCCESS! LOADED {len(new_data)} EMAILS")
                    import time; time.sleep(1); st.rerun()
                else: st.error("Invalid JSON format.")
            except: st.error("File is not valid JSON.")

    with c2:
        st.markdown("<b>BRAIN RULES</b>", unsafe_allow_html=True)
        p = st.session_state.agent.prompts
        cat = st.text_area("CATEGORIZATION RULE", p.get("categorization",""))
        rep = st.text_area("REPLY STYLE", p.get("auto_reply",""))
        gen = st.text_area("GENERAL ANALYSIS RULE", p.get("general",""))
        if st.button("SAVE RULES"):
            st.session_state.agent.save_prompts({**p, "categorization": cat, "auto_reply": rep, "general": gen})
            st.toast("RULES SAVED")