from memoripy import MemoryManager
from memoripy.cosmos_storage import CosmosStorage
from memoripy.implemented_models import AzureOpenAIEmbeddingModel, AzureOpenAIChatModel
import os
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Set here your actual Azure OpenAI API key, endpoint and API version
    # Or rely on environment variables if the models support it (they usually do)
    # For this example, we'll try to read from env or use empty strings as placeholders
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    # Define chat and embedding models
    chat_model_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    embedding_model_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

    # Choose your storage option
    try:
        # CosmosStorage supports both Key-based and Managed Identity authentication.
        # If MEMORIPY_COSMOS_KEY is set, it uses the key.
        # If MEMORIPY_COSMOS_KEY is missing, it attempts to use DefaultAzureCredential (MSI/Azure CLI).
        storage_option = CosmosStorage("default")
    except ValueError as e:
        print(f"Error initializing CosmosStorage: {e}")
        print("Please ensure you have set the MEMORIPY_COSMOS_* environment variables.")
        return

    # Initialize the MemoryManager with the selected models and storage
    memory_manager = MemoryManager(
        AzureOpenAIChatModel(
            azure_api_key, azure_api_version, azure_api_endpoint, chat_model_name
        ),
        AzureOpenAIEmbeddingModel(
            azure_api_key, azure_api_version, azure_api_endpoint, embedding_model_name
        ),
        storage=storage_option,
    )

    # New user prompt
    new_prompt = "My name is David"

    # Load the last 5 interactions from history (for context)
    short_term, _ = memory_manager.load_history()
    last_interactions = short_term[-5:] if len(short_term) >= 5 else short_term

    # Retrieve relevant past interactions, excluding the last 5
    relevant_interactions = memory_manager.retrieve_relevant_interactions(
        new_prompt, exclude_last_n=5
    )

    # Generate a response using the last interactions and retrieved interactions
    response = memory_manager.generate_response(
        new_prompt, last_interactions, relevant_interactions
    )

    # Display the response
    print(f"Generated response:\n{response}")

    # Extract concepts for the new interaction
    combined_text = f"{new_prompt} {response}"
    concepts = memory_manager.extract_concepts(combined_text)

    # Store this new interaction along with its embedding and concepts
    new_embedding = memory_manager.get_embedding(combined_text)
    memory_manager.add_interaction(new_prompt, response, new_embedding, concepts)


if __name__ == "__main__":
    main()
