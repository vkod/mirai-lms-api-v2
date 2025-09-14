# Azure Setup Instructions for Mirai LMS API

This guide will walk you through setting up the required Azure services for the Mirai LMS API storage system.

## Prerequisites
- Azure Account with active subscription
- Azure CLI installed (optional but recommended)
- Access to Azure Portal

## Step 1: Create Azure Storage Account

### Via Azure Portal:
1. Navigate to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → Search for "Storage account"
3. Configure:
   - **Resource Group**: Create new or use existing (e.g., `mirai-lms-rg`)
   - **Storage account name**: Choose unique name (e.g., `mirailmsstorage`)
   - **Region**: Select closest to your users
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally-redundant storage) for dev, GRS for production
4. Click "Review + create" → "Create"
5. Once deployed, go to the storage account
6. Navigate to "Access keys" → Copy the connection string
7. Add to `.env` file as `AZURE_STORAGE_CONNECTION_STRING`

### Via Azure CLI:
```bash
# Create resource group
az group create --name mirai-lms-rg --location eastus

# Create storage account
az storage account create \
  --name mirailmsstorage \
  --resource-group mirai-lms-rg \
  --location eastus \
  --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
  --name mirailmsstorage \
  --resource-group mirai-lms-rg \
  --query connectionString -o tsv
```

## Step 2: Create Azure Cosmos DB Account

### Via Azure Portal:
1. Click "Create a resource" → Search for "Azure Cosmos DB"
2. Select "Core (SQL) - Recommended"
3. Configure:
   - **Resource Group**: Use same as storage (e.g., `mirai-lms-rg`)
   - **Account Name**: Choose unique name (e.g., `mirai-lms-cosmos`)
   - **Location**: Same as storage account
   - **Capacity mode**: Serverless (for cost optimization)
   - **Geo-Redundancy**: Disable for dev
   - **Multi-region Writes**: Disable
4. Click "Review + create" → "Create"
5. Once deployed, go to Cosmos DB account
6. Navigate to "Keys" → Copy:
   - URI → Add to `.env` as `COSMOS_ENDPOINT`
   - PRIMARY KEY → Add to `.env` as `COSMOS_KEY`

### Via Azure CLI:
```bash
# Create Cosmos DB account
az cosmosdb create \
  --name mirai-lms-cosmos \
  --resource-group mirai-lms-rg \
  --capabilities EnableServerless \
  --default-consistency-level Session

# Get endpoint and key
az cosmosdb show \
  --name mirai-lms-cosmos \
  --resource-group mirai-lms-rg \
  --query documentEndpoint -o tsv

az cosmosdb keys list \
  --name mirai-lms-cosmos \
  --resource-group mirai-lms-rg \
  --query primaryMasterKey -o tsv
```

## Step 3: Create Azure Cache for Redis (Optional but Recommended)

### Via Azure Portal:
1. Click "Create a resource" → Search for "Azure Cache for Redis"
2. Configure:
   - **Resource Group**: Use same (e.g., `mirai-lms-rg`)
   - **DNS name**: Choose unique name (e.g., `mirai-lms-cache`)
   - **Location**: Same as other resources
   - **Cache type**: Basic C0 (250 MB) for dev
   - **Redis version**: 6 (latest stable)
3. Click "Review + create" → "Create"
4. Once deployed (takes 15-20 minutes), go to the cache
5. Navigate to "Access keys" → Copy:
   - Hostname → Add to `.env` as `REDIS_HOST`
   - Primary access key → Add to `.env` as `REDIS_KEY`

### Via Azure CLI:
```bash
# Create Redis Cache
az redis create \
  --name mirai-lms-cache \
  --resource-group mirai-lms-rg \
  --location eastus \
  --sku Basic \
  --vm-size c0

# Get hostname and key
az redis show \
  --name mirai-lms-cache \
  --resource-group mirai-lms-rg \
  --query hostName -o tsv

az redis list-keys \
  --name mirai-lms-cache \
  --resource-group mirai-lms-rg \
  --query primaryKey -o tsv
```

## Step 4: Create Azure AI Search (Optional for Advanced Search)

### Via Azure Portal:
1. Click "Create a resource" → Search for "Azure AI Search"
2. Configure:
   - **Resource Group**: Use same (e.g., `mirai-lms-rg`)
   - **Service name**: Choose unique name (e.g., `mirai-lms-search`)
   - **Location**: Same as other resources
   - **Pricing tier**: Basic (for up to 15 indexes)
