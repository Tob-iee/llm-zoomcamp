import json
import time
import requests 

import streamlit as st
from openai import OpenAI
from tqdm.auto import tqdm
from elasticsearch import Elasticsearch


client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama',
)

es_client = Elasticsearch('http://localhost:9200')

# for doc in tqdm(documents):
#     es_client.index(index=index_name, document=doc)

def elastic_search(query, index_name = "course-quesions"):
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
             
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "text", "section"],
                        "type": "best_fields"
                    }
                },
                "filter": {
                    "term": {
                        "course": "data-engineering-zoomcamp"
                    }
                }
            }
        }
    }

    response = es_client.search(index=index_name, body=search_query)
    
    result_docs = []
    
    for hit in response['hits']['hits']:
        result_docs.append(hit['_source'])
    
    return result_docs

def build_prompt(query, search_results):
    prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = ""
    
    for doc in search_results:
        context = context + f"section: {doc['section']}\nquestion: {doc['question']}\nanswer: {doc['text']}\n\n"
    
    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

def llm(prompt):
    response = client.chat.completions.create(
        model='phi3',
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

# Define the 'rag' function (replace with your actual function logic)
def rag(query):
    search_results = elastic_search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)
    return answer

# Streamlit application
def main():
    st.title("Streamlit Ask App")

    # Input box for user query
    user_input = st.text_input("Enter your question:")

    # 'Ask' button
    if st.button("Ask"):
        with st.spinner("Processing..."):
            # Call the rag function
            output = rag(user_input)
            # Display the output
            st.success("Completed!")
            st.write(output)

if __name__ == "__main__":
    main()
