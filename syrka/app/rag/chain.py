"""RAG chain for question answering over policy documents."""

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.rag.retriever import PolicyRetriever
from app.config import settings

logger = logging.getLogger(__name__)


class PolicyRAGChain:
    """
    RAG chain for querying policy documents using retrieval-augmented generation.

    Combines vector retrieval with LLM-powered answer generation.
    """

    def __init__(
        self,
        retriever: PolicyRetriever,
        llm_model: str = None
    ):
        """
        Initialize RAG chain.

        Args:
            retriever: Policy retriever for fetching relevant chunks
            llm_model: OpenAI model name (defaults to config setting)
        """
        self.retriever = retriever
        self.llm_model = llm_model or settings.OPENAI_MODEL

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.llm_model,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )

        # System prompt for policy analysis
        self.system_prompt = """You are an expert policy analyst specializing in workforce development and national development policies.
Your role is to analyze policy documents and provide clear, actionable insights based on the provided context.
Always cite specific sections when making claims and highlight key priorities and recommendations."""

    async def query(
        self,
        question: str,
        db: AsyncSession,
        context_filter: Optional[dict] = None,
        k: int = 5
    ) -> str:
        """
        Answer a question using RAG over policy documents.

        Args:
            question: User's question
            db: Database session
            context_filter: Optional filters for retrieval
            k: Number of context chunks to retrieve

        Returns:
            Generated answer based on retrieved policy context
        """
        # Retrieve relevant chunks
        chunks = await self.retriever.retrieve(
            query=question,
            db=db,
            k=k,
            filters=context_filter
        )

        if not chunks:
            return "I couldn't find relevant policy information to answer your question."

        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Access the document title through the relationship
            await db.refresh(chunk, ['document'])
            doc_title = chunk.document.title if chunk.document else "Unknown Document"
            context_parts.append(
                f"[Source {i}: {doc_title}]\n{chunk.content}\n"
            )

        context = "\n\n".join(context_parts)

        # Build prompt
        prompt = f"""Based on the following policy documents, please answer the question.

Context from policy documents:
{context}

Question: {question}

Please provide a comprehensive answer based solely on the information in the policy documents above.
If the documents don't contain enough information to answer fully, acknowledge this."""

        # Generate answer
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM query failed: {str(e)}")
            return f"Error generating answer: {str(e)}"

    async def extract_priorities(
        self,
        sector: str,
        db: AsyncSession
    ) -> list[dict]:
        """
        Extract national priorities for a specific sector.

        Args:
            sector: Target sector
            db: Database session

        Returns:
            List of dictionaries containing priority information
        """
        # Retrieve sector-relevant chunks
        chunks = await self.retriever.retrieve_by_sector(sector=sector, db=db, k=10)

        if not chunks:
            return []

        # Build context
        context = "\n\n".join([chunk.content for chunk in chunks])

        # Build prompt for priority extraction
        prompt = f"""Analyze the following policy documents and extract the key national priorities for the {sector} sector.

Policy Documents:
{context}

For each priority, provide:
1. The priority statement
2. A brief description
3. Any specific skills or competencies mentioned

Format your response as a structured list."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm(messages)

            # Parse response into structured format
            # This is a simplified version - production would need more robust parsing
            priorities = []
            lines = response.content.split('\n')

            current_priority = {}
            for line in lines:
                line = line.strip()
                if line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                    if current_priority:
                        priorities.append(current_priority)
                    current_priority = {
                        'sector': sector,
                        'priority': line[2:].strip(),
                        'description': '',
                        'skills_mentioned': []
                    }
                elif line and current_priority:
                    current_priority['description'] += ' ' + line

            if current_priority:
                priorities.append(current_priority)

            return priorities

        except Exception as e:
            logger.error(f"Priority extraction failed: {str(e)}")
            return []

    async def extract_skills(
        self,
        text: str
    ) -> list[str]:
        """
        Extract skill mentions from text using LLM.

        Args:
            text: Input text to analyze

        Returns:
            List of extracted skills
        """
        prompt = f"""Extract all skills, competencies, and capabilities mentioned in the following text.
Return only a comma-separated list of skills, nothing else.

Text:
{text}

Skills:"""

        messages = [
            SystemMessage(content="You are an expert at identifying skills and competencies in text."),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm(messages)
            # Parse comma-separated skills
            skills = [s.strip() for s in response.content.split(',')]
            return [s for s in skills if s]  # Remove empty strings

        except Exception as e:
            logger.error(f"Skill extraction failed: {str(e)}")
            return []

    async def summarize_document(
        self,
        document_id: str,
        db: AsyncSession
    ) -> str:
        """
        Generate a summary of a policy document.

        Args:
            document_id: Policy document ID
            db: Database session

        Returns:
            Document summary
        """
        # Retrieve all chunks from document (or top chunks if very long)
        chunks = await self.retriever.retrieve_by_document(
            document_id=document_id,
            db=db,
            query="summary overview main points",
            k=20
        )

        if not chunks:
            return "Document not found or has no content."

        # Combine chunk content
        full_content = "\n\n".join([chunk.content for chunk in chunks])

        # Truncate if too long (to fit in context window)
        max_chars = 10000
        if len(full_content) > max_chars:
            full_content = full_content[:max_chars] + "\n\n[Content truncated...]"

        prompt = f"""Please provide a comprehensive summary of the following policy document.
Include:
- Main objectives and goals
- Key priorities and recommendations
- Target sectors or populations
- Important timelines or milestones

Policy Document:
{full_content}

Summary:"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm(messages)
            return response.content
        except Exception as e:
            logger.error(f"Document summarization failed: {str(e)}")
            return f"Error generating summary: {str(e)}"