3. Click "Review + create" → "Create"
4. Once deployed, go to the search service
5. Navigate to "Keys" → Copy:
   - URL → Add to `.env` as `AZURE_SEARCH_ENDPOINT`
   - Admin key → Add to `.env` as `AZURE_SEARCH_KEY`

### Via Azure CLI:
```bash
# Create Search Service
az search service create \
  --name mirai-lms-search \
  --resource-group mirai-lms-rg \
  --sku basic \
  --location eastus

# Get endpoint and key
az search service show \
  --name mirai-lms-search \
  --resource-group mirai-lms-rg \
  --query hostName -o tsv

az search admin-key show \
  --service-name mirai-lms-search \
  --resource-group mirai-lms-rg \
  --query primaryKey -o tsv
```

## Step 5: Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update `.env` with your Azure credentials:
```env
# Required
AZURE_STORAGE_CONNECTION_STRING=<from-step-1>
COSMOS_ENDPOINT=<from-step-2>
COSMOS_KEY=<from-step-2>

# Optional but recommended
REDIS_HOST=<from-step-3>
REDIS_KEY=<from-step-3>

# Optional for advanced search
AZURE_SEARCH_ENDPOINT=<from-step-4>
AZURE_SEARCH_KEY=<from-step-4>
AZURE_SEARCH_INDEX_NAME=digital-twins-index
```

## Step 6: Initialize Storage Containers

Run the application once to auto-create required containers:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The application will automatically create:
- Blob containers: `digital-twins`, `persona-images`, `training-data`, `optimized-models`
- Cosmos DB database: `mirai-lms` with containers `metadata` and `surveys`

## Step 7: Create Search Index (If using Azure AI Search)

If you're using Azure AI Search, create the index:

```python
# Run this Python script once to create the search index
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType
)
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()

# Create index client
index_client = SearchIndexClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

# Define index schema
index = SearchIndex(
    name="digital-twins-index",
    fields=[
        SimpleField(name="lead_id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="persona_summary", type=SearchFieldDataType.String),
        SimpleField(name="lead_classification", type=SearchFieldDataType.String, 
                   filterable=True, facetable=True),
        SimpleField(name="age", type=SearchFieldDataType.Int32, 
                   filterable=True, facetable=True),
        SimpleField(name="income", type=SearchFieldDataType.Double, 
                   filterable=True, facetable=True),
        SearchableField(name="location", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
        SearchableField(name="occupation", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
        SimpleField(name="marital_status", type=SearchFieldDataType.String, 
                   filterable=True, facetable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="last_updated", type=SearchFieldDataType.DateTimeOffset, 
                   sortable=True)
    ]
)

# Create index
index_client.create_index(index)
print("Search index created successfully!")
```

## Step 8: Verify Setup

Test the setup with curl commands:

```bash
# Test health endpoint
curl http://localhost:8000/

# Create a digital twin
curl -X POST http://localhost:8000/test_digital_twin_agent \
  -H "Content-Type: application/json" \
  -d '{"data": "Test user data", "existing_digital_twin": ""}'

# Search digital twins
curl -X POST http://localhost:8000/search_digital_twins \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "filters": {}, "top": 10}'
```

## Cost Optimization Tips

1. **Development Environment**:
   - Use Serverless tier for Cosmos DB
   - Use Basic tier for Redis Cache
   - Use Hot tier for frequently accessed blobs
   - Consider skipping AI Search initially

2. **Production Environment**:
   - Enable auto-scaling for Cosmos DB
   - Use Standard tier for Redis with appropriate size
   - Implement blob lifecycle policies
   - Use Cool/Archive tiers for old data

3. **Monitoring**:
   - Set up cost alerts in Azure Portal
   - Monitor usage patterns
   - Review Azure Advisor recommendations

## Troubleshooting

### Connection Issues
- Ensure all environment variables are set correctly
- Check firewall rules allow connections
- Verify service endpoints are accessible

### Permission Issues
- Ensure your Azure account has necessary permissions
- Check access keys are valid and not expired

### Performance Issues
- Check Redis cache hit ratio
- Monitor Cosmos DB RU consumption
- Review blob storage metrics

## Clean Up Resources

To avoid charges when not using:

```bash
# Delete entire resource group (WARNING: Deletes all resources)
az group delete --name mirai-lms-rg --yes

# Or stop specific services
az redis stop --name mirai-lms-cache --resource-group mirai-lms-rg
```

## Support

For issues or questions:
1. Check Azure service health
2. Review application logs
3. Consult Azure documentation
4. Contact Azure support if needed