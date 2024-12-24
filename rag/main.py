from typing import List, Dict
from langchain_groq import ChatGroq
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

class PsychoRag:
    def __init__(self, vector_db_paths: Dict[str, str]):
        # Initialize embedding model and LLM
        self.embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.rag_llm = ChatGroq(model="llama3-8b-8192")

        # Load precomputed Chroma databases
        self.vectorstores = {
            name: Chroma(persist_directory=path, embedding_function=self.embed_model)
            for name, path in vector_db_paths.items()
        }
        self.retrievers = {}
        for name, db in self.vectorstores.items():
            self.retrievers[name] = db.as_retriever()

        self.conversation_histories = {}

        # Define prompts
        RAG_SYSTEM_PROMPT = """\
            You are a psychological assistant for answering questions about mental health. \
            You have knowledge base from which you're retrieving some context based on question.

            Based on conversation history:
            '''
            {history}
            '''

            Use the following pieces of retrieved context to answer the human's questions:
            '''
            {context}
            '''

            Be very careful if you don't know the answer, it's dangerous to give bad answers, just say that you don't know.
            ALSO VERY IMPORTANT TO ANSWER IN LANGOUGE OF REQUEST!!!
        """

        RAG_HUMAN_PROMPT = """\
          {input}
        """

        self.RAG_PROMPT = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_HUMAN_PROMPT)
        ])

        # RAG pipeline
        self.rag_chain = (
            {
                "context": RunnableLambda(func=self._retrieve_combined_context),
                "history": RunnableLambda(func=lambda inputs: self._format_history(inputs['user_id'])),
                "input": RunnablePassthrough(),
            }
            | self.RAG_PROMPT
            | self.rag_llm
            | StrOutputParser()
        )

    def _retrieve_combined_context(self, query: str) -> str:
        """Retrieve relevant documents from all databases and combine the context."""
        if isinstance(query, dict):
            query = str(query)  # Convert dictionary to string if necessary
        combined_context = ""
        for name, retriever in self.retrievers.items():
            docs: List[Document] = retriever.invoke(query)
            combined_context += f"--- Context from {name} ---\n"
            combined_context += "\n".join(doc.page_content for doc in docs[:3])  # Top 3 results per DB
            combined_context += "\n\n"
        return combined_context

    def _format_history(self, user_id: int) -> str:
        """Format the conversation history into a readable string."""
        if user_id not in self.conversation_histories:
            return ""
        return "\n".join([f"{speaker}: {text}" for speaker, text in self.conversation_histories[user_id]])

    async def ask(self, user_id: int, user_input: str) -> str:
        """Process the user input, retrieve context, and generate a response."""
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []

        response = await self.rag_chain.ainvoke({"input": user_input, "user_id": user_id})

        # Save the conversation history
        self.conversation_histories[user_id].append(("User", user_input))
        self.conversation_histories[user_id].append(("Assistant", response))

        return response

    async def end_session(self, user_id: int):
        """Summarize the conversation at the end of the session."""
        if user_id not in self.conversation_histories:
            return "No conversation history found."

        SUMMARY_PROMPT = """\
          You are a psychologist who just completed a session with a client (the user).
          Below is the entire conversation you had with the user.

          Conversation:
          '''
          {history}
          '''

          Based on the entire conversation:
          1. Summarize the user's main psychological concerns and issues that came up.
          2. Provide a few possible methods or strategies for the user to work on these issues.
          3. Maintain an empathetic, understanding tone.
          4. If there is insufficient information to conclude on something, mention that gently.
          ALSO VERY IMPORTANT TO ANSWER IN LANGOUGE OF REQUEST!!!
        """

        formatted_history = self._format_history(user_id)
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", SUMMARY_PROMPT.replace("{history}", formatted_history))
        ])

        summary_chain = (
            RunnablePassthrough()
            | summary_prompt
            | self.rag_llm
            | StrOutputParser()
        )

        report = await summary_chain.ainvoke("")
        return report


# Main Function
import asyncio

async def main():
    # Paths to the precomputed Chroma databases
    VECTOR_DB_PATHS = {
    "transcriptions": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/transcriptions_db_2",
    "books": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/books_db_2"
    }

    # Initialize the PsychoRag system
    psycho_rag = PsychoRag(vector_db_paths=VECTOR_DB_PATHS)

    print("Welcome to the PsychoRag chatbot. Type 'exit' to stop the session.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("\nEnding session...")
            report = await psycho_rag.end_session()
            print("\nSession Summary:\n")
            print(report)
            break

        # Get assistant response
        response = await psycho_rag.ask(user_input)
        print(f"Assistant: {response}\n")

if __name__ == "__main__":
    asyncio.run(main())
