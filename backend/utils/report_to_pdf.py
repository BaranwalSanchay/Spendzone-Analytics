import os
import sys
import re
import base64
import markdown
from datetime import datetime
from pathlib import Path
import logging
from bs4 import BeautifulSoup
from weasyprint import HTML, CSS
import glob

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("report_to_pdf")

# Directory paths
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = PROJECT_ROOT / "reports"
PLOTS_DIR = PROJECT_ROOT /"agents"/"plots"
if not PLOTS_DIR.exists():
    PLOTS_DIR.mkdir(exist_ok=True)

def clean_markdown(md_content):
    """Clean up the markdown content to better handle the specific report structure and remove questions"""
    # Remove the last updated line
    md_content = re.sub(r'\*Last updated:.*?\*\n', '', md_content)
    
    # First, let's split the content into sections by horizontal rules
    sections = re.split(r'---\n+', md_content)
    cleaned_sections = []
    
    for section in sections:
        if not section.strip():
            continue
            
        # Check if this section has a main heading
        section_title_match = re.search(r'^##\s+(.+?)$', section, re.MULTILINE)
        if not section_title_match:
            continue
            
        section_title = section_title_match.group(1).strip()
        
        # For 'Business Context' section, handle specially because it may not follow the standard format
        if "business context" in section_title.lower():
            # Just clean up any question markers but keep all content
            section_cleaned = re.sub(r'### Question \d+\n', '', section)
            section_cleaned = re.sub(r'\*\*Question:\*\*.*?\n\n', '', section_cleaned)
            section_cleaned = re.sub(r'\*\*Answer:\*\*\n\n', '', section_cleaned)
            section_cleaned = re.sub(r'<think>.*?</think>', '', section_cleaned, flags=re.DOTALL)
            
            # Ensure we preserve all content after the main heading
            content_after_heading = section_cleaned.split(section_title_match.group(0), 1)[-1].strip()
            if content_after_heading:
                cleaned_sections.append(f"## {section_title}\n\n{content_after_heading}")
            else:
                cleaned_sections.append(f"## {section_title}")
            
            continue
            
        # Extract the main section content before any questions
        main_content = section_title_match.group(0)
        
        # Extract all answers and combine them, removing question headers and question text
        answers = []
        
        # Look for all answer blocks in this section
        answer_blocks = re.findall(r'\*\*Answer:\*\*\n\n(.*?)(?=(?:\n\n### Question \d+)|$)', section, re.DOTALL)
        
        for answer_text in answer_blocks:
            # If there's a <think> tag, remove it and its contents
            answer_text = re.sub(r'<think>.*?</think>', '', answer_text, flags=re.DOTALL)
            if answer_text.strip():
                answers.append(answer_text.strip())
        
        # If we have answers, combine them with the main section content
        if answers:
            combined_section = f"## {section_title}\n\n{' '.join(answers)}"
            cleaned_sections.append(combined_section)
        # If no answers were found but there's content after the heading, preserve it
        elif section.split(section_title_match.group(0), 1)[-1].strip():
            content_after_heading = section.split(section_title_match.group(0), 1)[-1].strip()
            # Remove any question/answer markers
            content_after_heading = re.sub(r'### Question \d+\n', '', content_after_heading)
            content_after_heading = re.sub(r'\*\*Question:\*\*.*?\n\n', '', content_after_heading)
            content_after_heading = re.sub(r'\*\*Answer:\*\*\n\n', '', content_after_heading)
            content_after_heading = re.sub(r'<think>.*?</think>', '', content_after_heading, flags=re.DOTALL)
            
            if content_after_heading.strip():
                cleaned_sections.append(f"## {section_title}\n\n{content_after_heading.strip()}")
            else:
                # No content, just use the original section heading
                cleaned_sections.append(f"## {section_title}")
        else:
            # No answers found, just use the original section heading
            cleaned_sections.append(f"## {section_title}")
    
    # Join all sections with proper separators
    result = "\n\n---\n\n".join(cleaned_sections)
    
    # Final cleanup of any remaining duplicate headings
    lines = result.split('\n')
    seen_headings = {}
    filtered_lines = []
    
    for line in lines:
        heading_match = re.match(r'^(#+)\s+(.+)$', line)
        if heading_match:
            level, text = heading_match.groups()
            key = f"{level}:{text.strip()}"
            if key in seen_headings:
                # Skip duplicate heading
                continue
            seen_headings[key] = True
        filtered_lines.append(line)
    
    result = '\n'.join(filtered_lines)
    
    # Remove any "### Question X" lines that might remain
    result = re.sub(r'### Question \d+\n', '', result)
    
    # Remove any "**Question:**" and "**Answer:**" markers that might remain
    result = re.sub(r'\*\*Question:\*\*.*?\n\n', '', result)
    result = re.sub(r'\*\*Answer:\*\*\n\n', '', result)
    
    return result

