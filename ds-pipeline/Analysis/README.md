# Marketing Channel Analysis

## Overview
This project analyzes the relationship between various marketing channels and product sales/GMV (Gross Merchandise Value) across different product categories. The analysis uses machine learning models to understand which marketing channels most effectively drive sales for different product lines, providing actionable insights for marketing budget allocation and campaign optimization.

## Table of Contents
- [Datasets](#datasets)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Methodology](#methodology)
- [Key Findings](#key-findings)
- [Model Interpretability](#model-interpretability)
- [Visualizations](#visualizations)
- [Statistical Analysis](#statistical-analysis)
- [Future Work](#future-work)
- [Contributing](#contributing)
- [License](#license)

## Datasets
The analysis leverages several datasets:

1. **Media_Investment.csv**: Contains monthly marketing channel investments across different channels
   - Columns: Month, Year, Total Investment, TV, Digital, Sponsorship, Content Marketing, Online marketing, Affiliates, SEM, Radio, Other
   - Time period: July 2023 - June 2024
   - Values represent marketing spend in millions

2. **Master.csv**: Contains transaction and product data
   - Key columns: Date/Time, order_date, gmv, product_analytic_category
   - Product categories: Camera, CameraAccessory, EntertainmentSmall, GameCDDVD, GamingHardware
   - Time period: July 2023 - June 2024

3. **month.csv**: Contains aggregated monthly data with additional environmental and performance metrics
   - Located in: CSV Input Files directory
   - Contains metrics like temperature, holiday information, NPS scores, and stock indices
   - Used for hypothesis testing and environmental factor analysis

## Prerequisites
- Python 3.6+
- Jupyter Notebook
- Data analysis libraries (pandas, numpy)
- Machine learning libraries (scikit-learn)
- Model interpretability libraries (LIME, SHAP)
- Visualization libraries (plotly)
- Statistical analysis libraries (scipy.stats)

## Technologies Used

The project leverages a comprehensive suite of technologies for marketing channel analysis:

### Core Technologies
- **Python 3.6+**: Primary programming language
- **Jupyter Notebook**: Interactive development and analysis environment

### Data Processing & Analysis
- **pandas**: Data manipulation, transformation, and time series operations
- **numpy**: Numerical computing and array operations
- **scipy**: Statistical functions and tests

### Machine Learning
- **scikit-learn**: 
  - Random Forest regression for predictive modeling
  - Feature scaling and preprocessing
  - Model evaluation metrics
  - Cross-validation

### Model Interpretability
- **LIME** (Local Interpretable Model-agnostic Explanations): Explains individual predictions
- **SHAP** (SHapley Additive exPlanations): Assigns importance values to features
- **eli5**: Model inspection and visualization

### Statistical Analysis
- **scipy.stats**: Statistical hypothesis testing
- **seaborn**: Statistical data visualization and distribution analysis

### Data Visualization
- **plotly**: Interactive, browser-based visualizations
- **matplotlib**: Static plotting and visualization
- **seaborn**: Statistical data visualization

### Development Tools
- **Git**: Version control
- **Poetry**: Dependency management

## Installation
Clone this repository and install the required packages:

```bash
git clone <repository-url>
cd <repository-directory>
poetry install
```

Required packages:
```
pandas
numpy
scikit-learn
lime
shap
plotly
jupyter
scipy
matplotlib
seaborn
```

## Methodology
The analysis follows these key steps:

1. **Data Loading and Preprocessing**:
   - Loading CSV data files
   - Converting dates to datetime format
   - Creating month-year periods for time-series analysis
   - Handling missing values and duplicates

2. **Data Transformation**:
   - Creating pivot tables to analyze GMV by product category and time period
   - Aggregating data at monthly level
   - Merging marketing investment data with sales data

3. **Feature Engineering**:
   - Scaling features using StandardScaler for model training
   - Aligning time periods between datasets
   - Converting marketing spend to appropriate scale

4. **Model Building**:
   - Training Random Forest regression models to predict GMV based on marketing channels
   - Model selection focused on predictive accuracy and interpretability

5. **Model Interpretation**:
   - Using LIME (Local Interpretable Model-agnostic Explanations) to understand feature importance
   - Leveraging SHAP (SHapley Additive exPlanations) values to explain predictions
   - Analyzing feature impacts across different product categories

6. **Statistical Analysis**:
   - Performing hypothesis testing using Wilcoxon signed-rank test, Mann-Whitney U test, and Kruskal-Wallis test
   - Analyzing investment changes across categories
   - Computing Spearman correlation between categories

## Key Findings
Based on the analysis, we can identify which marketing channels have the strongest influence on sales for each product category:

1. **TV Advertising**:
   - Strong positive impact across all product categories
   - Particularly effective for Camera and GameCDDVD categories
   - Most efficient when investment levels are moderate to high

2. **Digital Marketing**:
   - Mixed effects depending on product category
   - Less effective for Camera and CameraAccessory
   - Shows negative correlation with GamingHardware sales

3. **Sponsorship**:
   - Strong positive impact for EntertainmentSmall products
   - Variable effectiveness across other categories
   - Requires substantial investment to see significant returns

4. **Online Marketing & Affiliates**:
   - Consistent positive impact across most product categories
   - Cost-effective channel with good ROI
   - More effective when coordinated with other channels

5. **SEM (Search Engine Marketing)**:
   - Mixed effectiveness
   - Works better for specific product categories
   - Performance varies significantly by time period

## Model Interpretability
The project employs two advanced techniques for model interpretation:

### LIME Analysis
LIME explains individual predictions by approximating the model locally with an interpretable model. Key insights include:
- TV advertising consistently appears in the top features affecting predictions
- Digital marketing shows variable importance
- Radio advertising often shows negative correlation with sales

The `lime_explanations.json` file contains detailed LIME interpretations for each product category, showing which features have the strongest influence on predictions.

### SHAP Analysis
SHAP values attribute the contribution of each feature to predictions. Findings include:
- For Camera products, TV and Online marketing have the highest impact
- EntertainmentSmall category is most influenced by Sponsorship
- GameCDDVD shows unique patterns, with high influence from Digital advertising

## Statistical Analysis
The `Hypothesis_Testing.py` script implements various statistical tests to validate findings:

1. **Wilcoxon Signed-Rank Test**: Analyzes whether investment changes have a significant impact on sales
2. **Mann-Whitney U Test**: Compares investment effectiveness between first and second half of the year
3. **Kruskal-Wallis Test**: Examines differences in investment effectiveness across product categories
4. **Spearman Correlation**: Measures relationship strength between investments in different categories

These statistical analyses help validate the machine learning model findings and provide additional confidence in the marketing channel recommendations.

## Visualizations
The notebook includes several visualization types:
- Trend analysis of GMV by product category
- Marketing channel effectiveness comparisons
- Feature importance plots from LIME and SHAP
- Interactive Plotly visualizations
- Statistical distribution visualizations using Seaborn

## Future Work
Potential extensions to this analysis include:

1. **Time-Lag Analysis**: Investigate delayed effects of marketing activities on sales
2. **Channel Interaction Effects**: Explore how different marketing channels interact
3. **Advanced Models**: Test neural networks or other ML approaches
4. **Seasonal Adjustments**: Account for seasonality in both marketing and sales data
5. **External Factors**: Incorporate external variables like competitive activity, holidays, and economic indicators
6. **Optimization Models**: Develop models for optimal budget allocation across channels
7. **Causal Inference**: Apply causal inference techniques to better understand true impact of marketing channels

## Contributing
Contributions to this analysis are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

*This README was last updated on March 2024* 