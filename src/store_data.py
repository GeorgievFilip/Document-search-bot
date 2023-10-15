from src.read_docs import FileReader
from src.utils import ConfigLoader, get_connection_string
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores.pgvector import PGVector
from aws_lambda_powertools import Logger
from typing import Any, Optional, Dict
import json


logger = Logger()


def handler(event, context):
    try:
        logger.info("Handling event to save embeddings.")
        config = ConfigLoader()
        save_embeddings(config.get_value('document_directory'), config.get_value('embedding_model'))
        return {
            "statusCode": 200,
            "body": json.dumps("Embeddings saved successfully.")
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def ensure_vector_extension_exists(connection_string: str) -> None:
    from sqlalchemy import create_engine
    engine = create_engine(connection_string)
    with engine.connect() as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def save_embeddings(docs_directory: str, embedding_model: str) -> None: 
    CONNECTION_STRING = get_connection_string()
    ensure_vector_extension_exists(CONNECTION_STRING)
    logger.info("Saving embeddings.")
    file_reader = FileReader(directory=docs_directory)
    loaded_content = file_reader.read_files()
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(loaded_content)
    embeddings = get_embeddings(embedding_model)

    PGVector.from_documents(
        embedding=embeddings,
        documents=documents,
        collection_name=embedding_model,
        connection_string=CONNECTION_STRING,
        pre_delete_collection=True
    )


def get_embeddings(
    embedding_model: str, 
    model_kwargs: Optional[Dict[str, Any]] = None, 
    encode_kwargs: Optional[Dict[str, Any]] = None
) -> Any:
    logger.info(f"Getting embeddings for model: {embedding_model}")

    if model_kwargs is None:
        model_kwargs = {'device': 'cpu'}

    if encode_kwargs is None:
        encode_kwargs = {'normalize_embeddings': True}

    embeddings = HuggingFaceBgeEmbeddings(
        model_name=embedding_model,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    return embeddings