def improve_headings(html_content):
    """Improve headings in the HTML content to ensure proper hierarchy and styling"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Add IDs to headings for better navigation
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for heading in headings:
        heading_text = heading.get_text().strip()
        # Create a URL-friendly ID from heading text
        heading_id = re.sub(r'[^a-zA-Z0-9_-]', '-', heading_text.lower())
        heading_id = re.sub(r'-+', '-', heading_id)
        heading['id'] = heading_id
        
        # Add a class based on heading level
        heading['class'] = heading.get('class', []) + [f'heading-{heading.name}']
    
    # Add special styling to section h2 headings
    section_headings = soup.find_all('h2')
    for heading in section_headings:
        heading['class'] = heading.get('class', []) + ['section-heading']
    
    # Add special styling to question h3 headings
    question_headings = soup.find_all('h3')
    for heading in question_headings:
        heading['class'] = heading.get('class', []) + ['question-heading']
    
    return str(soup)

def find_plots():
    """Find all plots and return them as a dictionary of filename: path pairs"""
    plot_files = {}
    
    # Look for plot files in the plots directory
    for plot_path in glob.glob(str(PLOTS_DIR / "*.png")):
        plot_name = os.path.basename(plot_path)
        plot_files[plot_name] = plot_path
    
    # Also look for any PNG files in the reports directory
    for plot_path in glob.glob(str(REPORTS_DIR / "*.png")):
        plot_name = os.path.basename(plot_path)
        plot_files[plot_name] = plot_path
    
    logger.info(f"Found {len(plot_files)} plot files: {list(plot_files.keys())}")
    return plot_files

def insert_plots_into_html(html_content, plot_files):
    """Locate appropriate sections in the HTML and insert relevant plots with better grouping"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get all sections (both main sections and question sections)
    sections = soup.find_all(['h2', 'h3'])
    
    # Keep track of remaining plots that need to go in the supporting viz section
    plots_inserted = 0
    unmatched_plots = []
    
    keywords_map = {
        'roi': ['roi', 'return', 'investment', 'marketing_roi', 'channel'],
        'gmv': ['gmv', 'revenue', 'sales', 'merchandise'],
        'nps': ['nps', 'score', 'satisfaction', 'promoter'],
        'sla': ['sla', 'service', 'level', 'agreement'],
        'budget': ['budget', 'allocation', 'spend', 'cost'],
        'discount': ['discount', 'price', 'promotion', 'offer'],
        'kpi': ['kpi', 'performance', 'indicator', 'metric'],
        'stock': ['stock', 'index', 'market', 'financial']
    }
    
    # Go through each plot file and try to match it with relevant sections
    for plot_name, plot_path in plot_files.items():
        plot_name_lower = plot_name.lower()
        matched = False
        
        # Identify relevant keywords in the plot name
        plot_keywords = set()
        for category, keywords in keywords_map.items():
            if any(keyword in plot_name_lower for keyword in keywords):
                plot_keywords.add(category)
        
        # Try to find a matching section for each plot
        for section in sections:
            section_text = section.text.lower()
            
            # Check if plot keywords match section content
            if any(category in section_text for category in plot_keywords):
                # Try to find a good insertion point - right after this section heading
                parent = section.parent
                next_sibling = section.find_next_sibling()
                
                # Create image element with caption
                img_div = soup.new_tag('div', attrs={'class': 'plot-container'})
                img = soup.new_tag('img', attrs={
                    'src': f"file://{plot_path}",
                    'class': 'plot-image',
                    'alt': f"Plot: {plot_name}"
                })
                img_div.append(img)
                
                # Add caption
                caption = soup.new_tag('p', attrs={'class': 'plot-caption'})
                caption.string = f"Figure: {plot_name.replace('_', ' ').replace('.png', '')}"
                img_div.append(caption)
                
                # Insert after the section heading or before the next sibling
                if next_sibling:
                    next_sibling.insert_before(img_div)
                else:
                    parent.append(img_div)
                
                matched = True
                plots_inserted += 1
                logger.info(f"Inserted plot {plot_name} into section '{section.text}'")
                break
        
        # If no match found, add to unmatched list
        if not matched:
            unmatched_plots.append((plot_name, plot_path))
    
    # If we have unmatched plots, add them to a Supporting Visualizations section in a grid
    if unmatched_plots:
        # Check if we already created the supporting visualizations section
        viz_section = soup.find('h2', string='Supporting Visualizations')
        if not viz_section:
            viz_section = soup.new_tag('h2')
            viz_section.string = 'Supporting Visualizations'
            viz_section['class'] = ['section-heading']
            soup.append(viz_section)
        
        # Create a grid container for the plots
        grid_div = soup.new_tag('div', attrs={'class': 'supporting-viz'})
        viz_section.insert_after(grid_div)
        
        # Add each plot to the grid
        for plot_name, plot_path in unmatched_plots:
            # Create grid item
            grid_item = soup.new_tag('div', attrs={'class': 'viz-item'})
            
            # Add image
            img = soup.new_tag('img', attrs={
                'src': f"file://{plot_path}",
                'class': 'plot-image',
                'alt': f"Plot: {plot_name}"
            })
            grid_item.append(img)
            
            # Add caption
            caption = soup.new_tag('p', attrs={'class': 'plot-caption'})
            caption.string = f"Figure: {plot_name.replace('_', ' ').replace('.png', '')}"
            grid_item.append(caption)
            
            # Add to grid
            grid_div.append(grid_item)
            plots_inserted += 1
        
        logger.info(f"Added {len(unmatched_plots)} plots to Supporting Visualizations grid")
    
    logger.info(f"Inserted {plots_inserted} plots into the report")
    return str(soup)

