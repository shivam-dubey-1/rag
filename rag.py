import os
from flask import Flask, request, jsonify
from vllm import LLM, SamplingParams

app = Flask(__name__)

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
llm = LLM(model=model_name) #, device="cpu")  # Specify CPU for local testing
documents = {}

def load_documents(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), 'r') as file:
                documents[filename] = file.read()

def search_documents(query, top_k=3):
    results = []
    for name, content in documents.items():
        relevance = sum(query.lower().count(word) for word in content.lower().split())
        if relevance > 0:
            results.append((name, relevance, content))
    return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]

def generate_response(prompt, max_new_tokens=1024):
    sampling_params = SamplingParams(
        temperature=0.7,
        top_p=0.9,
        max_tokens=max_new_tokens
    )
    outputs = llm.generate([prompt], sampling_params)
    return outputs[0].outputs[0].text

system_prompt = """Provide concise, factual information about Kubernetes and cloud infrastructure based on the given context. Focus on key points and technical details without conversational elements."""

def get_response(query):
    try:
        search_results = search_documents(query)
        
        if not search_results:
            return "No relevant information found."
        
        context = "\n\n".join([f"Document: {name}\nContent: {content}" for name, _, content in search_results])
        
        prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuery: {query}\nResponse:"
        
        response = generate_response(prompt)
        
        return response.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    user_query = data.get('query')
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    response = get_response(user_query)
    return jsonify({'response': response})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    load_documents("/app/docs")
    app.run(host='0.0.0.0', port=8080)
