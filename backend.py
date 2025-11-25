import os
import json
import ollama
import re

class EmailAgent:
    def __init__(self):
        self.emails_path = 'data/mock_inbox.json'
        self.prompts_path = 'data/prompts.json'
        self.model_name = "llama3.2" 
        
        self.emails = self.load_json(self.emails_path)
        self.prompts = self.load_json(self.prompts_path)

        # BACKFILL MISSING KEYS
        defaults = {
            "categorization": "Classify into exactly one: [Work, Personal, Newsletter, Security, Spam]. Return ONLY the word.",
            "auto_reply": "Draft a professional, concise reply.",
            # UPDATED: More conversational default
            "general": "Answer the user's question clearly and helpfully based on the email content."
        }
        
        updated = False
        for key, value in defaults.items():
            if key not in self.prompts:
                self.prompts[key] = value
                updated = True
        
        if updated:
            self.save_prompts(self.prompts)

    def load_json(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f: return json.load(f)
        return []

    def import_emails(self, json_data):
        if isinstance(json_data, list) and len(json_data) > 0:
            required_keys = {'id', 'sender', 'subject', 'body'}
            if required_keys.issubset(json_data[0].keys()):
                self.emails = json_data
                return True
        return False

    def save_prompts(self, new_prompts):
        self.prompts = new_prompts
        with open(self.prompts_path, 'w') as f:
            json.dump(new_prompts, f, indent=4)

    def process_with_ollama(self, prompt_key, email_content, user_command=""):
        system_rule = self.prompts.get(prompt_key, "")
        
        if not email_content or not email_content.strip() or len(email_content) < 10:
             email_content = "[CONTENT EMPTY OR TOO SHORT]"

        full_prompt = f"""
        You are an intelligent email processor.
        
        STRICT INSTRUCTIONS:
        1. Do NOT write Python code.
        2. If categorizing, pick exactly one category from the rule list.
        3. If the info is not found, state "Not Found".
        
        GUIDING RULE: {system_rule}

        USER COMMAND: {user_command}

        EMAIL CONTENT:
        {email_content}
        """
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': full_prompt},
            ])
            text = response['message']['content'].strip()
            
            # --- INTELLIGENT SANITIZATION ---
            
            # ONLY clean up output for "Categorization" tasks.
            # We want "General" and "Reply" to have punctuation and sentences!
            if prompt_key == "categorization":
                # Remove brackets and quotes
                text = re.sub(r'[\[\]\."\']', '', text).strip()
                # Remove label prefixes like "Category:"
                text = text.replace("Category:", "").strip()
                
                # If the AI outputs a whole sentence (hallucination), force Uncertain
                if len(text.split()) > 3:
                    return "Uncertain"
                
                text = text.title()
                
            return text
        except Exception as e:
            return f"Error: {str(e)}"