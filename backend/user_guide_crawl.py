import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import urljoin, urlparse
import hashlib

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from pydantic import BaseModel, Field

# ============================================================================
# Configuration
# ============================================================================

class DocumentChunk(BaseModel):
    """Schema for individual knowledge chunks"""
    chunk_id: str = Field(description="Unique identifier for the chunk")
    content: str = Field(description="The actual text content")
    title: str = Field(description="Section or page title")
    category: str = Field(description="Category: release_notes, user_guide, api_docs, etc.")
    source_url: str = Field(description="Original URL")
    parent_page_title: str = Field(description="Parent document title")
    topic_tags: List[str] = Field(description="Relevant topic tags")
    priority: str = Field(description="high, medium, or low priority")
    word_count: int = Field(description="Number of words in chunk")
    section_hierarchy: str = Field(description="Breadcrumb of section location")
    last_updated: str = Field(description="Timestamp of crawl")

class KnowledgeBase(BaseModel):
    """Complete knowledge base structure"""
    metadata: Dict[str, Any]
    chunks: List[DocumentChunk]
    statistics: Dict[str, Any]

# ============================================================================
# Configuration
# ============================================================================

CONFIG = {
    "seed_urls": {
        "release_notes": [
            "https://developer.apple.com/documentation/watchos-release-notes/watchos-26_3-release-notes",
            "https://developer.apple.com/documentation/watchos-release-notes/watchos-26_2-release-notes",
            "https://developer.apple.com/documentation/watchos-release-notes/watchos-26_1-release-notes",
            "https://developer.apple.com/documentation/watchos-release-notes/watchos-26-release-notes",
            "https://developer.apple.com/documentation/Xcode-Release-Notes/xcode-26-release-notes"
        ],
        "user_guide": [
            "https://support.apple.com/en-in/guide/watch/apd2054d0d5b/watchos"
        ]
    },
    "output_dir": Path("./apple_watch_kb"),
    "max_depth": 3,  # How deep to crawl from seed URLs
    "chunk_size": 500,  # Target words per chunk
    "chunk_overlap": 100,  # Overlap between chunks
    "delay_between_requests": 2.0,  # Be respectful
}

CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)

# ============================================================================
# URL Management
# ============================================================================

