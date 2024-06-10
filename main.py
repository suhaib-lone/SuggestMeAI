from flask import Flask, render_template, request
import requests
from g4f.client import Client
app = Flask(__name__)

YOUTUBE_API_KEY ='AIzaSyD69Tkn6khJDXVP7VnLeojHi4ez56d0TEA'

def fetch_response(input):
    messages = [{"role": "user", "content": f"suggest me some english resources (like books and websites) for {input}.review before returning!"}]
    client = Client()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response.choices[0].message.content


def search_youtube(query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&key={YOUTUBE_API_KEY}"
    response=requests.get(url)
    return response.json()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    return render_template('generate.html')


@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    user_input1 = request.form['user_input1']
    user_input2 = request.form['user_input2']
    gpt_response1 = fetch_response(user_input1)
    gpt_response2 = fetch_response(user_input2)

    search_response1=search_youtube(user_input1)
    search_response2=search_youtube(user_input2)
    
    videos1=search_response1['items']
    videos2=search_response2['items']

    if(gpt_response1 and gpt_response2):
        return render_template('generate.html', user_input1=user_input1, user_input2=user_input2, gpt_response1=gpt_response1, gpt_response2=gpt_response2,videos1=videos1,videos2=videos2)


if __name__ == "__main__":
    app.run(debug=True)
