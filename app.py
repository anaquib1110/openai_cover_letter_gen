import gradio as gr
import os
from dotenv import load_dotenv
import fitz  # PyMuPDF
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai  # Correct import for openai library

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key  # Set the API key globally for openai library

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text("text")
    return text

# Function to split text into chunks
def split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Function to create vector store
def create_vector_store(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embeddings)
    return vector_store

# Function to perform RAG
def perform_rag(vector_store, query):
    retriever = vector_store.as_retriever()
    docs = retriever.get_relevant_documents(query)
    context = " ".join([doc.page_content for doc in docs])
    return context

# Function to generate cover letter using OpenAI API
def generate_cover_letter(pdf_path, job_role, company_name, company_context):
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    # Split text into chunks
    chunks = split_text_into_chunks(text)
    # Create vector store
    vector_store = create_vector_store(chunks)
    # Perform RAG
    candidate_profile = perform_rag(vector_store, job_role)

    # Define the prompt for OpenAI API
    prompt = f"""
    So, I am applying for {job_role} at {company_name}
    =================
    {company_context}
    =================
    {candidate_profile}
    =================
    From the company profile and my profile, please create a cover letter for the {job_role} position. Ensure that it is well-crafted and engaging for recruiters and hiring managers. Also, verify that my recent work experience and academic background align with the role I am applying for.
    """

    # Call OpenAI API to generate cover letter
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt}
        ],
        max_tokens=500
    )

    generated_cover_letter = response['choices'][0]['message']['content'].strip()

    return generated_cover_letter

# Create Gradio interface
gr.Interface(
    fn=generate_cover_letter,
    inputs=[
        gr.File(label="Upload ATS Resume (PDF)", file_types=[".pdf"]),
        gr.Textbox(label="Job Role", placeholder="Ex: Data Scientist, Fullstack Developer, etc."),
        gr.Textbox(label="Company Name", placeholder="Enter a company name you are applying to"),
        gr.Textbox(label="Company Context", placeholder="Enter a brief description of the company")
    ],
    outputs=gr.Textbox(label="Generated Cover Letter", show_copy_button=True),
    title="Cover Letter Generator",
    description="Generate a cover letter based on your job role, company, context, and profile."
).launch()
