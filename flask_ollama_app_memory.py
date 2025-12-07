from flask import Flask, request, jsonify, render_template, stream_with_context, Response
import ollama
import json
import os
from datetime import datetime

app = Flask(__name__)

# ==========================================
# Core Memory Manager
# ==========================================

# Configuration
DEFAULT_MODEL = "gemma3:4b"
# File to store persistent memory
MEMORY_FILE = "memory_data.json"

class MemoryManager:
    def __init__(self):
        self.active_context = []
        self.long_term_summary = {
            "topics": {},  # Dictionary: {"TopicName": "Summary...", ...}
            "request_history": "None"
        }
        self.last_interaction = None
        self.load_memory()
    
    def load_memory(self):
        """Load state from JSON file if exists."""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_context = data.get("short_term_memory", [])
                    
                    lt = data.get("long_term_memory", {})
                    # Migration: if old "persona" string exists, move it to "General" topic
                    if "persona" in lt and isinstance(lt["persona"], str) and lt["persona"] != "Unknown":
                        self.long_term_summary["topics"] = {"General": lt["persona"]}
                    else:
                        self.long_term_summary["topics"] = lt.get("topics", {})
                        
                    self.long_term_summary["request_history"] = lt.get("request_history", "None")
                    
                    last_ts = data.get("last_interaction")
                    if last_ts:
                        self.last_interaction = datetime.fromisoformat(last_ts)
                        
                print(f"📂 Loaded memory from {MEMORY_FILE}")
            except Exception as e:
                print(f"⚠️ Failed to load memory: {e}")

    def save_memory(self):
        """Save current state to JSON file."""
        data = {
            "long_term_memory": self.long_term_summary,
            "short_term_memory": self.active_context,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None
        }
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Memory saved to {MEMORY_FILE}")
        except Exception as e:
            print(f"❌ Failed to save memory: {e}")

    def add_message(self, role, content, model=None):
        # If User message and model provided, check for topic shift
        if role == 'user' and model and len(self.active_context) > 0:
            if self.detect_topic_shift(content, model):
                print("🔄 Topic Shift Detected! Flushing memory...")
                self.force_flush(model)
        
        self.active_context.append({"role": role, "content": content})
        self.last_interaction = datetime.now()
        self.save_memory()

    def detect_topic_shift(self, new_content, model):
        """
        Ask LLM if new_content is a shift from active_context.
        """
        # Take last 3 messages for context
        recent = self.active_context[-3:]
        context_text = ""
        for m in recent:
            context_text += f"{m['role']}: {m['content']}\n"
            
        prompt = (
            "You are a conversation flow analyzer.\n"
            f"=== CONTEXT ===\n{context_text}\n"
            f"=== NEW MESSAGE ===\nuser: {new_content}\n\n"
            "TASK: Is the NEW MESSAGE introducing a completely different topic compared to the CONTEXT? "
            "(e.g. switching from coding to cooking, or family to work).\n"
            "Answer ONLY 'YES' or 'NO'."
        )
        
        try:
            resp = ollama.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
            ans = resp.get("message", {}).get("content", "").strip().upper()
            return "YES" in ans
        except:
            return False

    def force_flush(self, model):
        """
        Summarize ALL active context immediately and clear it.
        """
        if not self.active_context: return
        self._update_summary(self.active_context, model)
        self.active_context = []
        self.save_memory()


    def get_time_ago(self):
        if not self.last_interaction:
            return "a long time"
        
        delta = datetime.now() - self.last_interaction
        seconds = delta.total_seconds()
        
        if seconds < 60: return "just a moment"
        if seconds < 3600: return f"{int(seconds // 60)} minutes"
        if seconds < 86400: return f"{int(seconds // 3600)} hours"
        return f"{int(seconds // 86400)} days"

    def process_memory(self, window_size: int, model: str):
        """
        Check if active_context exceeds window_size.
        If so, take the overflow, summarize it, and append to long_term_summary.
        """
        max_msgs = window_size * 2 
        
        if len(self.active_context) > max_msgs:
            # We need to prune
            num_to_prune = len(self.active_context) - max_msgs
            to_be_summarized = self.active_context[:num_to_prune]
            self.active_context = self.active_context[num_to_prune:]
            
            # Perform Summarization
            self._update_summary(to_be_summarized, model)
            
            # Save after pruning
            self.save_memory()

    def _update_summary(self, messages, model):
        """
        Ask LLM to summarize messages into a specific TOPIC bucket.
        """
        print(f"🧠 Summarizing {len(messages)} messages (Topic Routing)...")
        
        conversation_text = ""
        for m in messages:
            role = "User" if m['role'] == 'user' else "AI"
            conversation_text += f"{role}: {m['content']}\n"
            
        current_topics = ", ".join(self.long_term_summary['topics'].keys())
        
        prompt = (
            "You are a memory manager. Compress this conversation into long-term memory.\n"
            f"=== EXISTING TOPICS ===\n{current_topics}\n"
            f"=== CONVERSATION ===\n{conversation_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. Identify the PRIMARY TOPIC of this conversation (e.g., Coding, Family, Health, Travel). Use an existing one if it fits, or name a new one.\n"
            "2. Summarize key facts/events relevant to that topic.\n"
            "3. Update the 'History' log with a 1-line summary of the user's request.\n"
            "4. FORMAT:\n"
            "TOPIC: [Topic Name]\n"
            "SUMMARY: [New facts to append to this topic]\n"
            "HISTORY: [1-line request summary]"
        )
        
        try:
            resp = ollama.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
            raw_output = resp.get("message", {}).get("content", "")
            
            # Parsing
            topic_name = "General"
            summary_text = ""
            history_text = ""
            
            lines = raw_output.split('\n')
            for line in lines:
                if line.startswith("TOPIC:"):
                    topic_name = line.replace("TOPIC:", "").strip()
                elif line.startswith("SUMMARY:"):
                    summary_text = line.replace("SUMMARY:", "").strip()
                elif line.startswith("HISTORY:"):
                    history_text = line.replace("HISTORY:", "").strip()
            
            # Fallback for multiline summary (simple heuristic or regex is better, but this suffices for demo)
            # A better parser would split by tokens. Let's do a reliable split.
            if "TOPIC:" in raw_output and "SUMMARY:" in raw_output:
                # Robust split
                parts = raw_output.split("SUMMARY:")
                topic_part = parts[0].replace("TOPIC:", "").strip()
                rem = parts[1]
                
                if "HISTORY:" in rem:
                    parts2 = rem.split("HISTORY:")
                    summary_part = parts2[0].strip()
                    history_part = parts2[1].strip()
                else:
                    summary_part = rem.strip()
                    history_part = "Conversation about " + topic_part
                
                if topic_part: topic_name = topic_part
                if summary_part: summary_text = summary_part
                if history_part: history_text = history_part
                
                # Update Topic
                old_summary = self.long_term_summary['topics'].get(topic_name, "")
                if old_summary:
                    self.long_term_summary['topics'][topic_name] = old_summary + "; " + summary_text
                else:
                    self.long_term_summary['topics'][topic_name] = summary_text
                    
                # Update History
                self.long_term_summary['request_history'] = self.long_term_summary.get('request_history', "") + "\n" + history_text
                
                print(f"✅ Summary Updated. Topic: {topic_name}")
                self.save_memory()
            else:
                print("⚠️ Summary Parsing Failed. Raw output:\n" + raw_output)
                
        except Exception as e:
            print(f"❌ Summary fail: {e}")

    def update_persona_only(self, model):
        """
        Special check: Onboarding check.
        If we have NO topics yet, try to extract basic info.
        """
        # Only run if we have 0 topics
        if len(self.long_term_summary['topics']) > 0:
            return

        print("🕵️‍♂️ Checking for Intro in active context...")
        conversation_text = ""
        for m in self.active_context:
            role = "User" if m['role'] == 'user' else "AI"
            conversation_text += f"{role}: {m['content']}\n"

        prompt = (
            "Analyze the conversation. Has the user provided their name, profession, or interests?\n"
            f"=== CONVERSATION ===\n{conversation_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. If YES, extract a concise summary (e.g., 'Alice, Baker').\n"
            "2. If NO (or if they just said 'Hi'), return 'Unknown'.\n"
            "3. FORMAT: Output ONLY the summary string."
        )

        try:
            resp = ollama.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
            result = resp.get("message", {}).get("content", "").strip()
            
            if result and "Unknown" not in result and len(result) < 50:
                print(f"🎯 Intro Discovered: {result}")
                self.long_term_summary['topics']['Personal'] = result
                self.save_memory()
            else:
                print("🤷‍♂️ No intro found yet.")
                
        except Exception as e:
            print(f"❌ Intro check fail: {e}")

    def get_context_for_llm(self):
        """
        Constructs messages. Swaps prompts based on emptiness of 'topics'.
        """
        topics = self.long_term_summary['topics']
        history = self.long_term_summary['request_history']
        
        if len(topics) == 0:
            # ONBOARDING PROMPT
            system_content = (
                "You are an empathetic AI Therapist interacting with a new client.\n"
                "Your goal is to establish a comfortable rapport and learn a little about them.\n"
                "INSTRUCTION: Ask a GENTLE, SHORT question (max 15 words) to politely encourage them to share their name or current state of mind.\n"
                "Do NOT force them to answer. Be warm and inviting."
            )
        else:
            # Format Topics
            knowledge_graph = ""
            for t, content in topics.items():
                knowledge_graph += f"[{t}]: {content}\n"
            
            # NORMAL PROMPT
            system_content = (
                "You are an empathetic, professional AI Therapist.\n\n"
                "=== PATIENT FILE ===\n"
                f"{knowledge_graph}\n"
                f"[Session History]: {history}\n\n"
                "=== GUIDELINES ===\n"
                "1. CONTINUITY: If 'Session History' is not empty, explicitly try to recall or check in on a previous topic if relevant.\n"
                "2. EMPATHY: Be supportive, non-judgmental, and concise.\n"
                "3. PERSONA: Tailor advice based on the 'Patient File' knowledge.\n"
                "4. DO NOT INTERROGATE: Avoid asking too many questions at once.\n"
                "Use the provided context to guide the session naturally."
            )
            
        messages = [{"role": "system", "content": system_content}]
        messages.extend(self.active_context)
        return messages

    def get_status(self):
        return {
            "current_summary": self.long_term_summary,
            "active_window": self.active_context,
            "active_count": len(self.active_context)
        }

    def reset(self):
        self.active_context = []
        self.long_term_summary = {
            "topics": {},
            "request_history": "None"
        }
        self.last_interaction = None
        self.save_memory()
