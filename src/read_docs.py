from src.utils import DOCUMENT_MAP
from aws_lambda_powertools import Logger
from typing import List, Optional
import os
from pathlib import Path
import boto3
from dotenv import load_dotenv

logger = Logger()


class FileReader:

    def __init__(self, directory: str):
        load_dotenv()
        self.directory = directory
        self.env = os.getenv('ENV')

    def read_files(self) -> Optional[List[str]]:
        logger.info("Reading files based on environment setting.")
        if self.env == 'local':
            return self._read_local_files()
        elif self.env == 'production':
            return self._read_s3_files()
        else:
            logger.error("Invalid environment. Set ENV to either 'local' or 'production'.")
            return None

    def _read_local_files(self) -> List[str]:
        logger.info(f"Reading local files from directory: {self.directory}")
        content_list = []
        for ext, loader in DOCUMENT_MAP.items():
            pathlist = Path(self.directory).glob(f'**/*{ext}')
            for path in pathlist:
                content = loader(str(path)).load()[0]
                content_list.append(content)
        return content_list

    def _read_s3_files(self) -> List[str]:
        logger.info("Reading files from S3")
        s3 = boto3.client('s3')
        content_list = []

        response = s3.list_objects(Bucket=self.directory)

        for item in response['Contents']:
            key = item['Key']
            file_ext = Path(key).suffix
            if file_ext in DOCUMENT_MAP:
                s3_object = s3.get_object(Bucket=self.directory, Key=key)
                content = s3_object['Body'].read().decode('utf-8')

                loader = DOCUMENT_MAP[file_ext](content)
                content_list.append(loader.load()[0])
        return content_list
