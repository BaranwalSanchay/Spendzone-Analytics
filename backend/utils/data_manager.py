import os
import pandas as pd
import glob
import logging
from typing import Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("data_manager")

class DataManager:
    """
    Centralized data manager for loading and providing dataframes to all agents.
    This class follows the Singleton pattern to ensure only one instance exists.
    """
    _instance = None
    
    def __new__(cls, data_path=None):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, data_path=None):
        # Only initialize once
        if self._initialized:
            return
            
        self.data_path = data_path
        self.dataframes = {}
        self._load_data()
        self._initialized = True
        
    def _load_data(self):
        """Load data from CSV file or directory."""
        logger.info(f"Loading data from {self.data_path}")
        
        # Configure pandas to limit output size
        pd.set_option('display.max_rows', 20)
        pd.set_option('display.max_columns', 10)
        pd.set_option('display.width', 80)
        pd.set_option('display.max_colwidth', 30)
        
        try:
            if os.path.isdir(self.data_path):
                # Load all CSV files in the directory
                csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
                for file_path in csv_files:
                    table_name = os.path.basename(file_path).replace(".csv", "")
                    df = pd.read_csv(file_path)
                    self.dataframes[table_name] = df
                    logger.info(f"Loaded {table_name} with {len(df)} rows and {len(df.columns)} columns")
            else:
                # Load single CSV file
                df = pd.read_csv(self.data_path)
                
                # Convert numeric columns and handle NaN values
                numeric_columns = ['gmv', 'sla', 'NPS_Score', 'product_mrp', 'units']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Convert order_date to datetime if available
                if 'order_date' in df.columns:
                    df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
                
                # Use 'master' as the default table name for single files
                self.dataframes['master'] = df
                logger.info(f"Loaded master with {len(df)} rows and {len(df.columns)} columns")
            
            logger.info(f"Successfully loaded {len(self.dataframes)} dataframes")
        
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_dataframes(self) -> Dict[str, pd.DataFrame]:
        """Get all loaded dataframes."""
        return self.dataframes
    
    def get_dataframe(self, name: str) -> Optional[pd.DataFrame]:
        """Get a specific dataframe by name."""
        return self.dataframes.get(name)
    
    def get_schema_info(self) -> str:
        """Generate schema information about all loaded dataframes."""
        schema_info = "Available Data Tables:\n\n"
        
        for table_name, df in self.dataframes.items():
            schema_info += f"Table: {table_name}\n"
            schema_info += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
            schema_info += "Columns:\n"
            
            # Get column info with types
            for col in df.columns:
                dtype = df[col].dtype
                sample = str(df[col].iloc[0]) if len(df) > 0 else "N/A"
                if len(sample) > 30:
                    sample = sample[:27] + "..."
                schema_info += f"  - {col} ({dtype}), Sample: {sample}\n"
            
            schema_info += "\n"
        
        return schema_info

def get_data_manager(data_path=None):
    """Get or create the DataManager instance."""
    if data_path is None:
        # Default data path
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    
    return DataManager(data_path) 