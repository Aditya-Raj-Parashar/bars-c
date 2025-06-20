import subprocess
import json
import os
from datetime import datetime
import sys

class BarsAI:
    def __init__(self, model_name="qwen2.5:7b"):
        self.model_name = model_name
        self.system_prompt_file = "bars_system_prompt.txt"
        self.memory_file = "bars_memory.json"
        self.max_context_length = 4000  # Adjust based on model
        self.load_system_prompt()
        self.load_memory()
    
    def load_system_prompt(self):
        """Load the system prompt"""
        try:
            with open(self.system_prompt_file, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            print(f"❌ {self.system_prompt_file} not found!")
            sys.exit(1)
    
    def load_memory(self):
        """Load conversation memory from JSON"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except json.JSONDecodeError:
                print("⚠️  Memory file corrupted, starting fresh")
                self.memory = {"conversations": [], "important_facts": []}
        else:
            # Initialize with existing chat history if available
            self.memory = {"conversations": [], "important_facts": []}
            self.migrate_old_memory()
    
    def migrate_old_memory(self):
        """Migrate from old text-based memory"""
        old_memory_file = "bars_chat_history.txt"
        if os.path.exists(old_memory_file):
            try:
                with open(old_memory_file, "r", encoding="utf-8") as f:
                    old_content = f.read()
                
                # Parse old conversations and add to new format
                lines = old_content.strip().split('\n')
                for line in lines:
                    if line.startswith("Aditya:"):
                        user_msg = line.replace("Aditya:", "").strip()
                        self.memory["conversations"].append({
                            "role": "user",
                            "content": user_msg,
                            "timestamp": datetime.now().isoformat()
                        })
                    elif line.startswith("Bars:"):
                        ai_msg = line.replace("Bars:", "").strip()
                        self.memory["conversations"].append({
                            "role": "assistant", 
                            "content": ai_msg,
                            "timestamp": datetime.now().isoformat()
                        })
                
                print("✅ Migrated old memory to new format")
                self.save_memory()
            except Exception as e:
                print(f"⚠️  Could not migrate old memory: {e}")
    
    def save_memory(self):
        """Save memory to JSON file"""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Failed to save memory: {e}")
    
    def get_recent_context(self, max_messages=10):
        """Get recent conversation context"""
        recent_convos = self.memory["conversations"][-max_messages:]
        return "\n".join([
            f"{'Aditya' if msg['role'] == 'user' else 'Bars'}: {msg['content']}"
            for msg in recent_convos
        ])
    
    def check_ollama_status(self):
        """Check if Ollama is running and model is available"""
        try:
            # Check if ollama is running
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode != 0:
                return False, "Ollama is not running"
            
            # Check if our model is available
            if self.model_name not in result.stdout:
                return False, f"Model {self.model_name} not found. Available models:\n{result.stdout}"
            
            return True, "All good!"
            
        except subprocess.TimeoutExpired:
            return False, "Ollama is not responding"
        except FileNotFoundError:
            return False, "Ollama is not installed"
    
    def generate_response(self, user_input):
        """Generate AI response using Ollama"""
        
        # Add user message to memory
        self.memory["conversations"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build context
        recent_context = self.get_recent_context()
        important_facts = "\n".join(self.memory["important_facts"])
        
        full_prompt = f"""{self.system_prompt}

Important facts about our relationship:
{important_facts}

Recent conversation:
{recent_context}

Aditya: {user_input}
Bars:"""
        
        try:
            # Run ollama
            process = subprocess.Popen(
                ["ollama", "run", self.model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            output, error = process.communicate(input=full_prompt, timeout=30)
            
            if process.returncode != 0:
                return f"❌ Error from model: {error}"
            
            response = output.strip()
            
            # Add AI response to memory
            self.memory["conversations"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save memory after each exchange
            self.save_memory()
            
            return response
            
       # except subprocess.TimeoutExpired:
       #     return "⏰ Response timeout - model took too long"
        except Exception as e:
            return f"❌ Unexpected error: {e}"
    
    def add_important_fact(self, fact):
        """Add an important fact to long-term memory"""
        self.memory["important_facts"].append(fact)
        self.save_memory()
        print(f"✅ Added to long-term memory: {fact}")
    
    def show_stats(self):
        """Show memory statistics"""
        total_messages = len(self.memory["conversations"])
        important_facts = len(self.memory["important_facts"])
        print(f"📊 Memory Stats:")
        print(f"   Total messages: {total_messages}")
        print(f"   Important facts: {important_facts}")
        print(f"   Current model: {self.model_name}")
    
    def run(self):
        """Main chat loop"""
        print("🧠 Bars AI v2.0 - Enhanced with memory!")
        print(f"📱 Using model: {self.model_name}")
        
        # Check ollama status
        status_ok, status_msg = self.check_ollama_status()
        if not status_ok:
            print(f"❌ {status_msg}")
            print("💡 Try: ollama serve (in another terminal)")
            return
        
        print("✅ Ollama is ready!")
        print("💬 Type 'help' for commands, 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("You > ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Bars > Catch you later, Aditya! 🤘")
                    break
                elif user_input.lower() == 'help':
                    print("""
🔧 Bars Commands:
   help     - Show this menu
   stats    - Show memory statistics  
   remember - Add something to long-term memory
   model    - Change AI model
   clear    - Clear recent memory (keep important facts)
   exit     - Quit Bars
                    """)
                    continue
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                elif user_input.lower().startswith('remember '):
                    fact = user_input[9:]  # Remove 'remember '
                    self.add_important_fact(fact)
                    continue
                elif user_input.lower().startswith('model '):
                    new_model = user_input[6:]  # Remove 'model '
                    self.model_name = new_model
                    print(f"🔄 Switched to model: {new_model}")
                    continue
                elif user_input.lower() == 'clear':
                    self.memory["conversations"] = []
                    self.save_memory()
                    print("🗑️  Cleared recent conversations")
                    continue
                elif not user_input:
                    continue
                
                # Generate and print response
                response = self.generate_response(user_input)
                print(f"Bars > {response}")
                
            except KeyboardInterrupt:
                print("\nBars > Alright, catch you later! 🤘")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    # You can change the model here
    bars = BarsAI(model_name="llama3.2:latest")  # or "llama3.2:3b", "mistral:7b", etc.
    bars.run()