from src.utils import ConfigLoader, extract_filenames, find_uuid_and_check_embedding
from src.store_data import get_embeddings
from src.store_data import get_connection_string
from langchain.vectorstores.pgvector import PGVector
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from aws_lambda_powertools import Logger
from dotenv import load_dotenv
import json
import time

logger = Logger()

load_dotenv()


def handler(event, context):
    try:
        logger.info("Handling incoming event")
        question = json.loads(event.get('body', {})).get('question')
        if not question:
            logger.warning("No question provided in the event body")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No question provided'})
            }
        answer, document_filename = get_answer_from_model(question)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'request': answer,
                'relevant_documents': document_filename
            })
        }
    except Exception as e:
        logger.exception(f"Exception occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken for {func.__name__}: {end_time - start_time} seconds")
        return result
    return wrapper


@timer_decorator
def get_qa_and_db():
    config = ConfigLoader()
    embedding_model = config.get_value('embedding_model')
    logger.info("Loading QA and database configuration")
    uuid, emb = find_uuid_and_check_embedding(embedding_model)
    if not uuid or not emb:
        raise FileNotFoundError(
            f"""
            Invalid vector store for model {embedding_model!r}.
            Make sure you create a vector store first, by running the 'saveVectorStore' lambda.
            """)
    embeddings = get_embeddings(embedding_model)

    db = PGVector(
        collection_name=embedding_model,
        connection_string=get_connection_string(),
        embedding_function=embeddings,
        )

    retriever = db.as_retriever()

    llm = ChatOpenAI()
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    return qa, db


@timer_decorator
def get_answer_from_model(question):
    logger.info(f"Getting answer for question: {question}")
    qa, db = get_qa_and_db()
    llm_response = qa(question)
    search = db.similarity_search_with_score(question)
    document_filename = {}
    for doc in search:
        document_filename[extract_filenames(doc[0].metadata['source'])] = doc[0].page_content
    return llm_response, document_filename
