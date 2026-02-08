"""
Text processing utilities
"""
import re
from typing import List


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better context retrieval
    
    Strategy:
    1. Try to break at sentence boundaries (. )
    2. Fall back to paragraph breaks (\n\n)
    3. Last resort: word boundaries
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings in the overlap region
            sentence_end = text.rfind('. ', end - overlap, end)
            if sentence_end != -1 and sentence_end > start:
                end = sentence_end + 1
            else:
                # Fallback to paragraph break
                para_break = text.rfind('\n\n', end - overlap, end)
                if para_break != -1 and para_break > start:
                    end = para_break + 2
                else:
                    # Last resort: word boundary
                    space = text.rfind(' ', end - overlap, end)
                    if space != -1 and space > start:
                        end = space + 1
        
        chunk_text = text[start:end].strip()
        if chunk_text:  # Only add non-empty chunks
            chunks.append(chunk_text)
        
        start = end - overlap if end < len(text) else end
    
    return chunks


def split_markdown_by_headers(markdown_text: str) -> List[tuple]:
    """
    Split markdown text by headers (## or ###) to preserve structure
    
    This helps maintain context when chunking technical documentation.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        List of (header_title, content) tuples
    """
    # Find all headers (## or ### level)
    header_pattern = r'^(#{2,3})\s+(.+)$'
    lines = markdown_text.split('\n')
    
    sections = []
    current_header = None
    current_content = []
    
    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            # Save previous section
            if current_header or current_content:
                content_text = '\n'.join(current_content).strip()
                if content_text:  # Only add non-empty sections
                    sections.append((current_header, content_text))
            
            # Start new section
            current_header = match.group(2).strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Add last section
    if current_header or current_content:
        content_text = '\n'.join(current_content).strip()
        if content_text:
            sections.append((current_header, content_text))
    
    return sections


def extract_version_from_category(category: str) -> str:
    """
    Extract version number from category string
    
    Examples:
        "release_notes26.3" -> "26.3" 
        "release_notes" -> "unknown"
    
    Args:
        category: Category string
        
    Returns:
        Version string (e.g., "26.3") or "unknown"
    """
    # Try to find version pattern like 26.3 or 26_3
    version_match = re.search(r'(\d+)[._](\d+)', category)
    if version_match:
        return f"{version_match.group(1)}.{version_match.group(2)}"
    
    # Try to find just major version
    major_match = re.search(r'(\d+)', category)
    if major_match:
        return major_match.group(1)
    
    return 'unknown'
