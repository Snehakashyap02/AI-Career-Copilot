from langchain_community.vectorstores import FAISS

from embeddings.embedding_model import embedding_model


def create_vectorstore(chunks):

    vector_db = FAISS.from_documents(
        chunks,
        embedding_model
    )

    vector_db.save_local("faiss_index")

    return vector_db