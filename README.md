# Starship - AI GitHub Knowledge Engine

🚀 Transform your GitHub stars into an intelligent knowledge base powered by AI agents and vector search.

## Overview

Starship is an innovative AI-powered platform that converts your GitHub starred repositories into a searchable, intelligent knowledge base. Using AutoGen multi-agent systems, ChromaDB vector database, and advanced RAG (Retrieval-Augmented Generation) techniques, Starship helps developers discover, understand, and leverage code from their favorite repositories.

## Key Features

- 🤖 **Multi-Agent System**: AutoGen-powered agents for data collection, analysis, and processing
- 🔍 **Intelligent Search**: RAG-based search with semantic understanding
- 📊 **Health Scoring**: Advanced algorithms to evaluate repository quality and relevance
- 🌳 **Code Analysis**: Tree-sitter powered code parsing and intelligent chunking
- 💾 **Vector Storage**: ChromaDB for efficient similarity search and retrieval
- 🎨 **Modern UI**: Streamlit-based web interface for intuitive interaction
- ⚡ **High Performance**: Optimized for large-scale repository processing

## Architecture

### Core Components

1. **AutoGen Agents**
   - GitHub Data Agent: Fetches repository information and code
   - Code Analysis Agent: Parses and chunks code using tree-sitter
   - Health Scoring Agent: Evaluates repository quality

2. **Vector Database**
   - ChromaDB for storing and retrieving code embeddings
   - Sentence transformers for generating embeddings
   - Optimized for similarity search

3. **RAG Search Engine**
   - Retrieval: Vector-based similarity search
   - Generation: LLM-powered response generation
   - Context-aware results

4. **User Interface**
   - Streamlit web application
   - Real-time search and filtering
   - Repository management dashboard

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- GitHub Personal Access Token

### Installation

1. Clone the repository:
```bash
git clone https://github.com/starship-ai/starship.git
cd starship
```

2. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:
```bash
uv sync
```

Or install in development mode:
```bash
uv sync --extra dev
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
uv run starship init
```

6. Start the application:
```bash
uv run streamlit run src/ui/streamlit_app.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token

# Database Configuration
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8000
CHROMA_DB_PERSIST_DIR=./data/chroma_db

# AI Model Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
```

### Configuration Files

- `config/app.yaml`: Main application configuration
- `config/agents.yaml`: AutoGen agents configuration
- `config/database.yaml`: Database and embedding configuration

## Usage

### Command Line Interface

```bash
# Initialize the system
uv run starship init

# Import GitHub stars
uv run starship import --user your_username

# Process repositories
uv run starship process --batch-size 10

# Start the web interface
uv run starship serve

# Health check
uv run starship health
```

### Web Interface

1. **Search**: Enter queries to find relevant code and repositories
2. **Manage**: Add, remove, or update repositories
3. **Analytics**: View repository health scores and statistics
4. **Settings**: Configure search parameters and filters

## Development

### Project Structure

```
starship/
├── src/
│   ├── agents/          # AutoGen agents
│   ├── data/            # Data processing modules
│   ├── vector_db/       # Vector database integration
│   ├── health/          # Health scoring algorithms
│   └── ui/              # User interface components
├── config/              # Configuration files
├── tests/               # Test suites
├── docs/                # Documentation
├── pyproject.toml       # Project configuration
└── requirements.txt     # Dependencies
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration
```

### Code Quality

```bash
# Format code
uv run black src tests
uv run isort src tests

# Lint code
uv run flake8 src tests
uv run mypy src

# Security check
uv run bandit -r src
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `uv sync --group dev`
4. Make your changes
5. Run tests and quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://starship-ai.github.io/starship)
- 🐛 [Issue Tracker](https://github.com/starship-ai/starship/issues)
- 💬 [Discussions](https://github.com/starship-ai/starship/discussions)
- 📧 [Email Support](mailto:support@starship.ai)

## Roadmap

- [ ] Multi-language support for UI
- [ ] Advanced filtering and search operators
- [ ] Integration with more code hosting platforms
- [ ] Real-time collaboration features
- [ ] Mobile application
- [ ] Enterprise features and deployment options

## Acknowledgments

- [AutoGen](https://github.com/microsoft/autogen) for multi-agent framework
- [ChromaDB](https://github.com/chroma-core/chroma) for vector database
- [Streamlit](https://streamlit.io/) for the web interface
- [Tree-sitter](https://tree-sitter.github.io/) for code parsing
- All the amazing open-source projects that make this possible

---

⭐ If you find Starship useful, please consider giving it a star on GitHub!