def create_table_of_contents(html_content):
    """Create a simplified table of contents with only main section headings"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find only h2 headings (main sections)
    main_headings = soup.find_all('h2')
    
    if not main_headings:
        return html_content
    
    # Create TOC container
    toc_div = soup.new_tag('div', attrs={'class': 'table-of-contents'})
    toc_title = soup.new_tag('h2')
    toc_title.string = 'Table of Contents'
    toc_div.append(toc_title)
    
    # Main TOC list
    toc_list = soup.new_tag('ul', attrs={'class': 'toc-list'})
    toc_div.append(toc_list)
    
    # Track headings to avoid duplicates
    seen_headings = {}
    
    # Process each main heading
    for heading in main_headings:
        text = heading.get_text().strip()
        
        # Skip TOC heading itself
        if text.lower() == 'table of contents':
            continue
            
        # Skip if we've seen this heading before (case-insensitive comparison)
        if text.lower() in seen_headings:
            continue
            
        # Fix special cases
        if "Performance Drivers" in text and "#" in text:
            text = "Performance Drivers"
            heading.string = text
        
        if "Marketing ROI" in text or "Marketing Roi" in text:
            text = "Marketing ROI"
            heading.string = text
        
        # Ensure heading has ID for linking
        if not heading.get('id'):
            heading_id = re.sub(r'[^a-zA-Z0-9_-]', '-', text.lower())
            heading_id = re.sub(r'-+', '-', heading_id)
            heading['id'] = heading_id
        else:
            heading_id = heading['id']
        
        # Create section list item
        section_li = soup.new_tag('li', attrs={'class': 'toc-item toc-section'})
        section_a = soup.new_tag('a', href=f"#{heading_id}")
        section_a.string = text
        section_li.append(section_a)
        toc_list.append(section_li)
        
        # Mark as seen
        seen_headings[text.lower()] = True
    
    # Insert TOC at beginning of document
    first_heading = soup.find('h2')
    if first_heading:
        first_heading.insert_before(toc_div)
    else:
        soup.body.insert(0, toc_div)
    
    return str(soup)

def markdown_to_pdf(md_path, output_pdf=None, title="Marketing Analysis Report", company_name="ACME Corporation"):
    """Convert markdown report to PDF with improved styling and plot integration"""
    try:
        if output_pdf is None:
            output_pdf = REPORTS_DIR / "marketing_report.pdf"
        
        logger.info(f"Converting {md_path} to PDF: {output_pdf}")
        
        # Read and clean markdown content
        with open(md_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()
        
        md_content = clean_markdown(md_content)
        
        # Find all plots
        plot_files = find_plots()
        logger.info(f"Found {len(plot_files)} plot files")
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists']
        )
        
        # Improve headings in the HTML
        html_content = improve_headings(html_content)
        
        # Insert plots into HTML - now with better grouping
        html_content = insert_plots_into_html(html_content, plot_files)
        
        # Create table of contents
        html_content = create_table_of_contents(html_content)

        # Create HTML document with CSS styling
        html_doc = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                @page {{
                    size: letter;
                    margin: 1in;
                    @bottom-center {{
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }}
                }}
                
                body {{
                    font-family: 'Calibri', 'Arial', sans-serif;
                    font-size: 11pt;
                    line-height: 1.5;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}
                
                /* Enhanced Title Page */
                .title-page {{
                    height: 80vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    position: relative;
                    border-left: 10px solid #3498db;
                    padding-left: 40px;
                }}
                
                .title-page::before {{
                    content: "";
                    position: absolute;
                    top: 0;
                    right: 0;
                    bottom: 0;
                    width: 25%;
                    background: linear-gradient(to bottom right, rgba(52, 152, 219, 0.1), rgba(52, 152, 219, 0.05));
                    z-index: -1;
                }}
                
                .title-page::after {{
                    content: "";
                    position: absolute;
                    right: 40px;
                    bottom: 100px;
                    width: 150px;
                    height: 150px;
                    border: 5px solid rgba(52, 152, 219, 0.2);
                    border-radius: 50%;
                    z-index: -1;
                }}
                
                .report-title {{
                    font-size: 36pt;
                    font-weight: 700;
                    color: #2980b9;
                    margin: 0 0 20px 0;
                }}
                
                .report-subtitle {{
                    font-size: 16pt;
                    color: #555;
                    margin: 0 0 60px 0;
                    font-weight: 400;
                }}
                
                .report-company {{
                    font-size: 18pt;
                    font-weight: 600;
                    margin-top: 60px;
                    color: #333;
                }}
                
                /* Table of Contents */
                .table-of-contents {{
                    margin: 2em 0 3em 0;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 2em;
                }}
                
                .table-of-contents h2 {{
                    color: #2980b9;
                    border-left: 5px solid #3498db;
                    padding-left: 10px;
                }}
                
                .toc-list {{
                    list-style-type: none;
                    padding-left: 1em;
                }}
                
                .toc-item {{
                    margin-bottom: 0.8em;
                    font-size: 12pt;
                }}
                
                .toc-item a {{
                    text-decoration: none;
                    color: #333;
                }}
                
                .toc-section {{
                    font-weight: bold;
                }}
                
                /* Content Styling */
                .content {{
                    margin-top: 2em;
                }}
                
                h2 {{
                    border-left: 5px solid #3498db;
                    padding-left: 10px;
                    margin-top: 1.8em;
                    color: #2980b9;
                    /* Remove page breaks between sections */
                    page-break-before: auto;
                }}
                
                h3 {{
                    color: #2c3e50;
                    margin-top: 1.5em;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 0.3em;
                }}
                
                /* Plot Styling */
                .plot-container {{
                    margin: 1.5em 0;
                    text-align: center;
                }}
                
                .plot-grid {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    align-items: center;
                }}
                
                .plot-grid-item {{
                    flex: 0 0 48%;
                    margin: 1%;
                }}
                
                .plot-image {{
                    max-width: 100%;
                    max-height: 400px;
                    object-fit: contain;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                .plot-caption {{
                    font-size: 10pt;
                    color: #666;
                    margin-top: 0.5em;
                    font-style: italic;
                }}
                
                p {{
                    margin-bottom: 1em;
                    text-align: justify;
                }}
                
                ul, ol {{
                    margin-bottom: 1em;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1.5em 0;
                }}
                
                th, td {{
                    border: 1px solid #ddd;
                    padding: 0.5em;
                }}
                
                th {{
                    background-color: #f2f7fa;
                    font-weight: bold;
                }}
                
                .highlight {{
                    background-color: #f2f7fa;
                    border-left: 4px solid #3498db;
                    padding: 1em;
                    margin: 1.5em 0;
                }}
                
                .metric {{
                    font-size: a4pt;
                    color: #2874a6;
                    font-weight: 600;
                }}
                
                /* CSS additions for TOC */
                .table-of-contents {{
                    margin: 2em 0 4em 0;
                }}
                
                .table-of-contents h2 {{
                    color: #2980b9;
                    border-left: 5px solid #3498db;
                    padding-left: 10px;
                    margin-bottom: 1.5em;
                    page-break-before: avoid;
                }}
                
                .toc-list {{
                    list-style-type: none;
                    padding-left: 1em;
                }}
                
                .toc-subsection-list {{
                    list-style-type: none;
                    padding-left: 2em;
                    margin-top: 0.5em;
                    margin-bottom: 0.5em;
                }}
                
                .toc-item {{
                    margin-bottom: 0.7em;
                }}
                
                .toc-item a {{
                    text-decoration: none;
                    color: #333;
                }}
                
                .toc-item a:hover {{
                    text-decoration: underline;
                    color: #3498db;
                }}
                
                .toc-section {{
                    font-weight: bold;
                    color: #2c3e50;
                    margin-top: 1em;
                }}
                
                .toc-level-3 {{
                    font-weight: normal;
                    margin-left: 1em;
                }}
                
                .toc-level-4 {{
                    font-weight: normal;
                    font-style: italic;
                    margin-left: 1.5em;
                }}
                
                /* Supporting visualizations grid */
                .supporting-viz {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }}
                
                .viz-item {{
                    width: 48%;
                    margin-bottom: 2em;
                }}
            </style>
        </head>
        <body>
            <div class="title-page">
                <h1 class="report-title">{title}</h1>
                <p class="report-subtitle">Performance Analysis & Strategic Recommendations</p>
                <p class="report-company">{company_name}</p>
            </div>
            
            <div class="content">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        # Convert HTML to PDF
        HTML(string=html_doc).write_pdf(
            output_pdf,
            stylesheets=[
                CSS(string='@page { size: letter; margin: 1in; }')
            ]
        )
        
        logger.info(f"PDF report generated successfully: {output_pdf}")
        return str(output_pdf)
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Process the markdown report and convert to PDF"""
    try:
        md_path = REPORTS_DIR / "report.md"
        
        if not md_path.exists():
            logger.error(f"Report file not found: {md_path}")
            print(f"Error: Report file not found at {md_path}")
            return
        
        output_pdf = REPORTS_DIR / "marketing_report.pdf"
        pdf_path = markdown_to_pdf(md_path, output_pdf)
        
        if pdf_path:
            print(f"\nPDF report generated successfully!")
            print(f"Location: {pdf_path}")
        else:
            print("Error generating PDF report. Check the logs for details.")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 