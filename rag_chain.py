from langchain_classic.chains import RetrievalQA

from models.llm import llm


def create_rag_chain(retriever):
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff"
    )

    return qa_chain