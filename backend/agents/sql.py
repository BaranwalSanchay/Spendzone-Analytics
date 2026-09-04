import pandas as pd
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq
import os
import glob
from sqlalchemy import create_engine, inspect
import traceback
import sys
import gc
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the data manager
from utils.data_manager import get_data_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sql_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("sql_agent")

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Get GROQ API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found in .env file")

# Determine paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "..", "data")
db_path = os.path.join(data_dir, "marketing_analysis.db")

# Create engine for database connection
engine = create_engine(f"sqlite:///{db_path}")

# Function to load all CSV files into the database using the data manager
def load_csv_files_to_db(data_manager=None):
    """Load all CSV files from the data directory into the database using the data manager."""
    logger.info("Loading CSV files into the database...")
    
    # Track if any tables were created or updated
    tables_created = False
    
    try:
        # Get existing tables in the database
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # If data_manager is provided, use its already loaded dataframes
        if data_manager:
            dataframes = data_manager.get_dataframes()
            
            for table_name, df in dataframes.items():
                # Check if table already exists
                if table_name in existing_tables:
                    logger.info(f"Table '{table_name}' already exists in database")
                    continue
                
                try:
                    logger.info(f"Importing dataframe as table '{table_name}'...")
                    
                    # Clean column names (replace spaces with underscores)
                    df_copy = df.copy()
                    df_copy.columns = [col.replace(' ', '_').lower() for col in df_copy.columns]
                    
                    # Write to database
                    df_copy.to_sql(table_name, engine, index=False, if_exists='replace')
                    tables_created = True
                    logger.info(f"✓ Successfully imported {len(df_copy)} rows to table '{table_name}'")
                    
                    # Free memory
                    del df_copy
                    gc.collect()
                
                except Exception as e:
                    logger.error(f"✗ Error importing {table_name}: {str(e)}")
                    continue
            
            return tables_created
        
        # Fall back to importing CSV files directly if no data manager
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {data_dir}")
            return False
        
        for file_path in csv_files:
            # Get table name from filename (without extension)
            table_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Check if table already exists
            if table_name in existing_tables:
                logger.info(f"Table '{table_name}' already exists in database")
                continue
            
            try:
                logger.info(f"Importing {file_path} as table '{table_name}'...")
                
                # Read CSV file with low memory
                df = pd.read_csv(file_path, low_memory=False)
                
                # Clean column names (replace spaces with underscores)
                df.columns = [col.replace(' ', '_').lower() for col in df.columns]
                
                # Convert date columns to datetime
                for col in df.columns:
                    if 'date' in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        except:
                            pass
                
                # Write to database
                df.to_sql(table_name, engine, index=False, if_exists='replace')
                tables_created = True
                logger.info(f"✓ Successfully imported {len(df)} rows to table '{table_name}'")
                
                # Free memory
                del df
                gc.collect()
            
            except Exception as e:
                logger.error(f"✗ Error importing {file_path}: {str(e)}")
                continue
        
        return tables_created
    
    except Exception as e:
        logger.error(f"Error in load_csv_files_to_db: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Create SQLDatabase object (initialized later to ensure database exists)
db = None

# Function to create and return the SQL agent
def get_sql_agent(llm=None, data_manager=None):
    """
    Create a SQL agent with the marketing database.
    
    Args:
        llm: Language model to use for the agent
        data_manager: Optional DataManager to use for loading data
        
    Returns:
        SQL agent executor and database connection
    """
    global db
    
    try:
        # Check if database exists, if not create it
        if not os.path.exists(db_path):
            logger.info(f"Database not found at {db_path}. Creating new database...")
            load_csv_files_to_db(data_manager)
        else:
            logger.info(f"Using existing database at {db_path}")
            # Check if we need to add any new tables
            load_csv_files_to_db(data_manager)
        
        # Initialize db if not already done
        if db is None:
            db = SQLDatabase(engine=engine)
        
        # Initialize LLM if not provided
        if llm is None:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile", 
                temperature=0, 
                api_key=GROQ_API_KEY
            )
        
        # Create and return the SQL agent
        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="tool-calling",
            verbose=True
        )
        
        return agent_executor, db
    
    except Exception as e:
        logger.error(f"Error creating SQL agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to create SQL agent: {str(e)}")

def main():
    """Test the SQL agent with a basic query."""
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not found in .env file. Cannot continue.")
        return
    
    try:
        # Get the shared data manager
        data_manager = get_data_manager()
        
        # Get the SQL agent
        agent_executor, db = get_sql_agent(data_manager=data_manager)
        
        # Get a list of all tables in the database
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nAvailable tables in the database: {', '.join(tables)}")
        
        # Let the agent describe the database
        print("\nAsking agent to describe the database:")
        result = agent_executor.invoke({"input": "Describe the database schema and list all available tables"})
        print(result["output"])
        
        if tables:
            # Sample query on the first table
            first_table = tables[0]
            print(f"\nRunning sample query on '{first_table}' table:")
            result = agent_executor.invoke({"input": f"Show me 5 rows from the {first_table} table"})
            print(result["output"])
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
