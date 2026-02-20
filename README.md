# Uber Eats Restaurant Analysis Dashboard

A comprehensive data analysis application built with Python and Streamlit for analyzing Uber Eats restaurant brand performance.

## Features

### 🏠 Home Dashboard
- Dataset overview and key metrics
- Data quality checks
- Quick insights and statistics

### 📊 Merchant Scoring
- Customizable merchant scoring system
- Tier classification (Gold, Silver, Bronze)
- Top and bottom performer identification
- Improvement opportunity analysis

### 💰 Fee Optimization
- Marketplace fee optimization recommendations
- Revenue impact analysis
- Price elasticity modeling
- Fee structure analysis

### 📈 Unit Economics
- Profitability analysis by brand
- Cost breakdown (courier, processing, defects, acquisition)
- Contribution margin calculations
- Growth scenario modeling

### 📊 Presentation Charts
- Executive-ready visualizations
- Multiple chart types for different analyses
- Data export capabilities
- Professional formatting for presentations

## Project Structure

```
uber-eats-analysis/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── .gitignore                     # Git ignore file
├── data/
│   └── restaurant_data.xlsx       # Excel file with data (you need to add this)
├── utils/
│   ├── data_loader.py            # Data loading and processing
│   ├── scoring.py                # Merchant scoring logic
│   └── calculations.py           # Fee optimization and unit economics
└── pages/
    ├── 1_Merchant_Scoring.py     # Merchant scoring analysis page
    ├── 2_Fee_Optimization.py     # Fee optimization page
    ├── 3_Unit_Economics.py       # Unit economics page
    └── 4_Presentation_Charts.py  # Presentation charts page
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Steps

1. **Navigate to the project directory:**
   ```bash
   cd uber-eats-analysis
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Add your data file:**
   - Place your Excel file (`restaurant_data.xlsx`) in the `data/` folder
   - The Excel file should contain two sheets:
     - "Restaurant Brands Dataset" (200 rows, 10 columns)
     - "Demographic Data"

## Running the Application

1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser:**
   - The app should automatically open in your default browser
   - If not, navigate to `http://localhost:8501`

3. **Navigate through the pages:**
   - Use the sidebar to switch between different analysis pages
   - Each page provides interactive visualizations and analysis tools

## Data Requirements

### Restaurant Brands Dataset
Expected columns:
- Brand Name
- Annualized Trips
- Active Locations
- Total Locations
- % Franchised
- Avg. Basket Size
- Marketplace Fee
- %Orders from First Time Eaters
- Order Defect Rate
- Avg. Courier Wait Time (min)

### Demographic Data
- Structure depends on your specific demographic dataset

## Usage Guide

### Merchant Scoring
1. Navigate to the "Merchant Scoring" page
2. Adjust scoring weights in the sidebar
3. View tier distribution, top/bottom performers
4. Identify improvement opportunities

### Fee Optimization
1. Go to "Fee Optimization" page
2. Set price elasticity and target revenue in sidebar
3. Review optimization recommendations
4. Analyze revenue impact
5. Download recommendations as CSV

### Unit Economics
1. Open "Unit Economics" page
2. Adjust cost assumptions in sidebar
3. Set growth scenario parameters
4. Review profitability analysis
5. Export growth projections

### Presentation Charts
1. Access "Presentation Charts" page
2. Select chart type from dropdown
3. View high-quality visualizations
4. Export data as CSV for further analysis

## Customization

### Adjusting Scoring Weights
Modify weights in the sidebar of the Merchant Scoring page to reflect your business priorities.

### Cost Assumptions
Update cost assumptions in the Unit Economics sidebar to match your actual costs.

### Growth Scenarios
Adjust growth percentages to model different business scenarios.

## Troubleshooting

### Data Loading Issues
- Ensure the Excel file is in the `data/` folder
- Check that sheet names match exactly: "Restaurant Brands Dataset" and "Demographic Data"
- Verify all required columns are present

### Package Installation Issues
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

## Development

### Adding New Features
- Utility functions go in `utils/` folder
- New analysis pages go in `pages/` folder (numbered prefix for ordering)
- Update main `app.py` for new navigation items

### Code Structure
- Data loading: `utils/data_loader.py`
- Business logic: `utils/scoring.py` and `utils/calculations.py`
- UI/Visualization: Page files in `pages/` folder

## Technologies Used

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **NumPy**: Numerical computations
- **Matplotlib & Seaborn**: Additional plotting capabilities
- **openpyxl**: Excel file handling

## License

This project is created for educational and interview purposes.

## Contact

Created for Uber Eats case study interview.

---

**Good luck with your interview! 🚀**
