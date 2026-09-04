import os
import sys
import time
import datetime
import json
import logging
import gc
import psutil
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our components
from agents.generator import SequentialGenerator
from utils.report import section_questions
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("report_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("report_generation")

# Memory monitoring function
def log_memory_usage():
    """Log current memory usage of the process"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage_mb = memory_info.rss / 1024 / 1024
    logger.info(f"Current memory usage: {memory_usage_mb:.2f} MB")
    return memory_usage_mb

def force_gc():
    """Force garbage collection and log memory before and after"""
    mem_before = log_memory_usage()
    gc.collect()
    mem_after = log_memory_usage()
    logger.info(f"Memory freed by GC: {mem_before - mem_after:.2f} MB")

def get_user_selected_sections() -> List[str]:
    """Allow user to select which sections to generate content for"""
    print("\nAvailable report sections:")
    for i, section in enumerate(section_questions.keys(), 1):
        print(f"{i}. {section.replace('_', ' ').title()}")
    
    print("\nSelect sections to generate (comma-separated numbers, or 'all' for all sections):")
    selection = input("> ").strip()
    
    if selection.lower() == 'all':
        return list(section_questions.keys())
    
    try:
        # Convert comma-separated input to list of integers
        selected_indices = [int(idx.strip()) for idx in selection.split(',')]
        # Convert indices to section names (adjusting for 1-based indexing)
        selected_sections = [list(section_questions.keys())[idx-1] for idx in selected_indices]
        return selected_sections
    except (ValueError, IndexError):
        print("Invalid selection. Defaulting to all sections.")
        return list(section_questions.keys())

def generate_selected_sections(selected_sections: List[str], output_dir: str = None, llm=None, data_path: str = None) -> Dict[str, Any]:
    """
    Generate content for selected sections and append to a single report file.
    
    Args:
        selected_sections: List of section names to generate content for
        output_dir: Directory to save report file (created if doesn't exist)
        llm: Language model to use (created with default if None)
        data_path: Path to the data files
        
    Returns:
        Dict with report generation metadata
    """
    # Create timestamp for this report run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set up output directory
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Report will be saved to: {output_dir}")
    
    # Log initial memory usage
    log_memory_usage()
    
    # Create or append to the report file
    report_path = os.path.join(output_dir, "report.md")
    report_exists = os.path.exists(report_path)
    
    # If file doesn't exist, create it with header
    if not report_exists:
        with open(report_path, "w") as report_file:
            report_file.write(f"# Marketing Report\n\n")
    else:
        # If file exists, update the timestamp
        with open(report_path, "r") as report_file:
            content = report_file.read()
    
    # Process each section and its questions
    all_results = {}
    all_metadata = {}
    
    # Dictionary to store report content by section
    report_dict = {}
    
    # Process each selected section
    for section in selected_sections:
        if section not in section_questions:
            logger.warning(f"Section '{section}' not found in section_questions. Skipping.")
            continue
            
        questions = section_questions[section]
        section_start_time = time.time()
        logger.info(f"Processing section: {section}")
        
        # Create a new generator for each section (to clear memory)
        generator = SequentialGenerator(llm=llm, data_path=data_path)
        logger.info("Sequential Generator initialized for section")
        log_memory_usage()
        
        # Initialize section content
        section_content = f"## {section.replace('_', ' ').title()}\n\n"
        
        # Append section header to report
        with open(report_path, "a") as report_file:
            report_file.write(f"## {section.replace('_', ' ').title()}\n\n")
        
        # Process each question in the section
        for i, question in enumerate(questions):
            question_num = i + 1
            logger.info(f"Processing question {question_num}/{len(questions)} in section '{section}'")
            
            try:
                # Run the analysis
                result = generator.analyze_section(question, section)
                
                # Append to report file and section content
                with open(report_path, "a") as report_file:
                    if "result" in result:
                        report_file.write(result["result"])
                        section_content += result["result"]
                    else:
                        error_msg = f"Error: {result.get('error', 'Unknown error')}"
                        report_file.write(error_msg)
                        section_content += error_msg
                    report_file.write("\n\n---\n\n")
                    section_content += "\n\n---\n\n"
                
                logger.info(f"Added question {question_num} result to report")
                
                # Store only minimal metadata rather than full result
                all_results[f"{section}_{question_num}"] = {
                    "success": "result" in result,
                    "error": result.get("error", None) if "error" in result else None
                }
                
                # Force garbage collection after each question
                force_gc()
                
                # If memory usage is high, restart the generator
                if log_memory_usage() > 4000:  # If memory usage exceeds 4GB
                    logger.warning("Memory usage high, recreating generator")
                    del generator
                    force_gc()
                    generator = SequentialGenerator(llm=llm, data_path=data_path)
                
            except Exception as e:
                error_msg = f"Error processing question {question_num} in section '{section}': {str(e)}"
                logger.error(error_msg)
                logger.exception("Exception details:")
                
                # Add error to report and section content
                error_content = f"### Question {question_num}\n\n**Question:** {question}\n\n**Answer:**\n\nError generating content: {str(e)}\n\n---\n\n"
                with open(report_path, "a") as report_file:
                    report_file.write(error_content)
                section_content += error_content
            
            # Extra GC to keep memory usage low
            force_gc()
        
        # Store section content in dictionary
        report_dict[section] = section_content
        
        section_time = time.time() - section_start_time
        logger.info(f"Section '{section}' completed in {section_time:.2f} seconds")
        all_metadata[section] = {"execution_time": section_time}
        
        # Add extra spacing between sections
        with open(report_path, "a") as report_file:
            report_file.write("\n\n")
        
        # Delete generator and force garbage collection between sections
        del generator
        force_gc()
        
        # Pause between sections to allow memory to stabilize
        logger.info("Pausing for 5 seconds to allow memory to stabilize...")
        time.sleep(5)
    
    # Save the report dictionary to a JSON file
    report_dict_path = os.path.join(output_dir, "report_dict.json")
    try:
        with open(report_dict_path, "w") as json_file:
            json.dump(report_dict, json_file, indent=2)
        logger.info(f"Report dictionary saved to {report_dict_path}")
    except Exception as e:
        logger.error(f"Error saving report dictionary: {str(e)}")
    
    # Log completion
    logger.info(f"Report generation complete. Results saved to {report_path}")
    
    return {
        "report_path": report_path,
        "report_dict_path": report_dict_path,
        "report_dict": report_dict,
        "sections_processed": selected_sections,
        "metadata": all_metadata
    }

def main():
    """Run report generation with user-selected sections."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable not set")
            print("Error: GROQ_API_KEY not found in environment variables")
            return
        
        # Initialize LLM
        llm = ChatGroq(
                model="llama-3.3-70b-versatile",  # Use a smaller model that uses less memory
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key = api_key
        )
        
        # Set data path - adjust as needed
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        # Get user selection for sections
        selected_sections = get_user_selected_sections()
        if not selected_sections:
            print("No sections selected. Exiting.")
            return
            
        print(f"\nGenerating content for sections: {', '.join(s.replace('_', ' ').title() for s in selected_sections)}")
        print("Starting report generation...")
        
        # Generate report for selected sections
        result = generate_selected_sections(selected_sections, llm=llm, data_path=data_path)
        
        print("\nReport generation complete!")
        print(f"Report saved to: {result['report_path']}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.exception("Exception details:")
        print(f"An error occurred: {str(e)}")
        
    finally:
        # Final garbage collection
        force_gc()

if __name__ == "__main__":
    main() 