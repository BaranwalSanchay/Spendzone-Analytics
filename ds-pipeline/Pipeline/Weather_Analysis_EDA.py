import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import os
import plotly.io as pio

class WeatherAnalysis:
    def __init__(self, file_path):
        """Initialize with dataset path and process the data"""
        
        self.df = pd.read_csv(file_path)
        print(f"Columns in the dataset: {list(self.df.columns)}")
        self.process_data()
        self.identify_key_columns()

    def process_data(self):
        """Preprocess data: Drop unwanted columns, impute missing values, and set index"""

        # Drop 'Data Quality' column if it exists
        if 'Data Quality' in self.df.columns:
            self.df.drop(columns=['Data Quality'], inplace=True)

        # Drop columns with more than 275 missing values
        cols_to_drop = [col for col in self.df.columns if self.df[col].isnull().sum() > 275]
        self.df.drop(columns=cols_to_drop, inplace=True)

        # Identify date column - try common date column names
        date_column = None
        possible_date_columns = ['Date/Time', 'Date', 'DateTime', 'Time', 'Datetime', 'date', 'date/time', 'DATE']
        
        for col in possible_date_columns:
            if col in self.df.columns:
                date_column = col
                break
        
        # If no standard date column found, look for column names containing 'date'
        if date_column is None:
            for col in self.df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    date_column = col
                    break
        
        # If still no date column, ask user
        if date_column is None:
            print("Could not identify a date column. Available columns are:")
            for i, col in enumerate(self.df.columns):
                print(f"{i}: {col}")
            col_index = int(input("Enter the number of the column that contains date information: "))
            date_column = self.df.columns[col_index]
        
        print(f"Using '{date_column}' as the date column")
        
        # Convert date column to datetime format and set as index
        try:
            # Try with default format first
            self.df[date_column] = pd.to_datetime(self.df[date_column], errors='coerce')
        except:
            # If that fails, try common date formats
            formats = ["%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
            for format in formats:
                try:
                    self.df[date_column] = pd.to_datetime(self.df[date_column], format=format, errors='coerce')
                    if not self.df[date_column].isna().all():
                        print(f"Successfully parsed dates with format: {format}")
                        break
                except:
                    continue
        
        # Rename the date column to 'Date/Time' for consistency with rest of the code
        self.df.rename(columns={date_column: 'Date/Time'}, inplace=True)
        self.df.set_index('Date/Time', inplace=True)
        
        # Check if Year, Month, Day columns exist, create them if not
        if 'Year' not in self.df.columns:
            self.df['Year'] = self.df.index.year
        if 'Month' not in self.df.columns:
            self.df['Month'] = self.df.index.month
        if 'Day' not in self.df.columns:
            self.df['Day'] = self.df.index.day

        # Impute missing values using 15-day rolling mean + Gaussian noise
        std_dev = 0.3
        numeric_cols = self.df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if col not in ['Year', 'Month', 'Day'] and self.df[col].isna().any():
                rolling_mean = self.df[col].rolling(window=15, min_periods=1).mean()
                noise = np.random.normal(0, std_dev, size=len(self.df))
                self.df[col].fillna(rolling_mean + noise, inplace=True)
    
    def identify_key_columns(self):
        """Identify and map standard column names to actual column names in the dataset"""
        # Initialize dictionaries to store column mappings
        self.temp_cols = {}
        self.precip_cols = {}
        self.degree_day_cols = {}
        
        # Check for temperature columns
        temp_patterns = {
            'max_temp': ['max temp', 'maximum temp', 'high temp', 'temp max', 'temp high'],
            'min_temp': ['min temp', 'minimum temp', 'low temp', 'temp min', 'temp low'],
            'mean_temp': ['mean temp', 'avg temp', 'average temp', 'temp avg', 'temp mean']
        }
        
        for key, patterns in temp_patterns.items():
            for col in self.df.columns:
                for pattern in patterns:
                    if pattern in col.lower():
                        self.temp_cols[key] = col
                        break
                if key in self.temp_cols:
                    break
        
        # Check for precipitation columns
        precip_patterns = {
            'rain': ['rain', 'rainfall', 'precipitation rain'],
            'snow': ['snow', 'snowfall', 'precipitation snow']
        }
        
        for key, patterns in precip_patterns.items():
            for col in self.df.columns:
                for pattern in patterns:
                    if pattern in col.lower():
                        self.precip_cols[key] = col
                        break
                if key in self.precip_cols:
                    break
        
        # Check for degree day columns
        degree_day_patterns = {
            'heat_deg_days': ['heat', 'hdd', 'heating degree'],
            'cool_deg_days': ['cool', 'cdd', 'cooling degree']
        }
        
        for key, patterns in degree_day_patterns.items():
            for col in self.df.columns:
                for pattern in patterns:
                    if pattern in col.lower() and 'deg' in col.lower():
                        self.degree_day_cols[key] = col
                        break
                if key in self.degree_day_cols:
                    break
        
        # Print identified columns
        print("\nIdentified temperature columns:")
        for key, col in self.temp_cols.items():
            print(f"  {key}: {col}")
        
        print("\nIdentified precipitation columns:")
        for key, col in self.precip_cols.items():
            print(f"  {key}: {col}")
        
        print("\nIdentified degree day columns:")
        for key, col in self.degree_day_cols.items():
            print(f"  {key}: {col}")
            
    def plot_temperature_trends(self):
        """Plot Max, Min, and Mean Temperature as separate subplots"""
        
        # Check if we have temperature columns
        if not self.temp_cols:
            print("No temperature columns found in dataset.")
            return [None, None]
        
        fig = make_subplots(rows=len(self.temp_cols), cols=1, shared_xaxes=True,
                           subplot_titles=[col.replace('_', ' ').title() for col in self.temp_cols.keys()])
        
        # Add traces for each temperature column
        row = 1
        for key, col in self.temp_cols.items():
            fig.add_trace(go.Scatter(x=self.df.index, y=self.df[col], mode='lines', name=key.replace('_', ' ').title()), 
                         row=row, col=1)
            row += 1
        
        fig.update_layout(title="Temperature Trends Over Time", height=900, showlegend=False)
        fig.show()
        
        # Create a second figure with all temperature series on the same plot
        if self.temp_cols:
            fig2 = px.line(self.df, x=self.df.index, y=list(self.temp_cols.values()),
                         title="Temperature Trends Over Time",
                         labels={'value': 'Temperature (°C)', 'index': 'Date/Time'})
            
            # Rename the traces to be more user-friendly
            for i, key in enumerate(self.temp_cols.keys()):
                new_name = key.replace('_', ' ').title()
                fig2.data[i].name = new_name
            
            fig2.update_layout(legend_title="Temperature Type", showlegend=True)
            fig2.show()
            return [fig, fig2]
        
        return [None, None]

    def avg_monthly_temp(self):
        """Plot Avg Monthly Temperatures"""
        
        # Check if we have a mean temperature column
        if 'mean_temp' not in self.temp_cols:
            print("No mean temperature column found in dataset.")
            return None
        
        mean_temp_col = self.temp_cols['mean_temp']
        
        # Group by month and calculate mean
        monthly_avg_temp = self.df.groupby('Month')[mean_temp_col].mean().reset_index()
        
        if monthly_avg_temp.empty or monthly_avg_temp[mean_temp_col].isna().all():
            print("No valid data for monthly temperature analysis.")
            return None
            
        fig = px.bar(monthly_avg_temp, x='Month', y=mean_temp_col,
                   title="Average Monthly Temperature", 
                   labels={mean_temp_col: 'Temperature (°C)'})
        
        fig.show()
        return fig

    def corr_plot(self):
        """Plots Correlation Matrix"""
        
        # Check if we have enough numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            print("Not enough numeric columns for correlation analysis.")
            return None
            
        # Drop Year column if it exists
        corr_df = self.df.drop('Year', axis=1) if 'Year' in self.df.columns else self.df
        
        # Calculate correlation matrix
        corr_matrix = corr_df.select_dtypes(include=[np.number]).corr().round(2)
        
        if corr_matrix.empty:
            print("Correlation matrix is empty.")
            return None
            
        fig = ff.create_annotated_heatmap(z=corr_matrix.values, 
                                        x=list(corr_matrix.columns), 
                                        y=list(corr_matrix.index),
                                        colorscale='Viridis')
        fig.update_layout(title="Correlation Heatmap")
        fig.show()
        return fig

    def box_plot(self):
        """Box Plot to Detect Outliers"""
        
        # Check if we have a mean temperature column
        if 'mean_temp' not in self.temp_cols:
            print("No mean temperature column found in dataset.")
            return None
            
        mean_temp_col = self.temp_cols['mean_temp']
        
        fig = px.box(self.df, y=mean_temp_col, title="Boxplot of Mean Temperature")
        fig.show()
        return fig
        
    def plot_rolling_mean_temperature(self, window=30):
        """Plot Mean Temperature with its rolling mean over a specified window."""
        
        # Check if we have a mean temperature column
        if 'mean_temp' not in self.temp_cols:
            print("No mean temperature column found in dataset.")
            return None

        mean_temp_col = self.temp_cols['mean_temp']
            
        df_temp = self.df.copy()  # Prevent modifying the original DataFrame
        df_temp['Rolling Mean Temp'] = df_temp[mean_temp_col].rolling(window=window).mean()

        fig = px.line(df_temp, x=df_temp.index, y=[mean_temp_col, 'Rolling Mean Temp'],
                    title=f"{window}-Day Rolling Mean of Temperature",
                    labels={'value': 'Temperature (°C)', 'index': 'Date/Time'})
        
        # Rename the traces
        fig.data[0].name = "Mean Temperature"
        fig.data[1].name = f"{window}-Day Rolling Mean"
        
        fig.show()
        return fig

    def temp_distribution(self):
        """Plot temperature distribution"""
        
        # Check if we have a mean temperature column
        if 'mean_temp' not in self.temp_cols:
            print("No mean temperature column found in dataset.")
            return None
            
        mean_temp_col = self.temp_cols['mean_temp']
        
        fig = px.histogram(self.df, x=mean_temp_col, nbins=30, marginal='box', 
                         title="Distribution of Mean Temperature", histnorm='probability density')
        fig.show()
        return fig

    def plot_heat_degree_days(self):
        """Plot Heat Degree Days (HDD) over time if available"""
        
        # Check if we have a heat degree days column
        if 'heat_deg_days' not in self.degree_day_cols:
            print("No heat degree days column found in dataset.")
            return None
            
        hdd_col = self.degree_day_cols['heat_deg_days']
        
        fig = px.line(self.df, x=self.df.index, y=hdd_col, 
                    title="Heat Degree Days Trend Over Time", 
                    labels={hdd_col: 'HDD (°C)'})
        fig.show()
        return fig
            
    def rain_snow_trends(self):
        """Plot Rainfall and Snowfall Trends"""
        
        # Check if we have precipitation columns
        if not self.precip_cols:
            print("No precipitation columns found in dataset.")
            return None
            
        valid_precip_cols = list(self.precip_cols.values())
        
        monthly_precip = self.df.groupby('Month')[valid_precip_cols].sum().reset_index()

        if monthly_precip.empty:
            print("No valid data for precipitation analysis.")
            return None
            
        fig = px.bar(monthly_precip, x='Month', y=valid_precip_cols,
                  title="Total Rain & Snow by Month", barmode='stack')
                  
        # Rename the traces
        for i, key in enumerate(self.precip_cols.keys()):
            new_name = key.replace('_', ' ').title()
            fig.data[i].name = new_name
            
        fig.show()
        return fig

    def plot_rolling_mean_precipitation(self, window=30):
        """Plot rolling mean for Rain and Snow"""
        
        # Check if we have precipitation columns
        if not self.precip_cols:
            print("No precipitation columns found in dataset.")
            return None
            
        valid_precip_cols = list(self.precip_cols.values())
        
        if valid_precip_cols:
            df_precip = self.df.copy()
            
            for col in valid_precip_cols:
                df_precip[f'Rolling {col}'] = df_precip[col].rolling(window=window).mean()

            plot_cols = valid_precip_cols + [f'Rolling {col}' for col in valid_precip_cols]
            
            fig = px.line(df_precip, x=df_precip.index, y=plot_cols,
                        title=f"{window}-Day Rolling Mean for Precipitation",
                        labels={'value': 'Precipitation', 'index': 'Date/Time'})
                        
            # Rename the traces
            for i, col in enumerate(valid_precip_cols):
                for key, val in self.precip_cols.items():
                    if val == col:
                        fig.data[i].name = key.replace('_', ' ').title()
                        fig.data[i + len(valid_precip_cols)].name = f"{window}-Day Rolling {key.replace('_', ' ').title()}"
            
            fig.show()
            return fig
        
        return None

    def plot_precipitation_vs_temperature(self):
        """Scatter plot of Total Precipitation vs. Mean Temperature"""
        
        # Check if we have temperature and precipitation columns
        if 'mean_temp' not in self.temp_cols or not self.precip_cols:
            print("Missing temperature or precipitation columns.")
            return None
            
        mean_temp_col = self.temp_cols['mean_temp']
        valid_precip_cols = list(self.precip_cols.values())

        if valid_precip_cols:
            # Compute Total Precipitation (sum of all precipitation columns)
            self.df['Total Precipitation'] = self.df[valid_precip_cols].sum(axis=1)

            # Create Scatter Plot
            fig = px.scatter(self.df, x=mean_temp_col, y='Total Precipitation', 
                           color=self.df.index.month, 
                           title="Precipitation vs Temperature",
                           labels={mean_temp_col: 'Temperature (°C)', 
                                 'Total Precipitation': 'Total Precipitation', 
                                 'color': 'Month'},
                           opacity=0.6)
            fig.show()
            return fig
        
        return None

    def plot_cool_degree_days(self):
        """Plot Cool Degree Days (CDD) over time if available"""
        
        # Check if we have a cool degree days column
        if 'cool_deg_days' not in self.degree_day_cols:
            print("No cool degree days column found in dataset.")
            return None
            
        cdd_col = self.degree_day_cols['cool_deg_days']
        
        fig = px.line(self.df, x=self.df.index, y=cdd_col, 
                    title="Cool Degree Days Trend Over Time", 
                    labels={cdd_col: 'CDD (°C)'})
        fig.show()
        return fig

    def plot_hdd_cdd_trends(self):
        """Plot both HDD and CDD on the same graph"""
        
        # Check if we have degree day columns
        if not self.degree_day_cols:
            print("No degree day columns found in dataset.")
            return None
            
        valid_degree_day_cols = list(self.degree_day_cols.values())

        if valid_degree_day_cols:
            fig = px.line(self.df, x=self.df.index, y=valid_degree_day_cols,
                        title="Degree Days Trends Over Time", 
                        labels={'value': 'Degree Days (°C)'})
                        
            # Rename the traces
            for i, key in enumerate(self.degree_day_cols.keys()):
                new_name = key.replace('_', ' ').replace('deg', 'Degree').title()
                fig.data[i].name = new_name
                
            fig.show()
            return fig
        
        return None
    
    def save_plots_to_folder(self, figures, folder_name="Graphs_Weather"):
        """Save all the generated plots to a folder as PNG files"""
        
        # Create directory if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"Created directory: {folder_name}")
            
        # Save each figure
        saved_count = 0
        for i, fig in enumerate(figures):
            if fig is not None:
                try:
                    filename = f"{folder_name}/plot_{i+1}.png"
                    print(f"Attempting to save figure {i+1} to {filename}")
                    
                    # Use pio.write_image instead of fig.write_image
                    pio.write_image(fig, filename, format='png', engine='kaleido')
                    
                    print(f"Saved: {filename}")
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving figure {i+1}: {str(e)}")
                    # Try alternative approach
                    try:
                        print("Trying alternative save method...")
                        if hasattr(fig, 'write_image'):
                            fig.write_image(filename)
                            print(f"Saved with alternative method: {filename}")
                            saved_count += 1
                    except Exception as alt_e:
                        print(f"Alternative save method also failed: {str(alt_e)}")
                        
        print(f"Saved {saved_count} plots to {folder_name}/")
    
    def run_all_plots(self):
        """Automatically run all visualization methods and save figures"""
        figures = []
        
        try:
            print("Running correlation plot...")
            figures.append(self.corr_plot())
            
            print("Running temperature trends plot...")
            figures.extend(self.plot_temperature_trends())
            
            print("Running monthly temperature plot...")
            figures.append(self.avg_monthly_temp())
            
            print("Running temperature distribution plot...")
            figures.append(self.temp_distribution())
            
            print("Running rolling mean temperature plot...")
            figures.append(self.plot_rolling_mean_temperature())
            
            print("Running rain/snow trends plot...")
            figures.append(self.rain_snow_trends())
            
            print("Running rolling mean precipitation plot...")
            figures.append(self.plot_rolling_mean_precipitation())
            
            print("Running precipitation vs temperature plot...")
            figures.append(self.plot_precipitation_vs_temperature())
            
            print("Running box plot...")
            figures.append(self.box_plot())
            
            print("Running heat degree days plot...")
            figures.append(self.plot_heat_degree_days())
            
            print("Running cool degree days plot...")
            figures.append(self.plot_cool_degree_days())
            
            print("Running HDD/CDD trends plot...")
            figures.append(self.plot_hdd_cdd_trends())
            
            # Save all figures
            print("Saving all plots...")
            self.save_plots_to_folder(figures)
            print("All plots saved successfully")
            
        except Exception as e:
            import traceback
            print(f"Error in weather analysis: {str(e)}")
            print(traceback.format_exc())
            
            # Try to save any figures that were generated before the error
            if figures:
                print(f"Attempting to save {len(figures)} figures that were generated before the error...")
                self.save_plots_to_folder(figures)
            
            # Re-raise the exception
            raise Exception(f"Error in weather analysis: {str(e)}")

if __name__ == "__main__":
    # Ask for CSV file input
    file_path = input("Enter the path to your weather CSV file: ")
    weather = WeatherAnalysis(file_path)
    weather.run_all_plots()
