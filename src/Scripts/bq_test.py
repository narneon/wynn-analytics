from google.cloud import bigquery
import dotenv

dotenv.load_dotenv()
client = bigquery.Client()

# List datasets in the project
datasets = list(client.list_datasets())
if datasets:
    print("Datasets accessible by the service account:")
    for d in datasets:
        print(f" - {d.dataset_id}")
else:
    print("No datasets found.")