class URLManager:
    """Manages crawled and pending URLs"""
    
    def __init__(self):
        self.visited = set()
        self.pending = []
        self.categorized_urls = {}
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL should be crawled"""
        parsed = urlparse(url)
        
        # Must be same domain
        if base_domain not in parsed.netloc:
            return False
        
        # Skip non-English pages
        if '/guide/watch/' in url and '/en-' not in url and url != "https://support.apple.com/en-in/guide/watch/apd2054d0d5b/watchos":
            return False
        
        # Skip downloads, images, etc.
        skip_extensions = {'.pdf', '.zip', '.dmg', '.jpg', '.png', '.gif', '.mp4', '.mov'}
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip fragments
        if '#' in url:
            url = url.split('#')[0]
        
        return url not in self.visited
    
    def add_urls(self, urls: List[str], category: str, depth: int):
        """Add new URLs to pending queue"""
        for url in urls:
            if url not in self.visited:
                self.pending.append({
                    'url': url,
                    'category': category,
                    'depth': depth
                })
    
    def get_next(self):
        """Get next URL to crawl"""
        if self.pending:
            return self.pending.pop(0)
        return None
    
    def mark_visited(self, url: str):
        """Mark URL as visited"""
        self.visited.add(url)

# ============================================================================
# Content Processing
# ============================================================================

class ContentProcessor:
    """Process and chunk crawled content"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def extract_sections(self, html_content: str, markdown_content: str) -> List[Dict[str, Any]]:
        """Extract logical sections from content"""
        sections = []
        
        # Try to parse markdown first (better structured)
        if markdown_content:
            sections = self._parse_markdown_sections(markdown_content)
        
        return sections if sections else self._fallback_chunking(markdown_content or html_content)
    
    def _parse_markdown_sections(self, markdown: str) -> List[Dict[str, Any]]:
        """Parse markdown into semantic sections"""
        sections = []
        lines = markdown.split('\n')
        current_section = {
            'title': '',
            'content': [],
            'level': 0,
            'hierarchy': []
        }
        hierarchy_stack = []
        
        for line in lines:
            # Detect headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # Save previous section
                if current_section['content']:
                    sections.append(current_section.copy())
                
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # Update hierarchy
                while hierarchy_stack and hierarchy_stack[-1]['level'] >= level:
                    hierarchy_stack.pop()
                
                hierarchy_stack.append({'level': level, 'title': title})
                
                current_section = {
                    'title': title,
                    'content': [],
                    'level': level,
                    'hierarchy': [h['title'] for h in hierarchy_stack]
                }
            else:
                if line.strip():
                    current_section['content'].append(line)
        
        # Add last section
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def _fallback_chunking(self, content: str) -> List[Dict[str, Any]]:
        """Fallback to simple paragraph-based chunking"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        sections = []
        for i, para in enumerate(paragraphs):
            if len(para.split()) > 20:  # Skip very short paragraphs
                sections.append({
                    'title': f'Section {i+1}',
                    'content': [para],
                    'level': 1,
                    'hierarchy': [f'Section {i+1}']
                })
        
        return sections
    
    def create_chunks(self, sections: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Create overlapping chunks from sections"""
        chunks = []
        
        for section in sections:
            section_text = '\n'.join(section['content'])
            words = section_text.split()
            
            # Skip very short sections
            if len(words) < 30:
                continue
            
            # If section is small enough, create single chunk
            if len(words) <= self.chunk_size:
                chunk = self._create_chunk(
                    content=section_text,
                    title=section['title'],
                    hierarchy=section['hierarchy'],
                    metadata=metadata
                )
                if chunk:
                    chunks.append(chunk)
            else:
                # Split into overlapping chunks
                start = 0
                chunk_num = 1
                
                while start < len(words):
                    end = start + self.chunk_size
                    chunk_words = words[start:end]
                    chunk_text = ' '.join(chunk_words)
                    
                    chunk = self._create_chunk(
                        content=chunk_text,
                        title=f"{section['title']} (Part {chunk_num})",
                        hierarchy=section['hierarchy'],
                        metadata=metadata
                    )
                    if chunk:
                        chunks.append(chunk)
                    
                    start += (self.chunk_size - self.overlap)
                    chunk_num += 1
        
        return chunks
    
    def _create_chunk(self, content: str, title: str, hierarchy: List[str], metadata: Dict[str, Any]) -> DocumentChunk:
        """Create a single chunk with metadata"""
        # Skip empty content
        if not content.strip():
            return None
        
        # Generate unique ID
        chunk_id = hashlib.md5(
            f"{metadata['source_url']}{title}{content[:100]}".encode()
        ).hexdigest()[:16]
        
        # Extract topic tags
        topic_tags = self._extract_topics(content, title)
        
        # Determine priority
        priority = self._determine_priority(content, title, metadata['category'])
        
        # Add contextual header
        context_header = f"Document: {metadata['parent_page_title']}\nSection: {' > '.join(hierarchy)}\n\n"
        enriched_content = context_header + content
        
        return DocumentChunk(
            chunk_id=chunk_id,
            content=enriched_content,
            title=title,
            category=metadata['category'],
            source_url=metadata['source_url'],
            parent_page_title=metadata['parent_page_title'],
            topic_tags=topic_tags,
            priority=priority,
            word_count=len(content.split()),
            section_hierarchy=' > '.join(hierarchy),
            last_updated=datetime.now().isoformat()
        )
    
    def _extract_topics(self, content: str, title: str) -> List[str]:
        """Extract relevant topic tags"""
        topics = set()
        
        # Keywords to look for
        keywords = {
            'health': ['health', 'heart', 'fitness', 'workout', 'ecg', 'blood', 'oxygen', 'vitals'],
            'notifications': ['notification', 'alert', 'notify'],
            'complications': ['complication', 'watch face'],
            'siri': ['siri', 'voice', 'dictation'],
            'connectivity': ['bluetooth', 'wifi', 'cellular', 'connection', 'pairing'],
            'battery': ['battery', 'power', 'charging'],
            'apps': ['app', 'application', 'software'],
            'settings': ['setting', 'preference', 'configuration', 'customize'],
            'security': ['security', 'privacy', 'passcode', 'authentication', 'unlock'],
            'performance': ['performance', 'speed', 'optimization', 'faster'],
            'bugs': ['bug', 'fix', 'issue', 'crash', 'resolved', 'problem'],
            'features': ['new feature', 'enhancement', 'improvement', 'update'],
            'watchos': ['watchos', 'watch os', 'operating system'],
            'display': ['display', 'screen', 'always-on', 'brightness'],
            'sensors': ['sensor', 'accelerometer', 'gyroscope', 'gps'],
            'accessibility': ['accessibility', 'voiceover', 'assistive']
        }
        
        text = (content + ' ' + title).lower()
        
        for topic, terms in keywords.items():
            if any(term in text for term in terms):
                topics.add(topic)
        
        return list(topics) if topics else ['general']
    
    def _determine_priority(self, content: str, title: str, category: str) -> str:
        """Determine chunk priority for RAG"""
        text = (content + ' ' + title).lower()
        
        # High priority indicators
        high_priority = ['critical', 'important', 'breaking', 'major', 'security', 'deprecated', 'removed', 'required']
        if any(term in text for term in high_priority):
            return 'high'
        
        # Release notes generally higher priority
        if category == 'release_notes':
            if any(term in text for term in ['new', 'added', 'improved', 'fixed']):
                return 'high'
            return 'medium'
        
        # Medium priority for feature descriptions
        if any(term in text for term in ['feature', 'enhancement', 'how to', 'guide']):
            return 'medium'
        
        return 'low'

