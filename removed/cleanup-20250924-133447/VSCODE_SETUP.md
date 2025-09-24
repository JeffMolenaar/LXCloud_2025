# VS Code Development Setup for LXCloud 2025

This guide will help you set up Visual Studio Code for optimal LXCloud development.

## Prerequisites

- Visual Studio Code installed
- Python 3.8+ installed
- Git installed

## Quick Setup

### Option 1: Open Workspace File (Recommended)
1. Clone the repository
2. Open VS Code
3. File → Open Workspace from File
4. Select `LXCloud_2025.code-workspace`
5. Install recommended extensions when prompted

### Option 2: Open Folder
1. Clone the repository
2. Open the `LXCloud_2025` folder in VS Code
3. Install recommended extensions when prompted

## Initial Setup Steps

### 1. Install Python Dependencies

Open the integrated terminal (`` Ctrl+` ``) and run:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install black flake8 isort
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

For development, you can use the provided development configuration:
```bash
cp .env.dev .env
```

### 3. Select Python Interpreter

1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Python: Select Interpreter"
3. Choose `./venv/bin/python` (or `.\venv\Scripts\python.exe` on Windows)

## Features Included

### ✅ What's Configured

- **Python Development**: Full IntelliSense, debugging, linting
- **Flask Framework**: Debug configurations, snippets, template support
- **Database Integration**: SQLAlchemy support, database utilities
- **MQTT Development**: Code snippets and debugging support
- **Code Quality**: Black formatting, flake8 linting, automatic imports
- **Template Support**: Jinja2 syntax highlighting and completion
- **Git Integration**: Enhanced Git features and history
- **Task Automation**: Pre-configured tasks for common operations

### 🎯 Debugging Features

- **Flask Development Server**: Full debugging with breakpoints
- **Database Scripts**: Debug database utilities and migrations
- **Controller Services**: Debug MQTT and status services
- **Test Applications**: Debug test scripts and API endpoints

### 🛠️ Available Tasks

Press `Ctrl+Shift+P` and type "Tasks: Run Task":

- **Install Dependencies**: Install Python packages
- **Create Virtual Environment**: Set up venv
- **Run Flask Development Server**: Start the app
- **Test Database Configuration**: Validate database setup
- **Format Python Code**: Auto-format with black
- **Lint Python Code**: Check code quality
- **Install Development Tools**: Install black, flake8, isort

### 📝 Code Snippets

Type these prefixes and press Tab:

- `route` → Flask route template
- `api` → API endpoint with error handling
- `blueprint` → Flask blueprint
- `model` → SQLAlchemy model
- `errorhandler` → Error handler function
- `mqtt` → MQTT message handler
- `try` → Try-except block

## Development Workflow

### Starting Development

1. **Open Project**: `code LXCloud_2025.code-workspace`
2. **Start Debugging**: Press `F5` or select "Flask App - Development"
3. **View Application**: Open http://127.0.0.1:5000 in browser

### Making Changes

1. **Edit Code**: Full IntelliSense support for Flask and SQLAlchemy
2. **Auto-Format**: Code automatically formatted on save
3. **Live Debugging**: Set breakpoints and debug in real-time
4. **Template Editing**: Jinja2 syntax highlighting and completion

### Testing

1. **Run Tests**: Use launch configurations for test files
2. **API Testing**: Use REST Client extension or integrated tools
3. **Database Testing**: Debug database utilities directly

## Recommended Extensions

The following extensions will be recommended when you open the project:

### Essential
- **Python** - Core Python support
- **Python Debugger** - Enhanced debugging
- **Jinja** - Template syntax highlighting
- **HTML CSS Support** - Web development

### Optional but Recommended
- **GitLens** - Enhanced Git integration
- **REST Client** - API testing
- **Docker** - Container support
- **Thunder Client** - API testing
- **Todo Tree** - Task management
- **Material Theme** - Better UI

## Troubleshooting

### Python Interpreter Issues
**Problem**: "Python interpreter not found"
**Solution**: 
1. Create virtual environment: `python3 -m venv venv`
2. Run task "Create Virtual Environment and Install Dependencies"
3. Select interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"

### Flask App Won't Start
**Problem**: Import errors or missing modules
**Solution**:
1. Ensure virtual environment is activated
2. Install dependencies: `pip install -r requirements.txt`
3. Check `.env` file exists and has correct values
4. Verify database configuration

### Template Syntax Not Highlighted
**Problem**: HTML templates don't show Jinja2 syntax
**Solution**:
1. Install "Jinja" extension
2. Check file associations in settings.json
3. Reload VS Code window

### Debugger Not Working
**Problem**: Breakpoints not hit or debugging fails
**Solution**:
1. Verify Python interpreter is correct
2. Check launch configuration in launch.json
3. Ensure Flask debug mode is enabled
4. Check that the correct launch configuration is selected

### Formatting Not Working
**Problem**: Code not auto-formatted on save
**Solution**:
1. Install black: `pip install black`
2. Check Python formatter setting is set to "black"
3. Verify "editor.formatOnSave": true in settings

## Advanced Configuration

### Custom Launch Configurations

Add your own debug configurations to `.vscode/launch.json`:

```json
{
    "name": "My Custom Script",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/my_script.py",
    "console": "integratedTerminal",
    "envFile": "${workspaceFolder}/.env"
}
```

### Custom Tasks

Add your own tasks to `.vscode/tasks.json`:

```json
{
    "label": "My Custom Task",
    "type": "shell",
    "command": "python3",
    "args": ["my_script.py"],
    "group": "build",
    "options": {
        "cwd": "${workspaceFolder}"
    }
}
```

### Environment Specific Settings

Create `.env.development`, `.env.testing`, or `.env.production` files and modify the `envFile` setting in launch configurations.

## VS Code Settings Explained

### Key Settings in `.vscode/settings.json`

```json
{
    // Use virtual environment Python
    "python.defaultInterpreterPath": "./venv/bin/python",
    
    // Auto-format on save with black
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    
    // Lint with flake8
    "python.linting.flake8Enabled": true,
    
    // Template support
    "files.associations": {
        "*.html": "html",
        "*.jinja": "jinja-html"
    },
    
    // Flask-specific paths
    "python.analysis.extraPaths": ["./app"]
}
```

## Performance Optimization

### Exclude Unnecessary Files

The configuration excludes these from search and file watching:
- `__pycache__/` and `*.pyc` files
- Virtual environments (`venv/`, `env/`)
- Database files (`.db`, `.sqlite3`)
- Log files and temporary directories
- Git objects and caches

### Large Project Optimization

For better performance with large codebases:
1. Use "Search: Exclude" patterns
2. Disable unnecessary extensions
3. Increase VS Code memory limits if needed

## Integration with LXCloud Features

### Database Development
- Debug database utilities with full stack traces
- SQLAlchemy model IntelliSense and completion
- Database connection testing and validation

### MQTT Integration
- MQTT message handler snippets
- Debug MQTT services with breakpoints
- JSON validation for MQTT payloads

### API Development
- Flask API route templates
- Error handling patterns
- Request/response debugging

### Frontend Development
- Jinja2 template debugging
- CSS and JavaScript integration
- Live reload during development

## Getting Help

- Check the `.vscode/README.md` file for detailed configuration info
- Use VS Code's built-in help: `F1` → "Help"
- Check the Problems panel for linting issues
- Review the Output panel for Python and extension logs

## Next Steps

1. **Explore the codebase** using VS Code's navigation features
2. **Set up your development database** using the provided scripts
3. **Start debugging** by setting breakpoints in Flask routes
4. **Test the API endpoints** using REST Client or Thunder Client
5. **Customize your environment** by modifying `.env` and VS Code settings

Happy coding! 🚀