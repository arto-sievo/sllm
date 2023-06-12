from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
# https://learn.microsoft.com/en-us/azure/key-vault/secrets/quick-create-python?tabs=azure-cli

def get_secrets():
    keyVaultName = 'kv-artodev'
    kvUrl = f'https://{keyVaultName}.vault.azure.net'
    credential = DefaultAzureCredential()
    print('Getting SecretClient...')
    client = SecretClient(vault_url=kvUrl, credential=credential)
    print('Got a client, now getting secrets')
    try:
        OPENAI_API_KEY=client.get_secret('openai-api-key')
        PC_API_KEY=client.get_secret('pinecone-api-key')
        PC_ENV=client.get_secret('pinecone-environment')
    except HttpResponseError as e:
        print('Failed to retrieve.')
        print(e.__str__())
        raise e
    sec ={'openai_api_key': OPENAI_API_KEY,
          'pc_api_key': PC_API_KEY,
          'pc_env': PC_ENV}
    return sec
# import configparser
# conf = configparser.ConfigParser()
# conf.read('config.ini')

# OPENAI_API_KEY=conf['openai']['api_key']  
# PC_API_KEY=conf['pinecone']['api_key']  
# PC_ENV=conf['pinecone']['environment'] 


from langchain.document_loaders import TextLoader
def load_doc(docpath):
    try:
        loader = TextLoader(docpath)
    except Exception as e:
        print(f'Caught {e}')
    return loader.load()

from langchain.text_splitter import RecursiveCharacterTextSplitter
def split_doc(doc):
    # langchain Document -> [langchain Document] 
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ' ', ''],
        chunk_size=400, 
        chunk_overlap=30)
    return text_splitter.split_documents(doc)
