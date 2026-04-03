# Contributing to PAGie

Welcome! We appreciate your interest in contributing to **PAGie** (Personal AI Generation & Information Engine). This project is part of an academic initiative at CADT (Cambodia Academy of Digital Technology) focused on advancing AI-powered document analysis and RAG systems.

## 🎓 Academic Context

PAGie is developed as a **Data Science & Software Engineering project** for university coursework. While we welcome contributions, please note that this is primarily an educational project designed to demonstrate:

- Advanced RAG (Retrieval-Augmented Generation) architectures
- Data Science techniques (EDA & IQR statistical filtering)
- Integration of Google AI (Gemini 3.0) with local embeddings
- ETL pipeline design for unstructured document processing

## 🤝 How to Contribute

### 1. Types of Contributions Welcome

- **🐛 Bug Reports**: Issues with the RAG pipeline, data processing, or UI
- **📚 Documentation**: Improvements to README, code comments, or academic explanations
- **⚡ Performance Optimizations**: Better caching, faster embeddings, or memory efficiency
- **🧪 Testing**: Unit tests, integration tests, or performance benchmarks
- **📊 Data Science Enhancements**: Better EDA visualizations, statistical filtering methods
- **🔧 Code Quality**: Refactoring, PEP 8 compliance, or architectural improvements

### 2. Development Setup

```bash
# Clone the repository
git clone https://github.com/LK-Hour/PAGie.git
cd PAGie

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Configure your API keys in .env
# GOOGLE_API_KEY=your_gemini_api_key_here
# GOOGLE_DRIVE_FOLDER_ID=your_cv_folder_id
```

### 3. Branch Strategy

- **`main`**: Stable release branch
- **`cv_focus`**: Development branch with CV-specific optimizations
- **Feature branches**: `feature/your-feature-name`

### 4. Code Standards

Since this is an academic project, we maintain high code quality standards:

#### **Python Style Guidelines:**
- Follow **PEP 8** formatting
- Use descriptive variable names (academic readability)
- Include comprehensive docstrings for functions and classes
- Add inline comments explaining **why**, not just **what**

#### **Data Science Standards:**
- **Always apply IQR filtering** when processing text chunks
- Include statistical validation for any data processing changes
- Generate visualizations for EDA (use matplotlib/seaborn)
- Document statistical assumptions and methodologies

#### **Security Requirements:**
- **Never commit API keys** - use environment variables only
- Validate all external inputs (Google Drive files, user queries)
- Include try/except blocks for external API calls

### 5. Commit Message Format

Use clear, descriptive commit messages:

```
type(scope): brief description

Examples:
feat(rag): add semantic caching for embedding queries
fix(ui): resolve memory leak in Streamlit chat history
docs(readme): update installation instructions for ChromaDB
perf(embeddings): optimize sentence-transformer model loading
test(pipeline): add unit tests for IQR filtering logic
```

### 6. Pull Request Process

1. **Fork the repository** and create your feature branch from `cv_focus`
2. **Test your changes** thoroughly:
   ```bash
   # Run performance tests
   python test_performance.py
   
   # Test both dev and prod modes
   ./ops_run_optimized_dev.sh
   ./ops_run_optimized_prod.sh
   ```
3. **Update documentation** if you change functionality
4. **Submit a Pull Request** with:
   - Clear description of changes
   - Screenshots/GIFs for UI changes
   - Performance impact analysis for optimization changes
   - Test results demonstrating your changes work

### 7. Academic Considerations

When contributing, please keep in mind:

- **Educational Value**: Code should be clear enough for other students to learn from
- **Documentation**: Explain complex algorithms or data science concepts
- **Reproducibility**: Ensure your changes work across different environments
- **Citation**: If using external algorithms or methodologies, include proper citations

## 📧 Contact

- **Project Lead**: LK-Hour
- **Institution**: CADT (Cambodia Academy of Digital Technology)
- **Course**: Y3 T2 Data Science
- **GitHub Issues**: [Create an issue](https://github.com/LK-Hour/PAGie/issues) for bug reports or feature requests

## 📝 License

By contributing to PAGie, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

**Thank you for helping make PAGie better!** 🚀

Your contributions help advance AI education and research at CADT and beyond.