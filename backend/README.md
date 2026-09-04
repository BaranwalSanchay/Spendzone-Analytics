# AI-Driven Marketing Analytics & Reporting System

An advanced system that automatically analyzes marketing data and generates comprehensive, insightful reports using various AI agents.

## Table of Contents
1. [Introduction](#introduction)
2. [Dataset Information](#dataset-information)
3. [Project Description](#project-description)
4. [Technologies Used](#technologies-used)
5. [Installation & Setup](#installation--setup)
6. [Project Structure](#project-structure)
7. [Agent System](#agent-system)
8. [Report Generation](#report-generation)
9. [Customization](#customization)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)

## Introduction

The Marketing Analytics & Reporting System is an AI-powered solution designed to streamline the process of generating comprehensive marketing reports. It leverages multiple specialized AI agents to analyze marketing data from various angles, including ROI analysis, budget optimization, KPI evaluation, and market research, producing detailed insights with minimal human intervention.

This system uses Large Language Models (LLMs) and specialized agents to intelligently analyze marketing data, extract meaningful insights, and compile structured reports. The project demonstrates how AI can be utilized to automate complex analytical tasks in marketing departments, saving time and providing data-driven recommendations.

## Dataset Information

The system works with marketing performance datasets, including:

- **Master.csv**: The main dataset containing comprehensive marketing information, including:
  - Marketing channel spend data
  - Revenue/GMV metrics
  - Product information
  - Channel performance metrics
  - SLA and NPS score data
  - Order and customer data

- **marketing_analysis.db**: An SQLite database containing structured marketing data for SQL-based analysis.

The data is managed by a centralized `DataManager` that handles loading, preprocessing, and providing consistent access to the datasets for all agents in the system.

## Project Description

This project is designed to transform raw marketing data into actionable intelligence through AI-powered analysis. The system:

1. **Ingests marketing data** from various sources (CSV, database)
2. **Processes and analyzes data** through specialized AI agents, each focused on different aspects of marketing analytics
3. **Compiles insights** into comprehensive, structured reports
4. **Outputs reports** in multiple formats (Markdown, PDF)

The core functionality revolves around a supervisor agent that coordinates multiple specialized analysis agents, including:

- **Exploration Agent**: Performs general data analysis and statistical evaluation
- **SQL Agent**: Conducts SQL-based data queries and analysis
- **ROI Agent**: Analyzes marketing return on investment
- **Budget Agent**: Optimizes budget allocation across marketing channels
- **KPI Agent**: Evaluates key performance indicators and metrics
- **Market Analysis Agent**: Conducts market research and competitive analysis

Each question in the report is processed by relevant agents, and their outputs are compiled into cohesive, well-structured report sections.

## Technologies Used

The system is built with a wide range of modern technologies:

### Core Technologies
- **Python 3.12**: Primary programming language
- **Poetry**: Dependency management and packaging
- **Git**: Version control

### Data Processing & Analysis
- **Pandas**: Data manipulation, transformation, and analysis
- **NumPy**: Numerical computing and array operations
- **SciPy**: Scientific computing and statistical analysis
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM)
- **SQLite**: Lightweight database storage

### AI & Machine Learning
- **LangChain**: Framework for developing LLM applications
- **LangGraph**: Agent workflow and orchestration
- **Groq**: High-performance LLM inference API
- **Google Generative AI**: Alternative LLM provider
- **Scikit-learn**: Machine learning utilities and algorithms

### Web & External Services
- **Tavily**: Web search and information retrieval
- **BeautifulSoup**: HTML parsing and web scraping
- **Requests**: HTTP library for API interactions

### Visualization & Reporting
- **Matplotlib**: Data visualization
- **Seaborn**: Statistical data visualization
- **ReportLab**: PDF generation from Python
- **WeasyPrint**: HTML to PDF conversion
- **pdfkit**: HTML to PDF wrapper for wkhtmltopdf
- **Markdown**: Report formatting

### Development & Debugging
- **Logging**: Application activity tracking
- **dotenv**: Environment variable management
- **pytest**: Testing framework (for development)

## Installation & Setup

### Prerequisites

- Python 3.12 or higher
- Poetry (recommended) or pip

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/GC_DATA_2025.git
   cd GC_DATA_2025/Report
   ```

2. **Install dependencies using Poetry**:
   ```bash
   poetry install
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the Report directory with your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   # Add other API keys as needed
   ```

4. **Prepare your data**:
   - Place your marketing data CSV file(s) in the `data/` directory
   - Ensure your database file is properly configured if using SQL

### Running the System

To generate a marketing report:

```bash
python main.py
```

The generated report will be available in the `reports/` directory in both Markdown and PDF formats.

## Project Structure

```
Report/
├── agents/              # Specialized AI agents
│   ├── budget.py        # Budget optimization agent
│   ├── exploration.py   # Data exploration agent
│   ├── kpi.py           # KPI analysis agent
│   ├── roi.py           # ROI analysis agent
│   ├── sql.py           # SQL query agent
│   ├── market_analysis.py # Market research agent
│   ├── compiler.py      # Results compilation agent
│   ├── report_generator.py # Report generation coordinator
│   └── ...
├── data/                # Data directory
│   ├── Master.csv       # Main marketing dataset
│   └── marketing_analysis.db # SQLite database
├── reports/             # Generated reports
├── utils/               # Utility modules
│   ├── data_manager.py  # Data loading and management
│   ├── report.py        # Report structure definitions
│   ├── report_to_pdf.py # PDF conversion utilities
│   └── clean.py         # Data cleaning utilities
├── test/                # Test files
├── main.py              # Main execution script
├── pyproject.toml       # Poetry dependencies
├── .env                 # Environment variables
└── README.md            # This file
```

## Agent System

The system uses a coordinated multi-agent approach:

### SupervisorAgent
Coordinates the entire analysis process, managing the workflow between specialized agents.

### Specialized Agents
- **ExplorationAgent**: Conducts general data exploration and statistical analysis
- **SQLAgent**: Performs SQL queries against the marketing database
- **ROIAgent**: Analyzes marketing ROI and performance metrics
- **BudgetAgent**: Optimizes budget allocation across marketing channels
- **KPIAgent**: Evaluates key performance indicators
- **MarketAnalysisAgent**: Conducts market research and competitive analysis

### Agent Workflow
1. Each question is assigned to relevant agents based on the report section
2. Agents perform parallel analysis on the question
3. Results are compiled by the compiler agent
4. Formatted content is added to the report

## Report Generation

The report generation process follows these steps:

1. **Section Planning**: The system uses predefined section questions from `utils/report.py`
2. **Question Processing**: Each question is sent to the SupervisorAgent
3. **Multi-Agent Analysis**: Specialized agents analyze the question
4. **Results Compilation**: The compiler agent integrates results
5. **Report Formatting**: Markdown report is generated
6. **PDF Conversion**: The markdown report is converted to PDF

## Customization

### Adding New Questions
Edit the `utils/report.py` file to add new questions to existing sections or create new sections.

### Modifying Agent Behavior
Each agent can be customized by editing their respective files in the `agents/` directory.

### Changing Report Format
Modify the `generate_markdown_report` function in `main.py` or update PDF conversion settings in `utils/report_to_pdf.py`.

## Troubleshooting

### Common Issues

- **API Rate Limiting**: If you encounter rate limiting errors, increase the pause times between sections and questions in `main.py`.
- **Memory Issues**: If you experience memory problems, enable garbage collection by setting appropriate parameters.
- **Missing Dependencies**: Ensure all dependencies are properly installed using Poetry or pip.
- **Data Loading Errors**: Check that your data files are in the correct format and location.

### Logs
Check the following log files for more information:
- `budget_agent.log`
- `kpi_agent.log`
- `roi_agent.log`
- `sql_agent.log`
- `exploration_agent.log`
- `data_manager.log`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 