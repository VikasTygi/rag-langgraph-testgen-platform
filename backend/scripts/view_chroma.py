import chromadb

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "automation_repo"

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(name=COLLECTION_NAME)

print("Collection:", COLLECTION_NAME)
print("Total documents:", collection.count())

results = collection.get(
    limit=10,
    include=["documents", "metadatas"]
)

for index, doc in enumerate(results["documents"], start=1):
    print("\n" + "=" * 80)
    print(f"Document {index}")
    print("Metadata:", results["metadatas"][index - 1])
    print("Content:")
    print(doc[:1000])
