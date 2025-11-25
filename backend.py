import os
import json
import ollama

class EmailAgent:
    def __init__(self):
        self.emails_path = 'data/mock_inbox.json'
        self.prompts_path = 'data/prompts.json'
        
        # IMPORTANT: Change this if you downloaded a different model (e.g., "llama3", "mistral")
        self.model_name = "llama3.2" 
        
        # Load Data
        self.emails = self.load_json(self.emails_path)
        self.prompts = self.load_json(self.prompts_path)

    def load_json(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return []

    def save_prompts(self, new_prompts):
        """Updates the agent's 'brain' based on UI edits"""
        self.prompts = new_prompts
        with open(self.prompts_path, 'w') as f:
            json.dump(new_prompts, f, indent=4)

    def process_with_ollama(self, prompt_key, email_content, extra_instruction=""):
        """
        Sends data to the local Ollama model.
        """
        # 1. Fetch the relevant prompt from our JSON 'Brain'
        system_instruction = self.prompts.get(prompt_key, "")
        
        # 2. Build the message
        prompt = f"""
        SYSTEM INSTRUCTION: {system_instruction}
        
        USER REQUEST: {extra_instruction}
        
        EMAIL CONTENT:
        {email_content}
        """
        
        try:
            # 3. Call local API
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content'].strip()
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}. Is the app running?"