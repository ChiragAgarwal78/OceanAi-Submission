import streamlit as st
import pandas as pd
from backend import EmailAgent

# Page Config
st.set_page_config(page_title="Local Email Agent", layout="wide")

# Initialize Backend
if 'agent' not in st.session_state:
    st.session_state.agent = EmailAgent()

st.title("📧 Local Prompt-Driven Email Agent")

# --- SIDEBAR: PROMPT BRAIN ---
st.sidebar.header("🧠 Agent Brain")
st.sidebar.info("Edit these prompts to change how your local AI behaves.")

current_prompts = st.session_state.agent.prompts

# Text Areas for editing prompts
cat_prompt = st.sidebar.text_area("Categorization Rules", current_prompts.get("categorization", ""), height=100)
reply_prompt = st.sidebar.text_area("Auto-Reply Style", current_prompts.get("auto_reply", ""), height=100)
act_prompt = st.sidebar.text_area("Action Extraction Rules", current_prompts.get("action_extraction", ""), height=100)

if st.sidebar.button("💾 Save Configuration"):
    new_prompts = {
        "categorization": cat_prompt,
        "auto_reply": reply_prompt,
        "action_extraction": act_prompt
    }
    st.session_state.agent.save_prompts(new_prompts)
    st.sidebar.success("Agent Brain Updated!")

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["📥 Inbox", "🤖 Agent Chat", "📝 Drafts"])

# --- TAB 1: INBOX VIEW ---
with tab1:
    st.subheader("Inbox Processing")
    emails = st.session_state.agent.emails
    
    # Auto-Categorize Button
    if st.button("🚀 Auto-Categorize Inbox (Local AI)"):
        progress_bar = st.progress(0)
        status = st.empty()
        
        for i, email in enumerate(emails):
            status.text(f"Processing email {i+1}/{len(emails)}...")
            
            # Call Ollama
            category = st.session_state.agent.process_with_ollama(
                "categorization", 
                f"Subject: {email['subject']}\nBody: {email['body']}"
            )
            
            email['category'] = category
            progress_bar.progress((i + 1) / len(emails))
        
        status.success("Categorization Complete!")
        st.rerun()

    # Data Table
    df = pd.DataFrame(emails)
    st.dataframe(df[['sender', 'subject', 'category']], use_container_width=True, hide_index=True)

# --- TAB 2: AGENT CHAT ---
with tab2:
    st.subheader("Chat with your Email")
    
    # Context Selector
    email_ids = [e['id'] for e in st.session_state.agent.emails]
    selected_id = st.selectbox("Select Email Context:", email_ids)
    
    selected_email = next(e for e in st.session_state.agent.emails if e['id'] == selected_id)
    
    with st.expander("View Email Content", expanded=True):
        st.markdown(f"**Subject:** {selected_email['subject']}")
        st.markdown(f"**Body:** {selected_email['body']}")

    # Chat Input
    user_query = st.chat_input("Ask: 'Draft a reply', 'Extract tasks'...")
    
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
            
        with st.chat_message("assistant"):
            with st.spinner("Ollama is thinking..."):
                # Determine which prompt to use
                prompt_type = "categorization" # Default
                if "reply" in user_query.lower() or "draft" in user_query.lower():
                    prompt_type = "auto_reply"
                elif "task" in user_query.lower():
                    prompt_type = "action_extraction"
                
                # Call Ollama
                response = st.session_state.agent.process_with_ollama(
                    prompt_type,
                    selected_email['body'],
                    extra_instruction=user_query
                )
                st.write(response)
                
                # Save draft logic
                if "reply" in user_query.lower():
                    st.session_state['last_draft'] = response

# --- TAB 3: DRAFTS ---
with tab3:
    st.subheader("Generated Drafts")
    if 'last_draft' in st.session_state:
        st.info("Drafts are saved locally. No emails are sent.")
        st.text_area("Latest Draft", st.session_state['last_draft'], height=200)
    else:
        st.write("No drafts generated yet.")