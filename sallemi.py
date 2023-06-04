import sllm_help as sh
import json
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
import pinecone
from langchain.agents import Tool
from langchain.vectorstores import Pinecone
from langchain.chains import RetrievalQA    
    


class MyKnowledgeBase:
    def __init__(self) -> None:
        self.files = [
            './sllm_data/spendanal.txt',
            './sllm_data/procu_an.txt',
            './sllm_data/procu_data.txt',
        ] 
        self.txts = [] 
    def load_documents(self):
        chunkdocs =[] 
        for f in self.files: 
            doc = sh.load_doc(f)
            chunkdocs.extend(sh.split_doc(doc))
        self.txts.extend([c.page_content for c in chunkdocs] ) 

    def load_tweets(self):    
        with open('./sllm_data/twets.txt') as f:
            js = json.loads(f.read())
        tweettexts = [j.get('text') for j in js ]
        self.tweetids = [j.get('id') for j in js ]
        self.txts.extend(tweettexts)        


class Embedder:
    def __init__(self) -> None:
        self.embedder = OpenAIEmbeddings(
            model='text-embedding-ada-002',
            openai_api_key=sh.OPENAI_API_KEY
        )

    def create_embeddings(self, kb):    
        self.embeddings = self.embedder.embed_documents(kb.txts)
    
index_name = 'langchain-retrieval-agent'

def create_pinecone_index():
    # Create a Pinecone index if it doesn't exist
    # https://docs.pinecone.io/docs/langchain-retrieval-agent

    pinecone.init(
        api_key=sh.PC_API_KEY,
        environment=sh.PC_ENV
    )
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name,
            metric='dotproduct',
            dimension=1536 
            # Supposedly 1536 is linked to the OpenAI model name.
        )


class Sallemi:    
    def __init__(self, temp) -> None:
        self.temp = temp
        self.kb = MyKnowledgeBase()
        self.kb.load_documents()
        self.kb.load_tweets()
        self.emb = Embedder()
        self.emb.create_embeddings(self.kb)
        # create_pinecone_index()
        self.vectorstore = self.create_vectorstore()
        self.create_conversation_memory()
        self.define_model()
        self.define_tools()
        self.agent = None

    def create_vectorstore(self):
        # Do the actual indexing. 
        # Using Pinecone client instead of LangChain vector store, 
        # so specifying type of index
        index = pinecone.GRPCIndex(index_name)

        # Put the actual text chunks to retrieve in metadata 
        metadatas =[{'text': t} for t in self.kb.txts]

        # Create ids for the text chunks
        ids = [str(i) for i in range(0,len(self.kb.txts))] 
        ids.extend(self.kb.tweetids)

        # The schema is: id, text embedding, text
        zvect = zip(ids, self.emb.embeddings, metadatas)
        index.upsert(vectors=zvect)

        # Get the index object to use with Langchain
        index=pinecone.Index(index_name)

        # Specify in which field the actual text chunks are
        text_field='text'
        vectorstore = Pinecone(index, self.emb.embed_query, text_field)
        return vectorstore

    def create_conversation_memory(self):
        self.conv_memory = ConversationBufferWindowMemory(
            memory_key='chat_history',
            k=5,
            return_messages=True
        )

    def define_tools(self):
        # Link the vectorstore to the model and wrap into a tool that the agent can use
        qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type='stuff',
            retriever=self.vectorstore.as_retriever()
        )
    
        tools =[
            Tool(
                name='SievoKb',
                func=qa.run,
                description=(
                    'use this tool when answering general knowledge queries to get '
                    'more information about the topic'
                )
            )
        ] 


    def define_model(self):
    # Specify the chat model 
        self.llm = ChatOpenAI(
            openai_api_key=sh.OPENAI_API_KEY,
            model_name='gpt-3.5-turbo',
            temperature=self.temp
        )

    def start_agent(self):
        # Create the agent that uses the LLM, memory and tool
        from langchain.agents import initialize_agent
        self.agent = initialize_agent(
            agent='chat-conversational-react-description',
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=3,
            early_stopping_method='generate',
            memory=self.conv_memory
        )
        


