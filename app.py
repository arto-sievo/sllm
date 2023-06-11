from sallemi import Sallemi
from pinecone import PineconeException

def return_ugly_error(msg):
    ugly_error = f"""    
    <h1>Launching failed.</h1>
    <p>Error {msg} 
    """
    return ugly_error

class Chat:
    def __init__(self) -> None:        
        self.prev_prompt = ''
        self.temp = 0        

    def set_prompt(self, userText):
        self.prev_prompt = userText
    
    def init_sllm(self):
        # Sallemi retains the current agent + tools and conversation history
        self.sllm = Sallemi(self.temp)

    def get_response(self, userText):
        prompt = userText.lower().strip()

        if prompt == 'have a drink': 
            if self.temp <= 1: 
                self.temp += .2
                resp = f'Thanks! My temp is {self.temp}'  
            else:
                resp = f'Thanks! I\'ve had quite enough. My temp is {self.temp}'            
            self.prev_prompt = prompt
        else:
            if self.prev_prompt == 'have a drink':
                # Done drinking. 
                # Start an agent with the same conversation history and vectorstore, but a higher temperature
                self.sllm.define_model()
                self.sllm.start_agent()              
            resp = self.sllm.agent(userText)
            resp = resp['output'] 
        return resp
    

from flask import Flask, render_template, request
app = Flask(__name__)
app.static_folder = 'static'
launch_error = False
chat = Chat()
try:
    chat.init_sllm()
except PineconeException as e:
    print('Sorry, Pinecone is not behaving')
    launch_error = e.__str__()

@app.route("/")
def home():
    if launch_error:
        ret = return_ugly_error(launch_error)
        #ret = f'Sorry, failed to launch.\n\n {launch_error} '
    else:
        ret = render_template("index.html")
    return ret

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return chat.get_response(userText)

if __name__ == "__main__":
    app.run(debug=True)