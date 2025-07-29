# Not Cursor - Independent AI Code Assistant

A locally hosted AI-powered code assistant that uses LangGraph and Together AI to automatically modify and commit code changes based on natural language prompts.

## 🚀 Features

- **Natural Language Interface**: Describe what you want to build or modify in plain English
- **Automatic File Analysis**: Analyzes your repository structure and recent commits
- **Intelligent Code Generation**: Creates or modifies files based on your requirements
- **Git Integration**: Automatically creates feature branches and commits changes
- **Real-time Streaming**: Watch the AI work in real-time with live output
- **Modern UI**: Clean, terminal-inspired interface with cosmic aesthetic

## 🛠️ How It Was Built

### Architecture Overview

This project combines several cutting-edge technologies:

1. **Flask Web Server** (`ui_server.py`): Provides the web interface and API endpoints
2. **LangGraph Workflow Engine**: Orchestrates the AI reasoning process
3. **Together AI Integration**: Uses Mixtral-8x7B-Instruct for code generation
4. **GitPython**: Handles repository operations and version control
5. **Server-Sent Events (SSE)**: Enables real-time streaming of AI progress

### Core Components

#### 1. State Management (`State` TypedDict)
```python
class State(TypedDict):
    repo_path: str
    files: dict[str, str]
    commits: list[str]
    file_list: list[str]
    current_idx: int
    modified_path: str
    new_content: str
    next: str
    modified_files: list[str]
```

#### 2. LangGraph Workflow
The AI reasoning process follows this sequence:
1. **Repository Context Loading**: Scans files and recent commits
2. **Action Planning**: AI creates a JSON plan of files to modify
3. **File Rewriting**: Iteratively modifies or creates files
4. **Git Operations**: Commits changes to a new feature branch

#### 3. Frontend Interface (`templates/index.html`)
- Terminal-inspired design with cosmic aesthetic
- Real-time streaming output display
- Interactive prompt input with execute button
- Color-coded output messages (success, error, info, warning)

### Key Technologies Used

- **Backend**: Flask, LangGraph, LangChain, GitPython
- **AI Model**: Together AI's Mixtral-8x7B-Instruct
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Real-time Communication**: Server-Sent Events (SSE)
- **Version Control**: Git integration with automatic branching

## 📦 Installation

### Prerequisites

- Python 3.8+
- Git repository initialized
- Together AI API key

### Setup Instructions

1. **Clone and Navigate**
   ```bash
   cd your-project-directory
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   TOGETHER_API_KEY=your_together_ai_api_key_here
   ```

4. **Repository Setup**
   Ensure your project is a Git repository:
   ```bash
   git init
   git remote add origin your-github-repo-url
   ```

## 🚀 Usage

### Starting the Server

1. **Run the Flask Application**
   ```bash
   python ui_server.py
   ```

2. **Access the Interface**
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Using the Interface

1. **Enter Your Prompt**
   - Type a natural language description of what you want to build or modify
   - Examples:
     - "Add a login button to the navbar"
     - "Create a new API endpoint for user registration"
     - "Add dark mode toggle to the settings page"

2. **Watch the AI Work**
   - The interface will show real-time progress
   - Files being analyzed and modified
   - Git operations being performed

3. **Review Changes**
   - Check the generated GitHub branch link
   - Review the pull request URL
   - Examine the modified files

### Example Prompts

```
"Add a contact form to the homepage with email validation"
"Create a new React component for displaying user profiles"
"Add error handling to the authentication API endpoints"
"Implement a search feature with debounced input"
"Add unit tests for the user service functions"
```

## 🔧 Configuration

### Customizing the Repository Path

Edit `ui_server.py` line 175:
```python
"repo_path": "/path/to/your/project",
```

### Adjusting AI Model Parameters

Modify the LLM configuration in `ui_server.py`:
```python
llm = ChatTogether(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.7,  # Adjust creativity (0.0-1.0)
    max_tokens=512    # Adjust response length
)
```

### Changing Commit Settings

Customize the commit message and branch naming in the `commit_to_git` function:
```python
branch_name = f"feature--{uuid.uuid4().hex[:6]}"
# Change to: branch_name = f"ai-feature-{uuid.uuid4().hex[:8]}"
```

## 📁 Project Structure

```
├── ui_server.py          # Main Flask application
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html       # Web interface
├── .env                 # Environment variables (create this)
└── README.md           # This file
```

## 🔍 How It Works

### 1. Prompt Processing
When you submit a prompt, the system:
- Loads your repository context (files + recent commits)
- Analyzes the current codebase structure
- Generates an action plan using AI

### 2. AI Planning Phase
The AI creates a JSON plan specifying:
- Which files need modification
- What actions to perform on each file
- Whether to create new files or modify existing ones

### 3. Code Generation
For each file in the plan:
- AI analyzes the current content (if existing)
- Generates new code based on your requirements
- Preserves existing functionality while adding new features

### 4. Git Operations
The system automatically:
- Creates a new feature branch
- Commits all changes with descriptive messages
- Pushes to your remote repository
- Provides links for pull requests

## 🎨 UI Features

### Real-time Streaming
- Live output display with color-coded messages
- Progress indicators for each operation
- Error handling with clear feedback

### Interactive Elements
- Auto-focusing input field
- Execute button with hover effects
- Keyboard shortcuts (Enter to submit)

### Visual Design
- Terminal-inspired aesthetic
- Cosmic color scheme with glowing effects
- Responsive design for different screen sizes

## 🛡️ Error Handling

The system includes comprehensive error handling:
- Invalid prompts are rejected with clear messages
- Network errors are displayed to the user
- Git operations are wrapped in try-catch blocks
- AI response parsing includes fallback mechanisms

## 🔄 Workflow States

1. **Initialization**: Loading repository context
2. **Planning**: AI generates action plan
3. **Execution**: Files are modified sequentially
4. **Commit**: Changes are committed to Git
5. **Completion**: Links and summaries are provided

## 🚨 Limitations

- Only supports text-based files (.py, .js, .ts, .jsx, .tsx)
- Requires Git repository to be properly configured
- Depends on Together AI API availability
- Maximum response length is limited by token count

## 🤝 Contributing

This is an independent project designed for local use. The architecture is modular and can be extended with:
- Additional AI models
- More file type support
- Enhanced Git workflows
- Custom UI themes

## 📄 License

This project is for educational and personal use. Please respect the terms of service for all integrated APIs and services.

---

**Built with ❤️ using LangGraph, Flask, and Together AI**
