import os
import sys
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import shutil
import tempfile
import webbrowser
import time
import socket

# Import all analytics modules
try:
    from Customers_Bivariate_EDA import AnalyticsOrchestrator as BivariateAnalytics
    from Customers_Univariate_EDA import AnalyticsOrchestrator as UnivariateAnalytics
    from master_data import DataLoader, RunAnalysis
    from SKU_EDA import ProductAnalytics
    from Weather_Analysis_EDA import WeatherAnalysis
    from Feature import DataLoader as FeatureDataLoader, FeatureEngineer, FeatureEngineeringOrchestrator
    
    # Check if Investment_EDA.py is also available
    if os.path.exists("Investment_EDA.py"):
        try:
            from Investment_EDA import run_analyzer as InvestmentAnalyzer
            has_investment_module = True
        except ImportError:
            has_investment_module = False
    else:
        has_investment_module = False
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required Python files are in the current directory.")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(title="Global Commerce Data Analytics Suite")

# Create necessary directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Create HTML template for the main page
with open("templates/index.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Global Commerce Data Analytics Suite</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            .analysis-card { margin-bottom: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Global Commerce Data Analytics Suite</h1>
            <p class="text-muted">Select an analysis type to begin</p>
        </div>
        
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-body">
                            <h5 class="card-title">Customer Analysis</h5>
                            <div class="d-grid gap-2">
                                <a href="/bivariate" class="btn btn-primary">Bivariate Analysis</a>
                                <a href="/univariate" class="btn btn-primary">Univariate Analysis</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-body">
                            <h5 class="card-title">Product Analysis</h5>
                            <div class="d-grid gap-2">
                                <a href="/master" class="btn btn-primary">Master Data Analysis</a>
                                <a href="/sku" class="btn btn-primary">SKU Analysis</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-body">
                            <h5 class="card-title">Environmental Analysis</h5>
                            <div class="d-grid gap-2">
                                <a href="/weather" class="btn btn-primary">Weather Analysis</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-body">
                            <h5 class="card-title">Financial Analysis</h5>
                            <div class="d-grid gap-2">
                                <a href="/investment" class="btn btn-primary">Investment Analysis</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-body">
                            <h5 class="card-title">Feature Engineering</h5>
                            <div class="d-grid gap-2">
                                <a href="/feature" class="btn btn-primary">Create Enhanced Features</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

# Create HTML template for file upload
with open("templates/upload.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Data File</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            .upload-form { max-width: 500px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="upload-form">
                <h2 class="text-center mb-4">Upload Data File</h2>
                <form action="/upload/{{ analysis_type }}" method="post" enctype="multipart/form-data">
                    <div class="mb-3">
                        {% if analysis_type == "investment" %}
                            <label for="file" class="form-label">Select Excel File</label>
                            <input type="file" class="form-control" id="file" name="file" accept=".xlsx,.xls" required>
                            <small class="form-text text-muted">For Investment Analysis, please upload an Excel file (.xlsx, .xls)</small>
                        {% else %}
                            <label for="file" class="form-label">Select CSV File</label>
                            <input type="file" class="form-control" id="file" name="file" accept=".csv" required>
                            <small class="form-text text-muted">Please upload a CSV file</small>
                        {% endif %}
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Upload and Analyze</button>
                    </div>
                </form>
            </div>
        </div>
    </body>
    </html>
    """)

# Create HTML template for results page
with open("templates/results.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis Results</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            .plot-container { margin-bottom: 30px; }
            .plot-image { max-width: 100%; height: auto; }
            .header { margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 class="text-center">Analysis Results</h2>
                <div class="text-center">
                    <a href="/" class="btn btn-primary">Back to Home</a>
                </div>
            </div>
            
            <div class="row">
                {% for plot in plots %}
                <div class="col-md-6 plot-container">
                    <div class="card">
                        <img src="/static/{{ analysis_type }}_plots/{{ plot }}" class="plot-image" alt="{{ plot }}">
                        <div class="card-body">
                            <h5 class="card-title">{{ plot }}</h5>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """)

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def find_available_port(start_port=8000, max_port=8010):
    """Find an available port starting from start_port"""
    for port in range(start_port, max_port + 1):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")

def ensure_directory_exists(directory):
    """Ensure a directory exists and is empty"""
    if os.path.exists(directory):
        # Clear existing contents
        shutil.rmtree(directory)
    os.makedirs(directory)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Display the main menu"""
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/{analysis_type}", response_class=HTMLResponse)
async def show_upload_form(analysis_type: str):
    """Show the file upload form for the selected analysis"""
    return templates.TemplateResponse("upload.html", {"request": {}, "analysis_type": analysis_type})

@app.post("/upload/{analysis_type}")
async def upload_file(analysis_type: str, file: UploadFile = File(...)):
    """Handle file upload and run analysis"""
    # Check file extension based on analysis type
    if analysis_type == "investment":
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed for investment analysis")
    else:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed for this analysis type")
    
    # Create a temporary file to store the uploaded data
    temp_dir = Path("temp")
    temp_file = temp_dir / f"{analysis_type}_{file.filename}"
    output_dir = f"static/{analysis_type}_plots"
    
    # Ensure output directory exists and is empty
    ensure_directory_exists(output_dir)
    
    try:
        # Save the uploaded file
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run the appropriate analysis based on the type
        if analysis_type == "bivariate":
            try:
                df = pd.read_csv(temp_file)
                analytics = BivariateAnalytics(df)
                analytics.run_analysis()
                # Create plots directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)
                analytics.save_plots(output_dir)
                
                # Verify plots were created
                plots = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
                if not plots:
                    raise Exception("No plots were generated by bivariate analysis")
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in bivariate analysis: {str(e)}"
                )
            
        elif analysis_type == "univariate":
            analytics = UnivariateAnalytics(str(temp_file))
            analytics.run_all_analyses()
            os.makedirs(output_dir, exist_ok=True)
            analytics.save_plots(output_dir)
            
        elif analysis_type == "master":
            data_loader = DataLoader(str(temp_file))
            data = data_loader.load_data()
            data = data_loader.preprocess_data()
            os.makedirs(output_dir, exist_ok=True)
            analyzer = RunAnalysis(data, output_dir)
            analyzer.run_all_analyses()
            
        elif analysis_type == "sku":
            analytics = ProductAnalytics(pd.read_csv(temp_file))
            analytics.generate_all_plots()
            os.makedirs(output_dir, exist_ok=True)
            analytics.save_all_plots(output_dir)
            
        elif analysis_type == "weather":
            try:
                print(f"Starting weather analysis for file: {temp_file}")
                weather = WeatherAnalysis(str(temp_file))
                print("Weather analysis object created")
                os.makedirs(output_dir, exist_ok=True)
                print(f"Output directory created: {output_dir}")
                print("Running all plots for weather analysis...")
                weather.run_all_plots()
                print("Weather analysis completed")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"WEATHER ERROR: {str(e)}\n{error_details}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in weather analysis: {str(e)}\n{error_details}"
                )
            
        elif analysis_type == "investment" and has_investment_module:
            try:
                # Use the run_analyzer function from Investment_EDA
                InvestmentAnalyzer(str(temp_file))
                # Since run_analyzer creates and saves plots directly, we just need to list them
                plots = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
                
                if not plots:
                    raise HTTPException(
                        status_code=500,
                        detail="No plots were generated for investment analysis. Please check if the data format is correct."
                    )
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"ERROR in investment analysis: {str(e)}\n{error_details}")
                raise HTTPException(status_code=500, detail=f"Error in investment analysis: {str(e)}")
                
        elif analysis_type == "feature":
            try:
                # Create feature engineering results directory if it doesn't exist
                feature_results_dir = Path("static/feature_results")
                os.makedirs(feature_results_dir, exist_ok=True)
                
                # Run feature engineering process
                orchestrator = FeatureEngineeringOrchestrator(str(temp_file))
                success = orchestrator.run_process()
                
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail="Feature engineering process failed. Please check if the data format is correct."
                    )
                
                # Copy the engineered data file to the results directory
                output_filepath = orchestrator.output_filepath
                result_file = feature_results_dir / os.path.basename(output_filepath)
                shutil.copy(output_filepath, result_file)
                
                # Create a simple HTML file to show the results
                result_html = feature_results_dir / "feature_results.html"
                sample_data = orchestrator.engineered_data.head(10).to_html(index=False)
                
                with open(result_html, "w") as f:
                    f.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Feature Engineering Results</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                        <style>
                            body {{ padding: 20px; }}
                            .header {{ margin-bottom: 30px; }}
                            .download-link {{ margin-top: 20px; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h2 class="text-center">Feature Engineering Results</h2>
                                <div class="text-center">
                                    <a href="/" class="btn btn-primary">Back to Home</a>
                                </div>
                            </div>
                            
                            <div class="alert alert-success">
                                Feature engineering completed successfully! The enhanced dataset has been created.
                            </div>
                            
                            <div class="download-link text-center">
                                <a href="/download/feature/{os.path.basename(output_filepath)}" class="btn btn-success">
                                    Download Enhanced Dataset
                                </a>
                            </div>
                            
                            <h4>Sample of the Enhanced Dataset:</h4>
                            <div class="table-responsive">
                                {sample_data}
                            </div>
                            
                            <div class="mt-4">
                                <h5>New Features Created:</h5>
                                <ul>
                                    <li>Daily average order value</li>
                                    <li>Weekly average order value</li>
                                    <li>Monthly average order value</li>
                                    <li>Weekly revenue per customer</li>
                                    <li>Monthly revenue per customer</li>
                                </ul>
                            </div>
                        </div>
                    </body>
                    </html>
                    """)
                
                # Return the feature engineering results page
                return HTMLResponse(content=open(result_html, "r").read())
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"ERROR in feature engineering: {str(e)}\n{error_details}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in feature engineering: {str(e)}"
                )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
        
        # Get list of generated plots
        plots = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        if not plots:
            raise HTTPException(
                status_code=500,
                detail=f"No plots were generated for {analysis_type} analysis. Please check if the data format is correct."
            )
        
        # Return the results page with the plots
        return templates.TemplateResponse(
            "results.html",
            {
                "request": {},
                "analysis_type": analysis_type,
                "plots": plots
            }
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_file.exists():
            temp_file.unlink()

@app.get("/results/{analysis_type}")
async def view_results(analysis_type: str):
    """View the results of the analysis"""
    output_dir = f"static/{analysis_type}_plots"
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Results not found")
    
    # Get list of plots
    plots = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    # Return the results page with the plots
    return templates.TemplateResponse(
        "results.html",
        {
            "request": {},
            "analysis_type": analysis_type,
            "plots": plots
        }
    )

@app.get("/download/feature/{filename}")
async def download_feature_file(filename: str):
    """Download a feature engineering result file"""
    file_path = Path(f"static/feature_results/{filename}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/csv"
    )

def main():
    """Run the FastAPI server"""
    try:
        # Find an available port
        port = find_available_port()
        print(f"\nStarting server on port {port}...")
        
        # Start the server in a separate thread
        import threading
        server_thread = threading.Thread(
            target=uvicorn.run, 
            kwargs={
                "app": app, 
                "host": "0.0.0.0", 
                "port": port
            }
        )
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for the server to start
        time.sleep(2)
        
        # Open Chrome with the localhost URL
        url = f'http://localhost:{port}'
        print(f"Opening {url} in Chrome...")
        webbrowser.get('chrome').open(url)
        
        try:
            # Keep the main thread running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down server...")
            sys.exit(0)
            
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 