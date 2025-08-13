import re
from pymongo import MongoClient
import google.generativeai as genai
from config import GEMINI_API_KEY, MONGO_URI

genai.configure(api_key=GEMINI_API_KEY)
modelo_llm = genai.GenerativeModel("gemini-2.5-flash")
client = MongoClient(MONGO_URI)
db = client["chatbot_pdf"]
collection = db["documentos"]

prompt_final = """
Eres un asistente legal experto en la Ley de Movilidad de Jalisco. Tu tarea es responder la pregunta del usuario basándote estricta y únicamente en el contexto proporcionado.

**Instrucciones de Respuesta:**

1.  **Respuesta Directa:** Si el contexto contiene una respuesta directa a la pregunta del usuario, proporciónala de forma clara y concisa.
2.  **Manejo de Variantes de Artículos (MUY IMPORTANTE):** Si el usuario pregunta por un número de artículo (ej. "Artículo 183") y el contexto contiene una variante cercana (ej. "Artículo 183 bis", "Artículo 183 ter"), ASUME que el usuario está interesado en esa variante. Responde explicando el contenido de la variante que encontraste, pero aclara que es una variante. Por ejemplo: "No encontré un Artículo 183, pero el Artículo 183 bis establece lo siguiente: [explicación]".
3.  **Sin Información:** Si después de seguir las reglas anteriores, la información para responder la pregunta no se encuentra en el contexto, responde única y exclusivamente con la frase: "La información solicitada no se encuentra en mi base de conocimiento." No inventes nada.

**Contexto:**
{contexto}

**Pregunta:**
{pregunta}

**Respuesta:**
"""

def buscar_contexto_semantico(pregunta, collection, k=3):
    print("--- Realizando BÚSQUEDA SEMÁNTICA (vectorial con Google) ---")

    embedding_pregunta = genai.embed_content(
        model='models/text-embedding-004',
        content=pregunta,
        task_type="retrieval_query"
    )['embedding']

    pipeline = [
        {"$vectorSearch": {
            "index": "vector_index", "path": "embedding",
            "queryVector": embedding_pregunta,
            "numCandidates": 150, "limit": k
        }}
    ]
    try:
        documentos = list(collection.aggregate(pipeline))
        print(f"Búsqueda semántica encontró {len(documentos)} documentos.")
        return "\n\n".join([doc['texto'] for doc in documentos])
    except Exception as e:
        print(f"ERROR en búsqueda semántica: {e}")
        return ""

def buscar_articulo_por_numero(numero_articulo, collection):
    print(f"--- Realizando BÚSQUEDA POR PALABRA CLAVE para el Artículo: {numero_articulo} ---")
    regex_pattern = f"^Artículo {re.escape(numero_articulo)}(?!\\d)"

    print(f"Intentando búsqueda con regex: '{regex_pattern}'")
    
    try:
        documento = collection.find_one({"texto": {"$regex": regex_pattern, "$options": "i"}})
        
        if documento:
            print("Artículo encontrado.")
            return documento['texto']
        else:
            print("Artículo NO encontrado.")
            return None
            
    except Exception as e:
        print(f"ERROR en búsqueda por palabra clave: {e}")
        return None


def responder_con_estilo(pregunta):
    print(f"\n--- INICIO DE PROCESO para la pregunta: '{pregunta}' ---")
    
    contexto = None
    match = re.search(r'art[íi]culo\s+(\d+\s*[\w-]*)', pregunta, re.IGNORECASE)
    
    if match:
        numero_articulo = re.sub(r'\s+', ' ', match.group(1)).strip()
        contexto = buscar_articulo_por_numero(numero_articulo, collection)

    if not contexto:
        contexto = buscar_contexto_semantico(pregunta, collection)
    
    if not contexto:
        print("Contexto final está VACÍO. Respondiendo directamente.")
        return "La información solicitada no se encuentra en mi base de conocimiento."

    prompt_completo = prompt_final.format(contexto=contexto, pregunta=pregunta)
    
    try:
        respuesta = modelo_llm.generate_content(prompt_completo)
        return respuesta.text
    except Exception as e:
        print(f"ERROR al generar contenido con Gemini: {e}")
        return "Ocurrió un error al intentar generar la respuesta."