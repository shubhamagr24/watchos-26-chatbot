"""
RAG Knowledge Base Service
"""
from typing import List, Dict, Any
from pathlib import Path
import json

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.utils.text_processing import (
    chunk_text, 
    split_markdown_by_headers, 
    extract_version_from_category
)


class RAGKnowledgeBase:
    """
    Manages the local Watch OS 26 knowledge base with vector search
    
    Features:
    - Separate processing for user guides and release notes
    - Intelligent chunking with overlap
    - Metadata-rich search
    - Persistent storage with ChromaDB
    """
    
    def __init__(self, force_rebuild: bool = None):
        """
        Initialize the RAG Knowledge Base
        
        Args:
            force_rebuild: Force rebuild from source (ignores cache)
        """
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.persist_directory = settings.CHROMA_PERSIST_DIR
        self.vectorstore = None
        self.chunks_loaded = 0
        self.user_guide_chunks = 0
        self.release_notes_chunks = 0
        
        force_rebuild = force_rebuild if force_rebuild is not None else settings.FORCE_REBUILD
        
        # Load and index the knowledge base
        self._load_knowledge_base(force_rebuild)
    
    def _process_user_guide(self, data: List[Dict]) -> tuple:
        """Process user guide JSON data with optimized chunking"""
        texts = []
        metadatas = []
        
        print(f"   Processing {len(data)} user guide documents...")
        
        for idx, doc in enumerate(data, 1):
            url = doc.get('url', '')
            title = doc.get('title', 'Untitled')
            category = doc.get('category', 'user_guide')
            text = doc.get('text', '') 
            
            if not text.strip():
                print(f"      ⚠️ Skipping empty document {idx}: {title}")
                continue
            
            # Chunk the text for better retrieval
            chunks = chunk_text(
                text, 
                chunk_size=settings.USER_GUIDE_CHUNK_SIZE, 
                overlap=settings.USER_GUIDE_CHUNK_OVERLAP
            )
            
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                metadatas.append({
                    'url': url,
                    'title': title,
                    'category': category,
                    'doc_type': 'user_guide',
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'source': 'apple_support',
                    'content_type': 'plain_text'
                })
        
        return texts, metadatas
    
    def _process_release_notes(self, data: List[Dict]) -> tuple:
        """Process release notes JSON data with markdown-aware chunking"""
        texts = []
        metadatas = []
        
        print(f"   Processing {len(data)} release notes documents...")
        
        for idx, doc in enumerate(data, 1):
            url = doc.get('url', '')
            category = doc.get('category', 'release_notes')
            text = doc.get('text', '')
            title = doc.get('title', doc.get('tittle', 'Unknown'))
            
            if not text.strip():
                print(f"      ⚠️ Skipping empty document {idx}: {url}")
                continue
            
            version = extract_version_from_category(category)
            sections = split_markdown_by_headers(text)
            
            if not sections:
                sections = [('Overview', text)]
            
            for section_title, section_text in sections:
                if len(section_text) <= 1000:
                    chunks = [section_text]
                else:
                    chunks = chunk_text(
                        section_text, 
                        chunk_size=settings.RELEASE_NOTES_CHUNK_SIZE, 
                        overlap=settings.RELEASE_NOTES_CHUNK_OVERLAP
                    )
                
                for i, chunk in enumerate(chunks):
                    texts.append(chunk)
                    metadatas.append({
                        'url': url,
                        'title': title,
                        'category': 'release_notes',
                        'version': version,
                        'section': section_title if section_title else 'Overview',
                        'doc_type': 'release_notes',
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'source': 'apple_developer',
                        'content_type': 'markdown'
                    })
        
        return texts, metadatas
    
    def _load_knowledge_base(self, force_rebuild: bool = False):
        """Load and process both user guide and release notes"""
        
        # Check if vector store already exists
        if Path(self.persist_directory).exists() and not force_rebuild:
            print(f"📦 Loading existing vector store from {self.persist_directory}")
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                try:
                    collection = self.vectorstore._collection
                    self.chunks_loaded = collection.count()
                except:
                    self.chunks_loaded = 0
                
                print(f"   ✓ Vector store loaded with {self.chunks_loaded} vectors")
                return
            except Exception as e:
                print(f"   ⚠️ Error loading existing vector store: {e}")
                print(f"   Creating new vector store...")
        
        # Build new vector store
        all_texts = []
        all_metadatas = []
        
        print("\n" + "="*70)
        print("Building Knowledge Base from Source Files")
        print("="*70)
        
        # Process User Guide
        user_guide_file = Path(settings.USER_GUIDE_PATH)
        if user_guide_file.exists():
            print(f"\n📘 Processing User Guide: {settings.USER_GUIDE_PATH}")
            try:
                with open(user_guide_file, 'r', encoding='utf-8') as f:
                    user_guide_data = json.load(f)
                
                texts, metadatas = self._process_user_guide(user_guide_data)
                all_texts.extend(texts)
                all_metadatas.extend(metadatas)
                self.user_guide_chunks = len(texts)
                print(f"   ✓ Created {len(texts)} chunks from {len(user_guide_data)} documents")
            except Exception as e:
                print(f"   ❌ Error processing user guide: {e}")
        
        # Process Release Notes
        release_notes_file = Path(settings.RELEASE_NOTES_PATH)
        if release_notes_file.exists():
            print(f"\n📗 Processing Release Notes: {settings.RELEASE_NOTES_PATH}")
            try:
                with open(release_notes_file, 'r', encoding='utf-8') as f:
                    release_notes_data = json.load(f)
                
                texts, metadatas = self._process_release_notes(release_notes_data)
                all_texts.extend(texts)
                all_metadatas.extend(metadatas)
                self.release_notes_chunks = len(texts)
                print(f"   ✓ Created {len(texts)} chunks from {len(release_notes_data)} documents")
            except Exception as e:
                print(f"   ❌ Error processing release notes: {e}")
        
        if not all_texts:
            print("\n⚠️ Warning: No documents loaded.")
            return
        
        self.chunks_loaded = len(all_texts)
        
        print("\n" + "="*70)
        print(f"📊 Knowledge Base Statistics:")
        print(f"   • User Guide Chunks: {self.user_guide_chunks}")
        print(f"   • Release Notes Chunks: {self.release_notes_chunks}")
        print(f"   • Total Chunks: {self.chunks_loaded}")
        print("="*70)
        
        # Create vector store
        print(f"\n🔨 Creating vector embeddings...")
        
        try:
            self.vectorstore = Chroma.from_texts(
                texts=all_texts,
                metadatas=all_metadatas,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"\n   ✓ Vector store created successfully\n")
        except Exception as e:
            print(f"\n   ❌ Error creating vector store: {e}")
    
    def search(self, query: str, k: int = None, filter_dict: Dict = None) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant chunks with similarity threshold"""
        if not self.vectorstore:
            return []
        
        k = k or settings.DEFAULT_SEARCH_RESULTS
        threshold = settings.RAG_SIMILARITY_THRESHOLD
        
        try:
            # Use similarity_search_with_relevance_scores to get scores (0-1)
            if filter_dict:
                results_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=k, filter=filter_dict
                )
            else:
                results_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=k
                )
            
            formatted_results = []
            for doc, score in results_with_scores:
                # Only include results that meet the similarity threshold
                if score >= threshold:
                    formatted_results.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'score': score
                    })
            
            if not formatted_results and results_with_scores:
                print(f"DEBUG: {len(results_with_scores)} results found but all below threshold {threshold}. Top score: {results_with_scores[0][1]:.4f}")
                
            return formatted_results
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    def search_by_doc_type(self, query: str, doc_type: str, k: int = None) -> List[Dict[str, Any]]:
        """Search within a specific document type"""
        return self.search(query, k=k, filter_dict={'doc_type': doc_type})
    
    def search_by_version(self, query: str, version: str, k: int = None) -> List[Dict[str, Any]]:
        """Search for specific version release notes"""
        return self.search(query, k=k, filter_dict={'version': version})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            'total_chunks': self.chunks_loaded,
            'user_guide_chunks': self.user_guide_chunks,
            'release_notes_chunks': self.release_notes_chunks,
            'vectorstore_ready': self.vectorstore is not None
        }


# Initialize RAG Knowledge Base (singleton)
print("\n🚀 Initializing Watch OS 26 Knowledge Base...")
rag_kb = RAGKnowledgeBase()
