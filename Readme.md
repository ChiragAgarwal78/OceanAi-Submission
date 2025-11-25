# Prompt-Driven Email Productivity Agent

## Overview
A local, privacy-first AI agent that categorizes emails, extracts tasks, and drafts replies using **Ollama (Llama 3.2)**. It features a custom high-contrast UI and a completely prompt-driven architecture.

## Setup Instructions
1. **Prerequisites:**
   - Install Python 3.8+
   - Install [Ollama](https://ollama.com/) and run `ollama pull llama3.2`
2. **Installation:**
   ```bash
   pip install -r requirements.txt

3. **Run App**
   ```bash 
   streamlit run app.py

Features
Inbox Ingestion: Loads mock data or custom JSON.

Prompt-Driven Brain: Edit agent behavior (Reply Style, Categorization Rules) in Settings.

Local Privacy: No data leaves your machine.