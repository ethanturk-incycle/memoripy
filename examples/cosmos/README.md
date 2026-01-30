# Storage Adapter for Azure Cosmos DB

A memoripy storage adapter to leverage Azure Cosmos DB as the memory persistence layer.

## Setup

To run this example, you need an Azure Cosmos DB account (SQL API).

### 1. Configuration

Copy the `.env.example` file to the root of the repository (or where you run the script from) and rename it to `.env`.

```shell
cp examples/cosmos/.env.example .env
```

Fill in your Azure Cosmos DB details in the `.env` file:

```dotenv
MEMORIPY_COSMOS_ENDPOINT=https://your-cosmos-db-account.documents.azure.com:443/
MEMORIPY_COSMOS_KEY=your_primary_key
MEMORIPY_COSMOS_DATABASE=memoripy
MEMORIPY_COSMOS_CONTAINER=memory_store
```

You also need to configure your LLM provider (e.g., Azure OpenAI) in the `.env` file as well, as this example uses it to generate embeddings and responses.

```dotenv
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=...
AZURE_OPENAI_CHAT_DEPLOYMENT=...
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...
```

## Running the Example

Once your environment is configured, run the example:

```shell
python -m examples.cosmos.cosmos_example
```

## Available Environment Variables

* `MEMORIPY_COSMOS_ENDPOINT`: The URI of your Azure Cosmos DB account.
* `MEMORIPY_COSMOS_KEY`: The primary or secondary key for your Cosmos DB account.
* `MEMORIPY_COSMOS_DATABASE` (default: `memoripy`): The name of the database.
* `MEMORIPY_COSMOS_CONTAINER` (default: `memory_store`): The name of the container.
