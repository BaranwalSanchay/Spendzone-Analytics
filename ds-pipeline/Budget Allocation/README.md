# Marketing Budget Allocation Optimization

## Table of Contents
1. [Introduction](#introduction)
2. [Dataset Information](#dataset-information)
3. [Project Description](#project-description)
4. [File Structure](#file-structure)
5. [Technologies Used](#technologies-used)
6. [Installation & Setup](#installation--setup)
7. [Models and Methodology](#models-and-methodology)
8. [Visualization and Analysis](#visualization-and-analysis)
9. [Interpreting Results](#interpreting-results)
10. [Comparison: Time Series vs. Static Budget Allocation](#comparison-time-series-vs-static-budget-allocation)
11. [Robyn Implementation](#robyn-implementation)
12. [Case Study](#case-study-interpreting-results-for-marketing-strategy)
13. [Mathematical Foundations](#mathematical-foundations)
14. [Limitations and Considerations](#limitations-and-considerations)
15. [Future Enhancements](#future-enhancements)
16. [Conclusion](#conclusion)

## Introduction

This project provides tools for optimizing marketing budget allocation across various channels to maximize predicted revenue (Gross Merchandise Value - GMV). It utilizes advanced mathematical modeling techniques to determine the most effective distribution of marketing budgets across different channels based on their performance characteristics and historical data.

The solution addresses a common challenge in marketing: how to allocate a limited budget across multiple channels to achieve maximum return on investment. By analyzing historical performance data, the model identifies the most effective channels and suggests optimal allocation strategies that evolve over time.

## Dataset Information

The model uses several datasets located in the CSV Input Files directory:

1. **Monthly_Master.csv**: Primary dataset containing monthly marketing spend and performance metrics
   - Marketing channel columns: `TV`, `Digital`, `Sponsorship`, `Content Marketing`, `Online marketing`, `Affiliates`, `SEM`, `Radio`, `Other`
   - Performance metrics: `gmv` (Gross Merchandise Value)
   - Time period: July 2023 - June 2024

2. **Final_monthly.csv**: Processed dataset with optimized allocations
   - Contains the results of budget allocation optimization

3. **Monthly_updated.csv**: Enhanced dataset with additional variables for advanced modeling
   - Includes environmental factors and derived metrics

The models require historical marketing data with the following structure:
- **Month_Year**: Date in YYYY-MM format
- **Marketing channel columns**: Investment amounts for each channel
- **Total Investment**: Total marketing budget for each month
- **gmv**: Gross Merchandise Value (revenue metric)

## Project Description

This project implements three complementary approaches to marketing budget allocation optimization:

1. **Time Series Approach** (`Budget_Allocation_Time_Series.ipynb`): Incorporates temporal effects such as adstock (carryover from previous periods) and adapts allocations month by month, learning from previous results.

2. **Bi-level Optimization** (`Budget_Bioptimisation.ipynb`): Uses bilevel optimization to find a single consistent allocation strategy that can be applied uniformly across periods while respecting channel-specific constraints.

3. **Robyn Framework** (`Robyn.ipynb`): Implements Meta's open-source marketing mix modeling framework for advanced attribution and budget allocation.

All approaches leverage non-linear response models to capture the diminishing returns typical in marketing channels and employ advanced optimization techniques to maximize predicted revenue within budget constraints.

## File Structure

The Budget Allocation directory is organized as follows:

```
Budget Allocation/
├── README.md                        # This documentation file
├── Budget_Allocation_Time_Series.ipynb  # Time series optimization approach
├── Budget_Bioptimisation.ipynb      # Bi-level optimization approach  
├── Robyn.ipynb                      # Meta's Robyn implementation
├── bilevel_optimization_results_constrained.csv  # Optimization results
├── Final_monthly.csv                # Processed final dataset
│
├── CSV Input Files/                 # Input data directory
│   ├── Monthly_Master.csv           # Primary dataset with marketing data
│   ├── Final_monthly.csv            # Dataset with optimized allocations
│   └── Monthly_updated.csv          # Enhanced dataset with additional variables
│
└── Plots/                           # Visualization outputs
    ├── Budget_Allocation_Time_Series_Plots/  # Time series model visualizations
    ├── Budget_Allocation_Plots/     # Static allocation model visualizations
    └── Robyn_Plots/                 # Robyn model visualizations
```

## Technologies Used

The project leverages a comprehensive suite of technologies:

### Core Technologies
- **Python 3.6+**: Primary programming language
- **Jupyter Notebook**: Interactive development and analysis environment

### Data Processing
- **pandas**: Data manipulation and time series analysis
- **numpy**: Numerical computing and array operations

### Mathematical Optimization
- **scipy.optimize**: Provides `minimize` and `curve_fit` functions
- **bilevel optimization**: Custom implementation for hierarchical optimization

### Machine Learning
- **scikit-learn**: Metrics and evaluation tools

### Statistical Modeling
- **Meta Robyn**: Open-source Marketing Mix Modeling (MMM) framework
- **Time series modeling**: Custom implementation for temporal effects

### Data Visualization
- **matplotlib**: Core plotting library
- **seaborn**: Statistical data visualization
- **plotly** (optional): Interactive visualization

## Installation & Setup

To run the notebooks in this project:

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Required packages:
```
pandas
numpy
matplotlib
seaborn
scipy
scikit-learn
plotly (optional)
```

4. Run the Jupyter notebooks:
```bash
jupyter notebook
```

## Models and Methodology

### Time Series Approach (Budget_Allocation_Time_Series.ipynb)

This approach models marketing channel effectiveness over time with these key components:

1. **Effectiveness Function**: Non-linear model capturing diminishing returns
   ```python
   def effectiveness_func(x, alpha, mu):
       return alpha * (1 - np.exp(-mu * x))
   ```

2. **Adstock Modeling**: Captures carryover effects from previous periods
   ```python
   def adstock_transformation(x, decay_rate):
       result = x.copy()
       for i in range(1, len(x)):
           result[i] += decay_rate * result[i-1]
       return result
   ```

3. **Sequential Optimization**: Month-by-month budget allocation with learning

4. **Constraint Handling**: Ensures allocations respect total budget and channel-specific constraints

### Bilevel Optimization Approach (Budget_Bioptimisation.ipynb)

This approach uses a hierarchical optimization structure:

1. **Upper Level**: Finds optimal channel weights that maximize overall GMV
2. **Lower Level**: Applies these weights to allocate budget within constraints
3. **Constraints Handling**: Incorporates channel-specific upper and lower bounds
4. **Normalization**: Ensures weights sum to 1 and all channels receive appropriate allocations

### Robyn Implementation (Robyn.ipynb)

Meta's Robyn framework provides a full Marketing Mix Modeling solution:

1. **Automated MMM**: Builds multiple model versions with different hyperparameters
2. **Prophet Integration**: Handles seasonality and trend decomposition
3. **Ridge Regression**: Regularized modeling to prevent overfitting
4. **Budget Allocation**: Advanced scenario planning and optimization

## Visualization and Analysis

The project generates comprehensive visualizations saved in the "Plots" directory:

1. **Channel Effectiveness Visualization**:
   - Individual channel response curves
   - Comparative effectiveness across channels

2. **Allocation Strategy Visualization**:
   - Percentage allocation by channel over time
   - Absolute values of budget allocation

3. **Performance Metrics**:
   - RMSE (Root Mean Square Error) for each channel's model fit
   - Overall RMSE for combined model prediction

### Visualization Details

All plots are automatically saved to specific folders within the "Plots/" directory based on the model approach. Key visualizations include:

#### 1. Channel Effectiveness
This plot shows all marketing channels' effectiveness curves together. The x-axis represents spend amount, and the y-axis shows the estimated contribution to GMV. Channels with steeper initial slopes provide better returns at low spend levels.

#### 2. Individual Channel Effectiveness
For each channel (e.g., "Online marketing"), a dedicated plot shows observed contributions based on historical data and the fitted effectiveness curve.

#### 3. Allocation Fractions Over Time
This time-series plot shows how the optimal percentage allocation to each channel evolves month by month.

#### 4. Absolute Allocation Over Time
Similar to the fractions plot, but showing actual budget amounts.

## Interpreting Results

When analyzing these visualizations, look for:

1. **Effectiveness Comparisons**: Channels with curves that rise quickly and reach higher maximum values typically deserve larger budget allocations.

2. **Saturation Points**: Where curves begin to flatten significantly marks the point of diminishing returns. Allocating beyond this point is inefficient.

3. **Consistency in Allocation**: Channels consistently receiving higher allocations across months indicate stable high-performers in your marketing mix.

4. **Adaptation Over Time**: Changes in allocation patterns over time demonstrate how the model adapts to new information and optimizes strategy.

5. **Budget Sensitivity**: Compare months with different total budgets to understand how optimal allocation strategy changes with budget constraints.

## Comparison: Time Series vs. Static Budget Allocation

The project includes two main approaches, each with distinct advantages:

### Time Series Approach (Budget_Allocation_Time_Series.ipynb)
**Advantages:**
- Captures temporal dynamics and carryover effects
- Adapts allocations based on recent performance
- Models channel-specific decay rates
- Provides month-by-month guidance

**Best for:**
- Dynamic marketing environments
- Seasonal businesses
- When historical patterns show temporal dependencies

### Static Allocation (Budget_Bioptimisation.ipynb)
**Advantages:**
- Finds a consistent allocation strategy
- Simpler to implement in practice
- Provides stable, predictable allocations
- Respects channel-specific constraints

**Best for:**
- Stable marketing environments
- Long-term planning
- When simplicity and consistency are valued

### Performance Comparison
The notebooks include comparison metrics showing the performance difference between approaches. Typically, the time series approach achieves slightly better overall performance but requires more complex implementation.

## Robyn Implementation

The `Robyn.ipynb` notebook implements Meta's open-source Marketing Mix Modeling framework, which provides:

1. **Advanced Modeling Features**:
   - Automated hyperparameter tuning
   - Built-in adstock and saturation modeling
   - Ridge regression with regularization
   - Prophet integration for trend and seasonality

2. **Unique Capabilities**:
   - Media decomposition analysis
   - ROAS (Return on Ad Spend) calculation
   - Budget scenario planning
   - Optimization with diminishing returns

3. **Visualization**:
   - Model fit diagnostics
   - Media decomposition plots
   - Response curves
   - Budget allocation recommendations

The Robyn implementation serves as a benchmark and validation for the custom approaches.

## Case Study: Interpreting Results for Marketing Strategy

The following insights are based on the model outputs:

### Key Findings
- **Online Marketing**: Consistently the highest performer with a steep response curve
- **Affiliates**: Strong performance with good ROI at medium investment levels
- **TV**: Shows diminishing returns at high spend levels
- **Digital**: Mixed performance with high variability

### Strategic Implementation

Based on these findings, the marketing team could implement the following strategy:

1. **Gradual Reallocation**:
   - Shift budget from TV and Digital toward Online Marketing and Affiliates
   - Implement changes gradually over 3-4 months to monitor actual performance
   - Keep small allocations to SEM to maintain presence

2. **Testing and Validation**:
   - Run A/B tests comparing historical and optimized allocations
   - Monitor performance metrics weekly
   - Re-optimize quarterly with new data

3. **Spending Efficiency**:
   - Ensure spending in Online Marketing and Affiliates stays below saturation points
   - Consider reallocating TV budget to test new channels not in the current mix
   - Focus SEM spend on highest converting keywords only

4. **Long-term Planning**:
   - Use the time-series projections to plan for seasonal budget adjustments
   - Build in flexibility for major market events
   - Develop contingency plans for channels that underperform

By following this data-driven approach, the marketing team can maximize ROI while maintaining a balanced channel mix that aligns with both short and long-term business objectives.

## Mathematical Foundations

### Non-linear Response Functions

The core mathematical foundation of this model is the use of non-linear response functions to accurately represent the relationship between marketing spend and returns.

#### Exponential Saturation Model

The primary effectiveness function used is:

$$f(x) = \alpha \cdot (1 - e^{-\mu \cdot x})$$

Where:
- $x$ is the spend amount
- $\alpha$ is the maximum potential contribution (asymptotic limit)
- $\mu$ is the rate parameter controlling the curve's steepness

### Bilevel Optimization

The bilevel optimization approach solves the following problem:

**Upper level (weight optimization):**
$$\max_{\mathbf{w}} \sum_{t=1}^{T} \sum_{i=1}^{n} f_i(x_{i,t}(\mathbf{w}))$$

**Lower level (budget allocation):**
$$x_{i,t}(\mathbf{w}) = \frac{w_i}{\sum_{j=1}^{n} w_j} \cdot B_t$$

Subject to constraints:
- $\sum_{i=1}^{n} x_{i,t} = B_t$ for all $t$ (budget constraint)
- $x_{i,t} \geq 0$ for all $i,t$ (non-negativity)
- $x_{i,t} \leq u_i$ for some $i,t$ (upper bounds for specific channels)

### Time Series with Adstock

The time series model incorporates adstock effects:

$$A_{i,t} = x_{i,t} + \theta_i \cdot A_{i,t-1}$$

Where:
- $A_{i,t}$ is the adstock-transformed value at time $t$ for channel $i$
- $x_{i,t}$ is the raw spend at time $t$ for channel $i$
- $\theta_i$ is the decay rate for channel $i$

## Limitations and Considerations

Important considerations when using these models:

1. **Data Requirements**:
   - Models require sufficient historical data with variation in spending
   - Performance degrades with limited or homogeneous data

2. **Model Assumptions**:
   - Channel independence (interaction effects not modeled)
   - Stationary channel effectiveness over time
   - Simplified carryover dynamics

3. **Implementation Challenges**:
   - Requires expertise to interpret and implement
   - May recommend radical shifts that are operationally challenging
   - External factors may not be fully captured

4. **Practical Limitations**:
   - Channel constraints often extend beyond simple upper/lower bounds
   - Media buying practicalities may limit implementing exact recommendations
   - Organization readiness for data-driven allocation

## Future Enhancements

Potential improvements to the models:

1. **Model Enhancements**:
   - Incorporating channel interaction effects
   - More sophisticated adstock modeling (e.g., delayed effects)
   - Bayesian approaches for uncertainty estimation
   - Deep learning for complex pattern recognition

2. **External Factors**:
   - Competitor activity modeling
   - Market condition variables
   - Seasonality and calendar effects
   - Consumer sentiment indicators

3. **Implementation Tools**:
   - Interactive dashboard for scenario planning
   - Automated data pipeline for continuous optimization
   - Confidence intervals for recommendations
   - A/B testing framework for validation

4. **Advanced Techniques**:
   - Multi-objective optimization (balancing revenue, profit, and growth)
   - Reinforcement learning for adaptive allocation
   - Causal inference methods for improved attribution

## Conclusion

The Budget Allocation project provides a comprehensive suite of tools for optimizing marketing spend across channels. By leveraging non-linear response models, sophisticated optimization techniques, and time-series analysis, the project enables data-driven decisions that maximize marketing ROI.

The three complementary approaches (Time Series, Bilevel Optimization, and Robyn) offer flexibility to adapt to different business contexts and requirements. Each approach has unique strengths, and together they provide robust guidance for marketing budget allocation.

By implementing the insights and recommendations from these models, marketing teams can achieve more efficient resource allocation, improved campaign performance, and stronger business results.

---

*This README was last updated on March 2024* 