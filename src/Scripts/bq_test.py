from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../../data/local_dev_sa.json"
client = bigquery.Client()

# List datasets in the project
datasets = list(client.list_datasets())
if datasets:
    print("Datasets accessible by the service account:")
    for d in datasets:
        print(f" - {d.dataset_id}")
else:
    print("No datasets found.")