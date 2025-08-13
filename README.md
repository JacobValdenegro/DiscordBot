# Bot de Discord con RAG y Gemini para Consultar Leyes

Este es un bot de Discord avanzado que utiliza un sistema de **Generación Aumentada por Recuperación (RAG)** para responder preguntas sobre un documento legal específico (**Ley de Movilidad y Transporte del Estado de Jalisco**).  
El bot está impulsado por la **API de Google Gemini** y utiliza **MongoDB Atlas** para la búsqueda vectorial.

---

## Demo

![demo](https://i.imgur.com/FR0rOsC.png)

---

## Características

- **Respuestas Basadas en Fuentes**: El bot responde utilizando únicamente la información extraída de los documentos PDF proporcionados, evitando “alucinaciones”.
- **Búsqueda Híbrida Inteligente**:
  - **Búsqueda por Palabra Clave**: Detecta automáticamente cuando se pregunta por un número de artículo específico y realiza una búsqueda exacta.
  - **Búsqueda Semántica**: Para preguntas conceptuales, utiliza embeddings vectoriales para encontrar los fragmentos más relevantes.
- **Manejo de Respuestas Largas**: Divide automáticamente las respuestas que exceden el límite de 2000 caracteres de Discord.

---

## Arquitectura y Funcionamiento

El proyecto se divide en dos fases principales:

### Ingesta de Datos (`ingest_documents.py`)
- **Extracción**: Se obtiene el texto de un PDF con **PyMuPDF**.
- **División**: El texto se segmenta por artículos completos.
- **Vectorización**: Se generan embeddings con `text-embedding-004` de Google.
- **Almacenamiento**: Se guarda cada artículo y su embedding en **MongoDB Atlas**.

### Ciclo de Pregunta-Respuesta (`rag.py` y `bot.py`)
1. El bot recibe la pregunta desde Discord.
2. Se analiza si es búsqueda por número de artículo o semántica.
3. Se recuperan los artículos relevantes de MongoDB.
4. Se forma un contexto con esos artículos.
5. El contexto y la pregunta se envían a **Gemini** para generar la respuesta.
6. El bot envía la respuesta a Discord (dividida si es muy larga).

---

## Tech Stack

- **Lenguaje**: Python 3.10+
- **IA & LLM**:
  - Google Gemini API (`gemini-2.5-flash`)
  - Google Text Embedding (`text-embedding-004`)
- **Base de Datos**: MongoDB Atlas (índice de búsqueda vectorial)
- **Framework Discord**: `discord.py`
- **Procesamiento de Datos**:
  - PyMuPDF (fitz)
  - Expresiones regulares (`re`)
- **Librerías Clave**:
  - `pymongo`
  - `google-generativeai`
  - `python-dotenv`

---

## Instalación y Configuración

### Prerrequisitos
- Python 3.10+
- Cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- Clave de API en [Google AI Studio](https://aistudio.google.com/)
- Token de bot de Discord

---

### 1. Clonar el Repositorio
```bash
git clone https://github.com/JacobValdenegro/DiscordBot.git
cd DiscordBot


### 2. Crear un Entorno Virtual

```bash
python -m venv venv
# En Windows
.\venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar Dependencias

Asegúrate de tener un archivo `requirements.txt` con:

```
discord.py
pymongo
google-generativeai
python-dotenv
PyMuPDF
```

Luego instala:

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz:

```env
DISCORD_TOKEN="TU_TOKEN_DE_DISCORD_AQUI"
MONGO_URI="TU_CADENA_DE_CONEXION_DE_MONGO_AQUI"
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"
```

---

## Poblar la Base de Datos

1. Coloca tus PDFs en una carpeta `docs/`.
2. Configura el índice vectorial en MongoDB Atlas:

   * Ve a la colección en Atlas y abre **Search**.
   * Crea un índice llamado `vector_index` con esta configuración:

     ```json
     {
       "fields": [
         {
           "type": "vector",
           "path": "embedding",
           "numDimensions": 768,
           "similarity": "cosine"
         }
       ]
     }
     ```
3. Ejecuta el script:

   ```bash
   python ingest_documents.py
   ```

---

## Iniciar el Bot

```bash
python bot.py
```

Verás el mensaje:

```
Bot conectado como ...
```

---

## Uso

* Saludar:

  ```
  !hola
  ```
* Preguntar por artículo:

  ```
  !pregunta ¿De qué habla el artículo 12?
  ```
* Preguntar concepto:

  ```
  !pregunta ¿Cuál es la sanción por no usar el cinturón de seguridad?
  ```
---

