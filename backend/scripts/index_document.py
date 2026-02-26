import os 
import glob
import logging
from  dotenv import load_dotenv
load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("indexer")

def index_docs():
    '''
    Reads the PDFs, chunks them, and them upload to Azure AI Search
    '''

    current_dir = os.path.dirname(__file__)
    data_folder = os.path.join(current_dir, "../../backend/data")

    logger.info("="*60)
    logger.info("Environment Configuration Check: ")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv("AZURE_OPENAI_ENDPOINT")}")
    logger.info(f"AZURE_OPENAI_ENDPOINT : {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"Embedding Deployemnt: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT : {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    required_vars=[
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]
     
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables : {missing_vars}")
        logger.error("Please check your .env file and ensure all the variables are set")
        return

    # intialize the embedding model : turns text into vectors
    try:
        logger.info("Initializing Azure Open AI Embeddings")
        embeddings = AzureOpenAIEmbeddings(
        azure_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-3-small'),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        )
        logger.info("Embeddings model initialized succesfully")

    except Exception as e:
        logger.error(f"Failed to initialize embeddings model : {e}")
        logger.error("Please check your embedding model and ensure all the variables are set")
        return


    # initialize the Azure Search
        try:
            logger.info("Initializing Azure AI Search vector store...")
            index_name = os.getenv('AZURE_SEARCH_INDEX_NAME')
            vector_store = AzureSearch(
                azure_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT'),
                azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY"),
                index_name = index_name,
                embedding_function = embeddings.embed_query
                )
            logger.info(f"vector store initialized succesfully for index:{index_name} ")

        except Exception as e:
            logger.error(f"Failed to initialize Azure Search : {e}")
            logger.error("Please check your Azure Search Endpoints and ensure all the variables are set")
            return
        
        # find PDF files
        pdf_files = glob.glob(os.path.join(data_folder, "*.pdf")) 
        if not pdf_files:
            logger.error(f"No PDF files found in the data folder: {data_folder}. Please add files")
        logger.info(f"Found {len(pdf_files)} PDFs to process : {[os.path.basename(f) for f in pdf_files]}")

        all_splits = []

        # process each PDF file
        for pdf_path in pdf_files:
            try:
                logger.info(f"loading: {os.path.basename(pdf_path)}.....")
                loader =PyPDFLoader(pdf_path)
                raw_docs = loader.load()

            # chunking strategy
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size = 1000,
                    chunk_overlap = 200,
                
                ) 
                splits = text_splitter.split_documents(raw_docs) 
                for split in splits:
                    split.metadata["source"] = os.path.basename(pdf_path)
                
                all_splits.extend(splits)
                logger.info(f"Processed {len(splits)} splits from {os.path.basename(pdf_path)}")

            except Exception as e:
                logger.error(f"Failed to process {os.path.basename(pdf_path)} : {e}")
            # upload to Azure
            if all_splits:
                logger.info(f"Processing {len(all_splits)} splits to Azure AI Search Index {index_name}...")
                try:
                    vector_store.add_documents(documents = all_splits)  
                    logging.info("="*60)  
                    logging.info("Indexing completed successfully")
                    logger.info(f"Total chunks indexed: {len(all_splits)}")
                    logger.info("="*60)
                except Exception as e:
                    logger.error(f"Failed to upload the documents to Azure Search : {e}")
                    logger.error("Please check the Azure Search configuration and try again")

            else:
                logging.info("No documents were processed. Please check the data folder and try again")        

            
if __name__ == "__main__":
    index_docs()   
                



