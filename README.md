
# Document Search Bot

## Project Overview

This AWS-based app efficiently navigates through large volumes of documentation. It provides answers to user queries based on the documentation and directs to relevant further reading.

![App Screenshot](src/images/Screenshot.png)

## Technical Stack

- **Programming Language**: Python
- **Web Framework**: Streamlit
- **Database**: PostgreSQL
- **Cloud**: AWS (Lambda, API Gateway, S3, EC2)
- **Libraries**: `langchain`, `sentence-transformer`, `openai`, `boto3`

## Getting Started
<a name="Prerequisites"></a>
### Prerequisites

- Python 3.x
- Node.js and Serverless Framework
- PostgreSQL and PGVector

## Local Setup
### Environment Setup

1. Install the [prerequisites](#Prerequisites).

2. Install JavaScript dependencies:
   ```bash
    npm install
    ```
3. Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Copy [`.env.example`](.env.example) to [`.env`](.env) and fill in the required fields.

5. Add your documents to the appropriate directory, and specify its path in [`config.yaml`](config.yaml)

### Running the Application
1. For local Lambda testing, start the local Lambda server by running:
    ```bash
    serverless offline start
    ```
2. Run the '/store_data' endpoint to create a vector store for a model as instructed in the [API Endpoints](#API-Endpoints) section.

    **Note**: You must run this at least once for creating the vector store for a given model and only rerun it if you want to update the vector store.

3. In a separate terminal, run the Streamlit app:
    ```bash
    streamlit run src/app.py
    ```
    **Note**: The local Lambda server must be running for the Streamlit app to function.

### Design Choices

#### Backend

1. **AWS Compatibility**:
    - Designed to be cloud-compatible, particularly with AWS services like Lambda and S3.
    - Documents should be stored in an S3 bucket in a production environment. They can be either '.txt', '.md', '.pdf', '.csv', '.xls', '.xlsx', '.docx', '.doc', '.html' or 'pptx' files
    - Lambda functions are used for processing and answering queries.
2. **Serverless Framework**: 
    - Simplifies the deployment and scaling of Lambda functions.
    - Configuration is defined in serverless.yaml.
    - Includes a `saveVectorStore` Lambda function for potentially updating the vector store in a single batched invocation when changes are detected in the S3 bucket. This can keep the vector store up to date with the latest changes in the documentation.
3.  **Document data embedding**:
    - Uses embeddings to create a searchable vector store saved in PostgreSQL table.

#### Frontend

1. **Streamlit**:
    - Used for rapid prototyping and ease of use.
    - Provides a straightforward way to deploy a frontend for the query interface.
    - The Streamlit app can be deployed on various platforms like Streamlit Sharing, Heroku, or AWS EC2.

## Architecture

The project follows a modular architecture:

- [`app.py`](src/app.py): Main script that uses Streamlit for the frontend and invokes Lambda functions.
- [`read_docs.py`](src/read_docs.py): Handles reading files from either local or S3 based on environment.
- [`store_data.py`](src/store_data.py): Lambda function that generates embeddings for the documents.
- [`question.py`](src/question.py): Lambda function to answer questions based on the documents.
- [`utils.py`](src/utils.py): Utility functions.
- [`serverless.yaml`](serverless.yaml): Serverless Framework configuration file for defining and deploying the Lambda functions.
- [`config.yaml`](config.yaml): Configuration file that outlines key parameters like the documentation directory and the embedding model to be used. This file serves as a centralized location for modifying important settings.

<a name="API-Endpoints"></a>
## API Endpoints

After running serverless offline start, the local Lambda server will be available for testing. Postman or similar tools can be used to send requests to the API endpoints, mimicking the behavior of AWS API Gateway. The local server will be accessible at http://localhost:3000/dev.

To test the question-answering function, for example, you could send a POST request to http://localhost:3000/dev/questions with a JSON payload containing your question.

<a name="get-store-data"></a>
### 1. GET `/store_data`
Creating or updating vector stores. In order to create one, update the `embedding_model` field in the [`config.yaml`](config.yaml) file and run this endpoint. Any of the model's name can be copied from [huggingface](https://huggingface.co/spaces/mteb/leaderboard).

### 2. POST `/questions`

Takes a question in JSON format and returns the answer and relevant documents. The expected JSON payload should be in the following format:

```bash
{
    "question": "What is SageMaker?"
}
```

Example response of the above request:

```bash
{
    "request": {
        "query": "What is SageMaker?",
        "result": "Amazon SageMaker is a fully managed service provided by..."
    },
    "relevant_documents": {
        "examples-sagemaker.md": "Working with Amazon SageMaker\n\nAmazon SageMaker is a fully managed service...",
        "sagemaker-projects-whatis.md": "What is a SageMaker Project?\n\nSageMaker Projects help organizations...",
        "integrating-sagemaker.md": "How Amazon SageMaker uses AWS Secrets Manager\n\nSageMaker is a fully managed...",
        "deeplens-getting-started-launch-sagemaker.md": "Train a Model in Amazon SageMaker\n\nTo begin creating your custom..."
    }
}
```

**Fields:**

- `request`: Contains the original query and the generated response.
    - `query`: The question that was asked.
    - `result`: The answer generated by the model.
- `relevant_documents`: A dictionary mapping document names to portions of their content that are relevant to the query.
