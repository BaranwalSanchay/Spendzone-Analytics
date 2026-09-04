import os
import sys
import time
import datetime
import logging
from pathlib import Path
import gc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("marketing_report")

# Import LLM
from langchain_groq import ChatGroq

# Import our modules
from agents.report_generator import SupervisorAgent
from utils.report import section_questions
from utils.report_to_pdf import markdown_to_pdf
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = PROJECT_ROOT / "reports"
if not REPORTS_DIR.exists():
    REPORTS_DIR.mkdir(exist_ok=True)

def force_gc():
    """Force garbage collection to free up memory"""
    collected = gc.collect()
    logger.info(f"Garbage collection: collected {collected} objects")

def format_section_title(section):
    """Format section name for display"""
    return section.replace('_', ' ').title()

def generate_markdown_report():
    """Generate a complete marketing report and save it as markdown"""
    # Load environment variables
    load_dotenv()
    
    # Initialize output file
    md_file = REPORTS_DIR / "report.md"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Write header to markdown file
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# Marketing Report\n\n")
        f.write(f"*Last updated: {timestamp}*\n\n")
    
    # Initialize LLM
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY environment variable not found")
        return None
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0, 
        api_key=api_key
    )
    
    # Initialize the supervisor agent
    logger.info("Initializing SupervisorAgent...")
    report_generator = SupervisorAgent(llm)
    
    # Track sections processed for reporting
    total_sections = len(section_questions)
    processed_sections = 0
    
    # Set pause times
    SECTION_PAUSE = 10  # seconds between sections
    QUESTION_PAUSE = 5  # seconds between questions
    
    # Generate each section
    for section, questions in section_questions.items():
        processed_sections += 1
        section_title = format_section_title(section)
        logger.info(f"[{processed_sections}/{total_sections}] Generating {section_title} section...")
        
        # Process each question in the section
        for i, question in enumerate(questions):
            logger.info(f"Processing question: {question[:100]}...")
            
            try:
                # Generate content for this section/question
                start_time = time.time()
                result = report_generator.analyze(question, section)
                
                # Append results to markdown file
                with open(md_file, 'a', encoding='utf-8') as f:
                    f.write(f"## {section_title}\n\n")
                    f.write(f"### Question {i+1}\n\n")
                    f.write(f"**Question:** {question}\n\n")
                    f.write(f"**Answer:**\n\n")
                    
                    if "result" in result:
                        f.write(f"{result['result']}\n\n")
                        logger.info(f"✓ Generated in {time.time() - start_time:.2f} seconds")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        f.write(f"Error generating content: {error_msg}\n\n")
                        logger.error(f"✗ Error: {error_msg}")
                
                # Add section separator
                with open(md_file, 'a', encoding='utf-8') as f:
                    f.write("---\n\n\n\n")
                
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
                with open(md_file, 'a', encoding='utf-8') as f:
                    f.write(f"Error: {str(e)}\n\n---\n\n")
            
            # Force garbage collection to free memory
            force_gc()
            
            # Add delay between questions to avoid rate limiting
            if i < len(questions) - 1:
                logger.info(f"Waiting {QUESTION_PAUSE} seconds before next question...")
                time.sleep(QUESTION_PAUSE)
        
        # Add longer delay between sections to avoid rate limiting
        if processed_sections < total_sections:
            logger.info(f"Waiting {SECTION_PAUSE} seconds before next section...")
            time.sleep(SECTION_PAUSE)
    
    logger.info(f"Markdown report generated: {md_file}")
    return md_file

def main():
    """Generate marketing report and convert to PDF"""
    try:
        logger.info("Starting marketing report generation...")
        
        # Generate markdown report
        md_file = generate_markdown_report()
        if not md_file:
            logger.error("Failed to generate markdown report")
            return
        
        # Convert markdown to PDF
        logger.info("Converting markdown to PDF...")
        output_pdf = REPORTS_DIR / "marketing_report.pdf"
        pdf_path = markdown_to_pdf(md_file, output_pdf, title="Marketing Analysis Report")
        
        if pdf_path:
            logger.info(f"PDF report generated: {pdf_path}")
            print(f"\nMarketing report generation complete!")
            print(f"Report saved to: {pdf_path}")
        else:
            logger.error("Failed to convert markdown to PDF")
            print("Error: Failed to convert markdown to PDF")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"An error occurred: {str(e)}")
        
    finally:
        # Final garbage collection
        force_gc()

if __name__ == "__main__":
    main()