import os
import re
from pymongo import MongoClient
import fitz
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
uri = os.getenv("MONGO_URI")
if not uri:
    raise ValueError("La URI de MongoDB no está definida.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("La GEMINI_API_KEY no está definida.")
genai.configure(api_key=GEMINI_API_KEY)

client = MongoClient(uri)
db = client["chatbot_pdf"]
collection = db["documentos"]

def extract_and_clean_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        lines = text.strip().split('\n')
        if lines and lines[-1].strip() == str(page_num + 1):
            text = '\n'.join(lines[:-1])
        full_text += text + "\n"
    doc.close()
    return full_text

def create_chunks_from_text(text):

    articles = {}
    current_article_key = None
    article_pattern = re.compile(r'^Artículo\s+([\d\w\s-]+?)(?:\.|\s-|-)', re.IGNORECASE)

    for line in text.split('\n'):
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        match = article_pattern.match(cleaned_line)
        if match:
            current_article_key = match.group(1).strip()
            articles[current_article_key] = cleaned_line + " "
        elif current_article_key is not None:
            articles[current_article_key] += cleaned_line + " "
            
    return [re.sub(r'\s+', ' ', article_text).strip() for article_text in articles.values()]

def generate_embeddings_with_google(text_list):
    print(f"Generando embeddings para {len(text_list)} chunks con el modelo de Google...")
    all_embeddings = []
    batch_size = 100
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i+batch_size]
        print(f"  Procesando lote {i//batch_size + 1}...")
        result = genai.embed_content(
            model='models/text-embedding-004',
            content=batch,
            task_type="retrieval_document"
        )
        all_embeddings.extend(result['embedding'])
    print("Embeddings generados exitosamente.")
    return all_embeddings

def process_pdf_and_store_in_mongodb(pdf_path):
    pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
    print(f"--- Procesando PDF: {pdf_name} ---")
    
    collection.delete_many({"titulo": pdf_name})
    print("1. Datos antiguos eliminados.")

    text = extract_and_clean_text_from_pdf(pdf_path)
    print(f"2. Texto extraído y limpiado ({len(text)} caracteres).")
    
    chunks = create_chunks_from_text(text)
    
    if not chunks:
        print("ERROR: No se pudieron generar chunks. Revisa el PDF.")
        return

    print(f"3. {len(chunks)} artículos (fragmentos) generados.")
    print("4. Generando embeddings...")
    embeddings = generate_embeddings_with_google(chunks)
    documents = [{"titulo": pdf_name, "texto": chunk, "embedding": emb} for chunk, emb in zip(chunks, embeddings)]

    if documents:
        collection.insert_many(documents)
        print(f"5. PDF '{pdf_name}' procesado y almacenado.")

pdf_directory = "file.pdf"
for file in os.listdir(pdf_directory):
    if file.endswith(".pdf"):
        process_pdf_and_store_in_mongodb(os.path.join(pdf_directory, file))
print("\n¡PROCESO DE CARGA COMPLETADO!")