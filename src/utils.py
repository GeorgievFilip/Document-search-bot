import yaml
import re
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from langchain.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    PDFMinerLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    UnstructuredPowerPointLoader
)

DOCUMENT_MAP = {
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".pdf": PDFMinerLoader,
    ".csv": CSVLoader,
    ".xls": UnstructuredExcelLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".docx": Docx2txtLoader,
    ".doc": Docx2txtLoader,
    ".html": UnstructuredHTMLLoader,
    ".pptx": UnstructuredPowerPointLoader
}


class ConfigLoader:
    def __init__(self, yaml_file_path=None):
        if yaml_file_path is None:
            current_directory = os.path.dirname(
                os.path.abspath(__file__)
                )
            parent_directory = os.path.abspath(
                os.path.join(current_directory,
                             os.pardir
                             )
                )
            yaml_file_path = os.path.join(parent_directory, "config.yaml")

        self.config_data = self._load_yaml(yaml_file_path)

    def _load_yaml(self, yaml_file_path):
        try:
            with open(yaml_file_path, "r") as file:
                return yaml.safe_load(file)
        except (FileNotFoundError, yaml.YAMLError):
            return None

    def get_value(self, key):
        if self.config_data is not None:
            return self.config_data.get(key, None)
        else:
            return None


def extract_filenames(path):
    extracted = None
    for ext in DOCUMENT_MAP.keys():
        match = re.search(fr'[^\\\/]*\{ext}$', path)
        if match:
            extracted = match.group(0)
            break
    if not extracted:
        raise ValueError("No matching files found.")
    return extracted


def get_connection_string():
    # Load variables from .env file
    load_dotenv()

    # Read variables
    driver = os.environ.get("PGVECTOR_DRIVER")
    host = os.environ.get("PGVECTOR_HOST")
    port = int(os.environ.get("PGVECTOR_PORT"))
    database = os.environ.get("PGVECTOR_DATABASE")
    user = os.environ.get("PGVECTOR_USER")
    password = os.environ.get("PGVECTOR_PASSWORD")

    # Construct and return connection string
    connection_string = f"postgresql+{driver}://{user}:{password}@{host}:{port}/{database}"
    return connection_string


def find_uuid_and_check_embedding(name):
    # Get the connection string
    connection_string = get_connection_string()

    # Initialize the database engine
    engine = create_engine(connection_string)

    # Initialize variables
    uuid_to_find = None
    is_in_embedding = False

    # SQL to find the uuid for the given name in 'langchain_pg_collection'
    find_uuid_sql = text("SELECT uuid FROM langchain_pg_collection WHERE name = :name")

    # SQL to check if the uuid exists in 'langchain_pg_embedding'
    check_embedding_sql = text("SELECT EXISTS(SELECT 1 FROM langchain_pg_embedding WHERE collection_id = :uuid)")

    with engine.connect() as connection:
        # Find the uuid
        result = connection.execute(find_uuid_sql, {'name': name}).fetchone()
        if result:
            uuid_to_find = result[0]

        # Check if the uuid exists in 'langchain_pg_embedding'
        if uuid_to_find:
            result = connection.execute(check_embedding_sql, {'uuid': uuid_to_find}).fetchone()
            is_in_embedding = result[0]

    return uuid_to_find, is_in_embedding