# ============================================================================
# Main Crawler
# ============================================================================

class AppleWatchKBCrawler:
    """Main crawler orchestrator"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.url_manager = URLManager()
        self.processor = ContentProcessor(
            chunk_size=config['chunk_size'],
            overlap=config['chunk_overlap']
        )
        self.all_chunks = []
        self.crawl_stats = {
            'pages_crawled': 0,
            'chunks_created': 0,
            'errors': 0,
            'categories': {}
        }
    
    async def crawl(self):
        """Main crawl orchestration"""
        print("🚀 Starting Apple Watch OS 26 Knowledge Base Crawler")
        print("=" * 60)
        
        # Initialize seed URLs
        for category, urls in self.config['seed_urls'].items():
            self.url_manager.add_urls(urls, category, depth=0)
        
        # Configure crawler
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=60000,
            delay_before_return_html=3.0
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            while True:
                url_info = self.url_manager.get_next()
                
                if not url_info:
                    break
                
                url = url_info['url']
                category = url_info['category']
                depth = url_info['depth']
                
                # Stop if max depth reached
                if depth > self.config['max_depth']:
                    continue
                
                print(f"\n📄 Crawling [{category}] depth={depth}: {url}")
                
                try:
                    # Crawl page
                    result = await crawler.arun(
                        url=url,
                        config=crawler_config
                    )
                    
                    if not result.success:
                        print(f"  ❌ Failed: {result.error_message}")
                        self.crawl_stats['errors'] += 1
                        continue
                    
                    # Process content
                    await self._process_page(result, category, url)
                    
                    # Extract and queue subpages
                    if depth < self.config['max_depth']:
                        subpages = self._extract_subpages(result, url, category)
                        if subpages:
                            print(f"  🔗 Found {len(subpages)} subpages to crawl")
                            self.url_manager.add_urls(subpages, category, depth + 1)
                    
                    self.url_manager.mark_visited(url)
                    self.crawl_stats['pages_crawled'] += 1
                    
                    # Be respectful - add delay
                    await asyncio.sleep(self.config['delay_between_requests'])
                    
                except Exception as e:
                    print(f"  ❌ Error: {str(e)}")
                    self.crawl_stats['errors'] += 1
        
        print("\n" + "=" * 60)
        print("✅ Crawling completed!")
        self._print_stats()
        
        # Save knowledge base
        await self._save_knowledge_base()
    
    async def _process_page(self, result, category: str, url: str):
        """Process a crawled page"""
        # Extract page title
        title = self._extract_title(result.html)
        
        print(f"  📝 Processing: {title}")
        
        # Extract sections
        sections = self.processor.extract_sections(result.html, result.markdown)
        
        print(f"  📑 Found {len(sections)} sections")
        
        # Create metadata
        metadata = {
            'source_url': url,
            'category': category,
            'parent_page_title': title
        }
        
        # Create chunks
        chunks = self.processor.create_chunks(sections, metadata)
        self.all_chunks.extend(chunks)
        
        # Update stats
        self.crawl_stats['chunks_created'] += len(chunks)
        self.crawl_stats['categories'][category] = self.crawl_stats['categories'].get(category, 0) + 1
        
        print(f"  ✓ Created {len(chunks)} chunks")
    
    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML"""
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up common suffixes
            title = re.sub(r'\s*[|-]\s*(Apple|Apple Support|Apple Developer).*$', '', title)
            return title
        return "Untitled Page"
    
    def _extract_subpages(self, result, base_url: str, category: str) -> List[str]:
        """Extract valid subpage links"""
        if not hasattr(result, 'links') or not result.links:
            return []
        
        links = result.links.get('internal', [])
        base_domain = urlparse(base_url).netloc
        
        valid_links = []
        for link in links:
            try:
                absolute_url = urljoin(base_url, link)
                
                if self.url_manager.is_valid_url(absolute_url, base_domain):
                    valid_links.append(absolute_url)
            except:
                continue
        
        return list(set(valid_links))  # Remove duplicates
    
    def _print_stats(self):
        """Print crawl statistics"""
        print(f"\n📊 Crawl Statistics:")
        print(f"  Pages crawled: {self.crawl_stats['pages_crawled']}")
        print(f"  Chunks created: {self.crawl_stats['chunks_created']}")
        print(f"  Errors: {self.crawl_stats['errors']}")
        print(f"\n  By category:")
        for cat, count in self.crawl_stats['categories'].items():
            print(f"    {cat}: {count} pages")
    
    async def _save_knowledge_base(self):
        """Save complete knowledge base"""
        print("\n💾 Saving knowledge base...")
        
        if not self.all_chunks:
            print("  ⚠️ No chunks to save!")
            return
        
        # Calculate statistics
        stats = {
            'total_chunks': len(self.all_chunks),
            'total_words': sum(chunk.word_count for chunk in self.all_chunks),
            'avg_chunk_size': sum(chunk.word_count for chunk in self.all_chunks) / len(self.all_chunks),
            'categories': {},
            'priorities': {},
            'topics': {}
        }
        
        for chunk in self.all_chunks:
            # Category stats
            stats['categories'][chunk.category] = stats['categories'].get(chunk.category, 0) + 1
            
            # Priority stats
            stats['priorities'][chunk.priority] = stats['priorities'].get(chunk.priority, 0) + 1
            
            # Topic stats
            for topic in chunk.topic_tags:
                stats['topics'][topic] = stats['topics'].get(topic, 0) + 1
        
        # Create knowledge base
        kb = KnowledgeBase(
            metadata={
                'created_at': datetime.now().isoformat(),
                'source': 'Apple Watch OS 26 Documentation',
                'version': '1.0',
                'crawl_config': {
                    'chunk_size': self.config['chunk_size'],
                    'chunk_overlap': self.config['chunk_overlap'],
                    'max_depth': self.config['max_depth']
                }
            },
            chunks=self.all_chunks,
            statistics=stats
        )
        
        # Save user guide knowledge base
        user_guide_path = self.config['output_dir'] / 'user_guide.json'
        with open(user_guide_path, 'w', encoding='utf-8') as f:
            json.dump(kb.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved user guide knowledge base: {user_guide_path}")
        print(f"    Size: {user_guide_path.stat().st_size / 1024 / 1024:.2f} MB")

        # Print summary
        print(f"\n📈 Knowledge Base Summary:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Total words: {stats['total_words']:,}")
        print(f"  Average chunk size: {stats['avg_chunk_size']:.1f} words")
        print(f"\n  Priority distribution:")
        for priority, count in sorted(stats['priorities'].items()):
            print(f"    {priority}: {count} chunks")
        print(f"\n  Top 10 topics:")
        for topic, count in sorted(stats['topics'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {topic}: {count} chunks")

# ============================================================================
# Main Execution
# ============================================================================

async def main():
    """Main entry point"""
    crawler = AppleWatchKBCrawler(CONFIG)
    await crawler.crawl()
    
    print("\n" + "=" * 60)
    print("🎉 Knowledge Base Creation Complete!")
    print("\nGenerated files:")
    print(f"  1. {CONFIG['output_dir']}/user_guide.json - User Guide KB with all metadata")
    print("\nNext steps:")
    print("  - Use rag_chunks.json with your embedding model")
    print("  - Index in vector database (Pinecone, Weaviate, ChromaDB, etc.)")
    print("  - Configure your RAG agent with the knowledge base")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())