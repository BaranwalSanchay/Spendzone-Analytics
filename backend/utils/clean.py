import re

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

# Read the original report.md
with open('reports/report.md', 'r', encoding='utf-8') as file:
    original_content = file.read()

# Clean the markdown content
cleaned_content = clean_markdown(original_content)

# Write the cleaned content back to report.md
with open('reports/report.md', 'w', encoding='utf-8') as file:
    file.write(cleaned_content)

print("Report cleaned and updated successfully.")