memory = MemoryManager()


# ==========================================
# Routes
# ==========================================

@app.route('/')
def home():
    return render_template('index_memory.html')

@app.route('/api/chat_memory', methods=['POST'])
def api_chat_memory():
    data = request.json
    user_input = data.get('message', '')
    memory_length = int(data.get('memory_length', 3))
    model = data.get('model', DEFAULT_MODEL) # Use Global Config

    if not user_input:
        return jsonify({'error': 'No input provided'}), 400

    # 1. Add User Message to Memory (Triggers Topic Check)
    memory.add_message('user', user_input, model=model)

    def generate():
        # 2a. Prune/Update active context based on window size
        #    Note: Ideally we'd do this *before* generating, but we can do it here.
        #    Wait, prune active context happens in process_memory usually *after* adding. 
        #    Let's ensure we are clean. 
        #    The original code called process_memory BEFORE generation to ensure prompt fits.
        #    Let's stick to that order.
        
        # Pruning / Summarizing Old Messages
        memory.process_memory(memory_length, model)
        
        # 2b. Attempt to learn Persona (if unknown)
        memory.update_persona_only(model)

        # 3. Get Full Context
        messages_to_send = memory.get_context_for_llm()
        
        print(f"🤖 Generating with {len(messages_to_send)} msgs context (Streaming)...")

        # 4. Stream Response from Ollama
        try:
            stream = ollama.chat(model=model, messages=messages_to_send, stream=True)
            
            full_response = ""
            for chunk in stream:
                content = chunk.get('message', {}).get('content', '')
                if content:
                    full_response += content
                    # Yield token as NDJSON
                    yield json.dumps({"type": "token", "content": content}) + "\n"
            
            # 5. After generation is complete:
            # 5a. Save AI response to memory
            memory.add_message('assistant', full_response)
            
            # 5b. Check if we need to summarize AGAIN because we just added a long AI reply?
            #     The original code only checked before. Let's stick to simple cycle:
            #     User adds -> Check/Summ -> AI adds. 
            #     Next turn handles the formatting.
            
            # 5c. Send final status update
            status_payload = {
                "type": "status",
                "memory_status": memory.get_status()
            }
            yield json.dumps(status_payload) + "\n"

        except Exception as e:
            print(f"Streaming Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

@app.route('/api/reset', methods=['POST'])
def reset_memory():
    memory.reset()
    return jsonify({'success': True})

@app.route('/api/welcome', methods=['GET'])
def api_welcome():
    """Generates a proactive greeting if the user is known."""
    try:
        topics = memory.long_term_summary['topics']
        if len(topics) == 0:
            return jsonify({'message': ''}) # No greeting for new users

        time_ago = memory.get_time_ago()
        history = memory.long_term_summary['request_history']
        
        # Flatten topics for context
        topics_str = ", ".join([f"{k}: {v}" for k, v in topics.items()])
        
        prompt = (
            "You are an empathetic AI Therapist.\n"
            f"Client Profile: {topics_str}\n"
            f"Last Topic: {history}\n"
            f"Time Since Last Chat: {time_ago}\n\n"
            "TASK: Generate a short, warm greeting (max 30 words).\n"
            "1. Say 'Hi' or 'Welcome back'.\n"
            f"2. Mention it has been {time_ago} since you last spoke.\n"
            "3. Briefly reference the last topic and ask how they are feeling today."
        )
        
        # Use a model for generation (hardcoded default or query param if needed)
        # model = 'gemma3:1b'
        resp = ollama.chat(model=DEFAULT_MODEL, messages=[{'role': 'user', 'content': prompt}])
        greeting = resp.get("message", {}).get("content", "")
        
        # We don't save this greeting to memory immediately to avoid clutter, 
        # OR we save it as Assistant message so the user sees it in context. 
        # Let's save it so the transcript makes sense.
        if greeting:
            memory.add_message('assistant', greeting)
            
        return jsonify({'message': greeting, 'memory_status': memory.get_status()})

    except Exception as e:
        print(f"Error generating welcome: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    PORT = 5003
    print('=' * 60)
    print('🧠 Ollama Memory Chat App Started')
    print('=' * 60)
    print(f'📍 URL: http://localhost:{PORT}')
    print('=' * 60)
    app.run(debug=True, host='0.0.0.0', port=PORT)
