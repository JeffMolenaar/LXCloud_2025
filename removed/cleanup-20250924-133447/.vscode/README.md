# VS Code Configuration for LXCloud 2025

This directory contains Visual Studio Code configuration files to enhance your development experience with the LXCloud platform.

## Quick Start

1. **Open the project in VS Code:**

   ```bash
   code LXCloud_2025.code-workspace
   ```

   Or simply open the folder in VS Code.

2. **Install recommended extensions when prompted**

3. **Set up Python virtual environment:**

   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)

   - Type "Python: Select Interpreter"

   - Choose `./venv/bin/python` or create a new virtual environment

## Configuration Files

### `settings.json`

- Python interpreter configuration
- Linting with flake8
- Formatting with black
- Flask-specific settings
- File associations for Jinja templates
- Search and file watcher exclusions

### `launch.json`

- Debug configurations for Flask app
- Multiple launch configurations:
   - Flask Development Server
   - Database utilities
   - Controller status debugging

### `tasks.json`

- Common development tasks:
   - Install dependencies
   - Create virtual environment
   - Run development server
   - Code formatting and linting
   - Database setup

### `extensions.json`

- Recommended VS Code extensions for:
   - Python development
   - Flask and Jinja2 templates
   - Web development (HTML/CSS/JS)
   - Database management
   - Git integration
   - Code quality tools

## Debugging

### Flask Application

1. Set breakpoints in your Python code

2. Press `F5` or go to Run > Start Debugging

3. Select "Flask App - Development" configuration

4. Your Flask app will start in debug mode

### API Endpoints

- Use the REST Client extension with `.http` files
- Or test endpoints directly in VS Code using Thunder Client

## Running Tasks

Press `Ctrl+Shift+P` and type "Tasks: Run Task" to access:
- **Install Dependencies**: Install Python packages from requirements.txt
- **Run Flask Development Server**: Start the development server
- **Test Database Configuration**: Run database tests
- **Format Python Code**: Format code with black
- **Lint Python Code**: Check code quality with flake8

## Python Environment Setup

### Automatic Setup
The workspace is configured to automatically:
- Detect the Python interpreter in `./venv/bin/python`
- Activate the virtual environment in terminal
- Load environment variables from `.env` file

### Manual Setup
If you need to create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate   # Windows
pip install -r requirements.txt
```

## Code Quality

### Formatting
- Code is automatically formatted on save using black
- Line length: 120 characters
- Compatible with PEP 8

### Linting
- flake8 is configured for code quality checks
- Custom rules for Flask applications
- Ignores some black-incompatible rules

### Import Sorting
- isort configured to work with black formatter
- Automatically sorts imports on save

## Templates and Snippets

### Flask Snippets
Type these prefixes and press Tab:
- `route` - Flask route template
- `api` - API endpoint with error handling
- `blueprint` - Flask blueprint
- `model` - SQLAlchemy model
- `errorhandler` - Error handler
- `mqtt` - MQTT message handler

### Jinja2 Templates
- Syntax highlighting for `.html` files in templates/
- IntelliSense for Jinja2 variables and filters
- Auto-completion for Flask template functions

## File Associations

- `.html` files in templates/ are treated as Jinja2 templates
- `.env*` files have proper syntax highlighting
- `.conf` files are treated as INI format

## Excluded Files

The following are excluded from search and file watching:
- `__pycache__/` and `.pyc` files
- Virtual environments (`venv/`, `env/`)
- Database files (`.db`, `.sqlite3`)
- Log files and temporary directories
- Node modules (if using frontend build tools)

## Troubleshooting

### Python Interpreter Not Found
1. Create a virtual environment: Run task "Create Virtual Environment"
2. Install dependencies: Run task "Install Dependencies"
3. Select interpreter: `Ctrl+Shift+P` > "Python: Select Interpreter"

### Flask App Won't Start
1. Check your `.env` file exists and has correct values
2. Ensure database is properly configured
3. Check the terminal output for specific error messages

### Extensions Not Working
1. Install recommended extensions when prompted
2. Reload VS Code window: `Ctrl+Shift+P` > "Developer: Reload Window"
3. Check extension requirements (e.g., Python extension needs Python installed)

## Development Workflow

1. **Start Development:**
   - Open workspace: `code LXCloud_2025.code-workspace`
   - Press `F5` to start debugging, or run task "Run Flask Development Server"

2. **Make Changes:**
   - Edit Python files with full IntelliSense support
   - Edit templates with Jinja2 syntax highlighting
   - Code is auto-formatted on save

3. **Test Changes:**
   - Use debug breakpoints for troubleshooting
   - Run specific test files via launch configurations
   - Use integrated terminal for database operations

4. **Code Quality:**
   - Linting issues appear in Problems panel
   - Format code with `Shift+Alt+F`
   - Run linting task for full codebase check

## Integration with LXCloud Features

### Database Development
- Launch configurations for database utilities
- Snippets for SQLAlchemy models
- Environment integration for database connections

### MQTT Development
- Snippets for MQTT handlers
- JSON schema validation for MQTT messages
- Debug support for MQTT services

### API Development
- REST Client integration for API testing
- JSON formatting and validation
- Error handling snippets

### Template Development
- Jinja2 syntax support
- Bootstrap and custom CSS integration
- Live preview of template changes