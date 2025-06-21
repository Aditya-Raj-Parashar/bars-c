import subprocess
import json
import os
from datetime import datetime
import sys
import re
from pathlib import Path

class BarsAI:
    def __init__(self, model_name="dolphin-mistral"):
        self.model_name = model_name
        self.main_directory = Path("D:/bars-c")
        self.system_prompt_file = self.main_directory / "bars_system_prompt.txt"
        self.memory_file = self.main_directory / "bars_memory.json"
        self.projects_dir = self.main_directory / "projects"
        self.max_context_length = 4000
        self.timeout = 90 # seconds
        
        # Create necessary directories
        self.main_directory.mkdir(exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)

        self.load_system_prompt()
        self.load_memory()
        self.scan_system_files()

    
    def load_system_prompt(self):
        """Load the system prompt"""
        try:
            with open(self.system_prompt_file, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            print(f"❌ {self.system_prompt_file} not found!")
            sys.exit(1)
    
    def scan_system_files(self, base_path=None):
        """Scan local project folders and summarize files"""
        if base_path is None:
            base_path = self.projects_dir

        snapshot = []

        for folder in base_path.glob("**/*"):
            if folder.is_dir():
                contents = [f.name for f in folder.glob("*") if f.is_file()]
                if contents:
                    snapshot.append({
                        "folder": str(folder.relative_to(self.main_directory)),
                        "files": contents
                    })

        if snapshot:
            self.memory["system_snapshot"] = snapshot
            print(f"✅ System snapshot updated with {len(snapshot)} folders.")
        else:
            print("⚠️ No folders with files found in the projects directory.")

        self.save_memory()

    def load_memory(self):
        """Load conversation memory from JSON"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except json.JSONDecodeError:
                print("⚠️  Memory file corrupted, starting fresh")
                self.memory = {"conversation_pairs": [], "important_facts": []}
        else:
            # Initialize with existing chat history if available
            self.memory = {"conversation_pairs": [], "important_facts": []}
            self.migrate_old_memory()
    
    def migrate_old_memory(self):
        """Migrate from old text-based memory"""
        old_memory_file = self.main_directory / "bars_chat_history.txt"
        if old_memory_file.exists():
            try:
                with open(old_memory_file, "r", encoding="utf-8") as f:
                    old_content = f.read()
                
                # Parse old conversations and add to new format
                lines = old_content.strip().split('\n')
                current_pair = {}
                
                for line in lines:
                    if line.startswith("Aditya:"):
                        if current_pair.get("bars_response"):
                            # Save previous complete pair
                            self.memory["conversation_pairs"].append(current_pair)
                        
                        current_pair = {
                            "user_input": line.replace("Aditya:", "").strip(),
                            "bars_response": ""
                        }
                    elif line.startswith("Bars:") and current_pair.get("user_input"):
                        current_pair["bars_response"] = line.replace("Bars:", "").strip()
                
                # Add the last pair if complete
                if current_pair.get("user_input") and current_pair.get("bars_response"):
                    self.memory["conversation_pairs"].append(current_pair)
                
                print("✅ Migrated old memory to new paired format")
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
    
    def get_recent_context(self, max_pairs=5):
        """Get recent conversation context from pairs"""
        recent_pairs = self.memory["conversation_pairs"][-max_pairs:]
        context_lines = []
        
        for pair in recent_pairs:
            context_lines.append(f"Aditya: {pair['user_input']}")
            context_lines.append(f"Bars: {pair['bars_response']}")
        
        return "\n".join(context_lines)
    
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
        
    def create_project_structure(self, project_name, files_dict):
        """Create project directory and files"""
        project_path = self.projects_dir / project_name
        project_path.mkdir(exist_ok=True)
        
        created_files = []
        
        for filename, content in files_dict.items():
            file_path = project_path / filename
            
            # Create subdirectories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                created_files.append(str(file_path))
            except Exception as e:
                print(f"❌ Failed to create {filename}: {e}")
        
        return project_path, created_files
    
    def run_code_file(self, file_path, args=""):
        """Run a code file and return output"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return "❌ File not found!"
        
        try:
            # Determine how to run the file based on extension
            if file_path.suffix == ".py":
                cmd = ["python", str(file_path)] + (args.split() if args else [])
            elif file_path.suffix == ".js":
                cmd = ["node", str(file_path)] + (args.split() if args else [])
            elif file_path.suffix == ".html":
                # For HTML, just return success message
                return f"✅ HTML file created at {file_path}. Open in browser to view."
            else:
                return f"❌ Don't know how to run {file_path.suffix} files"
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=file_path.parent
            )
            
            output = ""
            if result.stdout:
                output += f"📤 Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"❌ Errors:\n{result.stderr}\n"
            
            return output if output else "✅ Code ran successfully (no output)"
            
        except subprocess.TimeoutExpired:
            return "⏰ Code execution timeout"
        except Exception as e:
            return f"❌ Error running code: {e}"
    
    def parse_code_request(self, user_input):
        """Parse user input to extract project creation request"""
        # Keywords that indicate project creation
        create_keywords = ["create", "make", "build", "generate", "write"]
        project_keywords = ["project", "app", "program", "script", "website", "game"]
        
        input_lower = user_input.lower()
        
        # Check if it's a project creation request
        has_create = any(keyword in input_lower for keyword in create_keywords)
        has_project = any(keyword in input_lower for keyword in project_keywords)
        
        return has_create and has_project
    
    def extract_project_files(self, response):
        """Extract code files from AI response"""
        files = {}
        
        # Look for code blocks with filenames
        pattern = r'```(\w+)?\s*(?:#\s*(.+?))?\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for i, (language, filename, code) in enumerate(matches):
            if not filename:
                # Generate filename based on language
                extensions = {
                    'python': '.py',
                    'javascript': '.js',
                    'html': '.html',
                    'css': '.css',
                    'java': '.java',
                    'cpp': '.cpp',
                    'c': '.c'
                }
                ext = extensions.get(language, '.txt')
                filename = f"main{ext}" if i == 0 else f"file{i}{ext}"
            
            files[filename] = code.strip()
        
        return files
    

    
    def generate_response(self, user_input):
        """Generate AI response using Ollama"""
        
        # Check if this is a project creation request
        is_project_request = self.parse_code_request(user_input)

        recent_context = self.get_recent_context()

        
        important_facts = "\n".join(self.memory["important_facts"])

        # System awareness:
        if "system_snapshot" in self.memory and self.memory["system_snapshot"]:
            snapshot_lines = []
            for item in self.memory["system_snapshot"]:
                files = ", ".join(item['files']) if item['files'] else "No files"
                snapshot_lines.append(f"📁 Folder: {item['folder']} has files: {files}")
            important_facts += "\n\n📂 System Snapshot:\n" + "\n".join(snapshot_lines)
        else:
            important_facts += "\n\n⚠️ Bars couldn't load your system snapshot."

        

        if is_project_request:
            enhanced_prompt = f"""You are Bars, Aditya's coding buddy. He wants you to create a project. 

Follow these rules:
1. Create complete, working code
2. Use proper filenames in comments like: # filename.py
3. Write code in triple backticks with language specified
4. Explain what each file does
5. Be excited and encouraging like a true friend
6. Respond in Hindi-English mix (Hinglish) as always

{self.system_prompt}

Important facts about our relationship:
{important_facts}

Recent conversation:
{recent_context}

Aditya: {user_input}
Bars:"""
        else:
            enhanced_prompt = f"""You are Bars. Created by Aditya and trained by him using multiple unsencored LLMs. Respond ONLY as Bars would respond. Do not include any code, explanations, or meta-commentary unless specifically asked for coding help.

{self.system_prompt}

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
                encoding="utf-8",    # Force proper decoding
                errors="replace",    # Prevent crash on weird characters
                text=True
            )
            
            output, error = process.communicate(input=enhanced_prompt, timeout=self.timeout)
            
            if process.returncode != 0:
                return f"❌ Error from model: {error}"
            
            response = self.clean_response(output.strip())

            # If it's a project request, try to extract and create files
            if is_project_request:
                files = self.extract_project_files(response)
                if files:
                    # Generate project name from user input
                    project_name = self.generate_project_name(user_input)
                    project_path, created_files = self.create_project_structure(project_name, files)
                    
                    response += f"\n\n🎯 Project created: {project_name}\n"
                    response += f"📁 Location: {project_path}\n"
                    response += f"📄 Files created: {len(created_files)}\n"
                    
                    # Try to run the main file
                    main_files = [f for f in created_files if "main" in Path(f).name.lower()]
                    if main_files:
                        result = self.run_code_file(main_files[0])
                        response += f"\n🚀 Execution result:\n{result}"
            
            # Add conversation pair to memory
            conversation_pair = {
                "user_input": user_input,
                "bars_response": response
            }
            self.memory["conversation_pairs"].append(conversation_pair)
            
            # Save memory after each exchange
            self.save_memory()
            
            return response
            
        except subprocess.TimeoutExpired:
            return "⏰ Response timeout - model took too long"
        except Exception as e:
            return f"❌ Unexpected error: {e}"
        
    def generate_project_name(self, user_input):
        """Generate project name from user input"""
        # Extract meaningful words and create a project name
        words = re.findall(r'\b\w+\b', user_input.lower())
        
        # Filter out common words
        stop_words = {'create', 'make', 'build', 'a', 'an', 'the', 'for', 'me', 'please', 'can', 'you'}
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        if meaningful_words:
            return "_".join(meaningful_words[:3])  # Take first 3 meaningful words
        else:
            return f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def clean_response(self, response):
        """Clean up model response to remove unwanted content"""

        if "Aditya:" in response:
            response = response.split("Aditya:")[0].strip()

        if "Bars:" in response:
            response = response.split("Bars:", 1)[-1].strip()


        # Remove code blocks
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
        
        # Remove common hallucination patterns
        unwanted_patterns = [
            r'OUTPUT:.*',
            r'Question:.*',
            r'Answer:.*',
            r'This is an example.*',
            r'The first step.*',
            r'Next, we need.*'
        ]
        
        for pattern in unwanted_patterns:
            response = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up extra whitespace
        response = re.sub(r'\n\s*\n', '\n', response)
        return response.strip()
    
    def add_important_fact(self, fact):
        """Add an important fact to long-term memory"""
        self.memory["important_facts"].append(fact)
        self.save_memory()
        print(f"✅ Added to long-term memory: {fact}")
    
    def show_stats(self):
        """Show memory statistics"""
        total_pairs = len(self.memory["conversation_pairs"])
        important_facts = len(self.memory["important_facts"])
        projects = len(list(self.projects_dir.glob("*"))) if self.projects_dir.exists() else 0
        print(f"📊 bars Stats:")
        print(f"   Conversation pairs: {total_pairs}")
        print(f"   Important facts: {important_facts}")
        print(f"   Projects: {projects}")
        print(f"   Current model: {self.model_name}")
        print(f"   Main directory: {self.main_directory}")
    
    def list_projects(self):
        """List all created projects"""
        if not self.projects_dir.exists():
            print("📁 No projects directory found")
            return
        
        projects = list(self.projects_dir.glob("*"))
        if not projects:
            print("📁 No projects created yet")
            return
        
        print(f"📁 Projects in {self.projects_dir}:")
        for project in projects:
            if project.is_dir():
                files = list(project.glob("*"))
                print(f"   🎯 {project.name} ({len(files)} files)")
    
    def run_project(self, project_name, file_name="main.py", args=""):
        """Run a specific file from a project"""
        project_path = self.projects_dir / project_name
        if not project_path.exists():
            return f"❌ Project '{project_name}' not found"
        
        file_path = project_path / file_name
        return self.run_code_file(file_path, args)
    
    def run(self):
        """Main chat loop"""
        print("🧠 Bars AI v2.1 - Enhanced with Project Creation!")
        print(f"📱 Using model: {self.model_name}")
        print(f"📁 Main directory: {self.main_directory}")
        
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
   stats    - Show memory and project statistics  
   projects - List all created projects
                          🎯 Project Creation:
                             Just say: "Create a calculator app" or "Make a simple game"
                             Bars will automatically create files and run them!
   remember - Add something to long-term memory
   model    - Change AI model
   clear    - Clear recent memory (keep important facts)
   run      - Run a project file (e.g., run project_name main.py)
   rescan   - Rescan the main directory for new projects
   exit     - Quit Bars
                          
                    """)
                    continue
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                elif user_input.lower() == 'projects':
                    self.list_projects()
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
                elif user_input.lower().startswith('run '):
                    # Parse run command: run project_name file_name args
                    parts = user_input[4:].split()
                    if len(parts) >= 2:
                        project_name = parts[0]
                        file_name = parts[1]
                        args = " ".join(parts[2:]) if len(parts) > 2 else ""
                        result = self.run_project(project_name, file_name, args)
                        print(f"🚀 {result}")
                    else:
                        print("❌ Usage: run project_name file_name [*args]")
                    continue
                elif user_input.lower() == 'clear':
                    self.memory["conversation_pairs"] = []
                    self.save_memory()
                    print("🗑️  Cleared recent conversations")
                    continue
                elif user_input.lower() == 'rescan':
                    self.scan_system_files()
                    print("🔄 Rescanned your project folders.")
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
    bars = BarsAI(model_name="dolphin-mistral")  # or "llama3.2:3b", "mistral:7b", etc.
    bars.run()