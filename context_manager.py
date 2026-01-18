"""
Context Management for RLM Engine
Handles token counting, document chunking, and context window optimization
"""

import re
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TokenCounter:
      """Estimates token count for text using simple heuristics"""

    # Average characters per token (rough estimate: 4 chars = 1 token)
      CHARS_PER_TOKEN = 4

    @staticmethod
    def count_tokens(text: str) -> int:
              """Estimate token count for text"""
              if not text:
                            return 0
                        return max(1, len(text) // TokenCounter.CHARS_PER_TOKEN)

    @staticmethod
    def count_tokens_batch(texts: List[str]) -> int:
              """Count tokens for multiple texts"""
        return sum(TokenCounter.count_tokens(text) for text in texts)


class ContextManager:
      """Manages context window and document chunking for RLM"""

    def __init__(self, 
                                  max_context_tokens: int = 10000000,
                                  chunk_size: int = 100000,
                                  chunk_overlap: int = 5000):
                                            """
                                                    Initialize context manager

                                                                    Args:
                                                                                max_context_tokens: Maximum tokens in context window (10M for RLM)
                                                                                            chunk_size: Size of each chunk in characters
                                                                                                        chunk_overlap: Overlap between chunks for continuity
                                                                                                                """
                                            self.max_context_tokens = max_context_tokens
                                            self.chunk_size = chunk_size
                                            self.chunk_overlap = chunk_overlap
                                            self.token_counter = TokenCounter()

    def estimate_context_usage(self, documents: List[str], query: str) -> Dict:
              """Estimate token usage for documents and query"""
        query_tokens = self.token_counter.count_tokens(query)
        doc_tokens = self.token_counter.count_tokens_batch(documents)
        total_tokens = query_tokens + doc_tokens

        return {
                      "query_tokens": query_tokens,
                      "document_tokens": doc_tokens,
                      "total_tokens": total_tokens,
                      "within_limit": total_tokens <= self.max_context_tokens,
                      "utilization_percent": (total_tokens / self.max_context_tokens) * 100
        }

    def chunk_documents(self, documents: List[str], 
                                               preserve_paragraphs: bool = True) -> List[Dict]:
                                                         """
                                                                 Split documents into chunks with optional overlap

                                                                                 Args:
                                                                                             documents: List of document strings
                                                                                                         preserve_paragraphs: Whether to avoid splitting paragraphs
                                                                                                                 
                                                                                                                         Returns:
                                                                                                                                     List of chunk dictionaries with metadata
                                                                                                                                             """
                                                         chunks = []
                                                         chunk_id = 0

        for doc_idx, document in enumerate(documents):
                      # Split by paragraphs if enabled
                      if preserve_paragraphs:
                                        paragraphs = document.split('\n\n')
else:
                paragraphs = [document]

            current_chunk = ""
            chunk_start_para = 0

            for para_idx, paragraph in enumerate(paragraphs):
                              # Check if adding this paragraph exceeds chunk size
                              if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                                                    # Save current chunk
                                                    chunks.append({
                                                                              "chunk_id": chunk_id,
                                                                              "document_id": doc_idx,
                                                                              "content": current_chunk.strip(),
                                                                              "token_count": self.token_counter.count_tokens(current_chunk),
                                                                              "paragraphs": f"{chunk_start_para}-{para_idx}",
                                                                              "start_char": len("\n\n".join(paragraphs[:chunk_start_para])),
                                                                              "end_char": len("\n\n".join(paragraphs[:para_idx]))
                                                    })
                                                    chunk_id += 1

                    # Start new chunk with overlap
                                  overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                    current_chunk = overlap_text + "\n\n" + paragraph
                    chunk_start_para = para_idx
else:
                    current_chunk += ("\n\n" if current_chunk else "") + paragraph

            # Save final chunk
              if current_chunk:
                                chunks.append({
                                                      "chunk_id": chunk_id,
                                                      "document_id": doc_idx,
                                                      "content": current_chunk.strip(),
                                                      "token_count": self.token_counter.count_tokens(current_chunk),
                                                      "paragraphs": f"{chunk_start_para}-{len(paragraphs)}",
                                                      "start_char": len("\n\n".join(paragraphs[:chunk_start_para])),
                                                      "end_char": len(document)
                                })
                                chunk_id += 1

        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks

    def select_relevant_chunks(self, chunks: List[Dict], query: str, 
                                                             max_chunks: int = None) -> List[Dict]:
                                                                       """
                                                                               Select most relevant chunks based on query similarity

                                                                                               Args:
                                                                                                           chunks: List of document chunks
                                                                                                                       query: Query string
                                                                                                                                   max_chunks: Maximum chunks to return (None = use context window)
                                                                                                                                           
                                                                                                                                                   Returns:
                                                                                                                                                               Selected chunks sorted by relevance
                                                                                                                                                                       """
                                                                       # Simple TF-IDF style scoring
                                                                       query_terms = set(re.findall(r'\b\w+\b', query.lower()))

        scored_chunks = []
        for chunk in chunks:
                      # Count matching terms in chunk
                      chunk_terms = re.findall(r'\b\w+\b', chunk["content"].lower())
                      matches = sum(1 for term in chunk_terms if term in query_terms)
                      score = matches / (len(chunk_terms) + 1)  # Normalize

            scored_chunks.append({
                              **chunk,
                              "relevance_score": score,
                              "rank": 0
            })

        # Sort by relevance
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Apply max_chunks limit
        if max_chunks is None:
                      # Estimate max chunks that fit in context
                      available_tokens = self.max_context_tokens - self.token_counter.count_tokens(query)
                      tokens_per_chunk = sum(c["token_count"] for c in scored_chunks) / len(scored_chunks) if scored_chunks else 1
                      max_chunks = int(available_tokens / tokens_per_chunk)

        selected = scored_chunks[:max_chunks]

        # Add ranking
        for rank, chunk in enumerate(selected):
                      chunk["rank"] = rank + 1

        logger.info(f"Selected {len(selected)} of {len(chunks)} chunks (relevance-based)")
        return selected

    def build_context(self, chunks: List[Dict], query: str, 
                                           include_metadata: bool = True) -> str:
                                                     """
                                                             Build final context string from chunks

                                                                             Args:
                                                                                         chunks: Selected chunks
                                                                                                     query: Original query
                                                                                                                 include_metadata: Whether to include chunk metadata
                                                                                                                         
                                                                                                                                 Returns:
                                                                                                                                             Formatted context string
                                                                                                                                                     """
                                                     context_parts = [f"Query: {query}\n", "=" * 80, "\n\nContext Documents:\n"]

        for chunk in chunks:
                      if include_metadata:
                                        context_parts.append(f"\n[Chunk {chunk['chunk_id']} - Document {chunk['document_id']} - Relevance: {chunk.get('relevance_score', 0):.2f}]")

                      context_parts.append(f"\n{chunk['content']}\n")

            if include_metadata:
                              context_parts.append(f"[End Chunk {chunk['chunk_id']}]\n")

        return "".join(context_parts)

    def optimize_context(self, documents: List[str], query: str) -> Tuple[str, Dict]:
              """
                      Complete context optimization pipeline

                                      Args:
                                                  documents: Input documents
                                                              query: User query

                                                                              Returns:
                                                                                          Tuple of (optimized_context, metadata)
                                                                                                  """
        # Estimate usage
        usage = self.estimate_context_usage(documents, query)

        if usage["within_limit"]:
                      logger.info("All documents fit in context window")
                      chunks = self.chunk_documents(documents)
else:
            logger.warning("Documents exceed context - selecting relevant chunks")
            all_chunks = self.chunk_documents(documents)
            chunks = self.select_relevant_chunks(all_chunks, query)

        context = self.build_context(chunks, query)

        return context, {
                      "original_usage": usage,
                      "chunks_used": len(chunks),
                      "total_chunk_tokens": sum(c["token_count"] for c in chunks),
                      "optimization_applied": not usage["within_limit"]
        }


def create_context_manager(max_tokens: int = 10000000) -> ContextManager:
      """Factory function to create context manager"""
    return ContextManager(max_context_tokens=max_tokens)
