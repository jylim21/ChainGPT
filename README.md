# ChainGPT
A self-hosting ChatGPT chatbot clone using LangChain and Chainlit, running on Ollama and powered by Mistral.

# Dependencies
### Modules
- langchain v0.3
- langchain-core>=0.3.40
- langchain-ollama>=0.2.3
- langchain-chroma>=0.2.2
- chainlit>=2.2.1
- chromadb>=0.6.3
- psycopg2>=2.9.10
- bcrypt>=4.2.1

### Applications
- [Ollama](https://ollama.com/download) with 'mistral' model (run <code>ollama pull mistral</code> to install)
- PostgreSQL

# Installation
1. Clone this repository
    ```bash
    git clone https://github.com/jylim21/ChainGPT
    cd ChainGPT
    ```
2. Open PostgreSQL and create a new database, run the <code>postgres_init.sql</code> SQL script to initialize the database.
3. Open the <code>env_example.env</code> using any text editor.
4. Enter your Postgres user and database details into the <code>DB_HOST</code>, <code>DB_USER</code>, <code>DB_PASSWORD</code>, and <code>DB_NAME</code> fields.
5. In your terminal, generate a chainlit secret key by typing the following command:
   ```bash
    chainlit create-secret
   ```
   Copy the generated key and paste it inside your .env file's <code>CHAINLIT_AUTH_SECRET</code> field. Save the .env file.
6. Register a local user account by running the <code>register.py</code> file, then type in your username and password. This user account will be used to save chat history for each user.
    ```bash
    python register.py
    ```
    ```bash
    Enter a new username: <YOUR USERNAME HERE>
    Enter a new password: <YOUR PASSWORD HERE>
    ```
7. Run the chatbot using the following:
    ```bash
    chainlit run app.py
    ```

