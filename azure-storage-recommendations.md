# Azure Storage Recommendations for Mirai LMS API

## Executive Summary
Based on your FastAPI codebase analysis, here are my recommendations for storing different data types in Azure to balance cost, performance, and scalability.

## Data Types Identified

1. **Digital Twins (Markdown files)**
   - Text-based persona descriptions
   - Structured markdown format
   - Frequent read/write operations
   - Need versioning and update tracking

2. **Persona Images**
   - Multiple sizes (thumbnail, medium, full)
   - Binary files (PNG/JPG)
   - Static content after generation
   - Served via API endpoints

3. **Training Sets**
   - CSV files for agent optimization
   - Relatively static after creation
   - Used for ML model training

4. **Extracted Structured Data**
   - Derived from digital twins
   - Potentially JSON/structured format
   - Used for analytics and querying

5. **Surveys (Future Feature)**
   - User responses and configurations
   - Structured data requiring queries
   - Potentially transactional

## Recommended Azure Storage Architecture

### 1. **Azure Cosmos DB** - Primary Database
**Use for:** Digital twins, extracted structured data, surveys

**Configuration:**
- **API:** Core (SQL) API for flexible querying
- **Partition Key:** `/lead_id` for digital twins
- **Consistency Level:** Session consistency (balance between performance and consistency)

**Benefits:**
- Serverless pricing tier available (pay per request)
- Built-in versioning with change feed
- Global distribution if needed
- Excellent for JSON/document storage
- Full-text search capabilities
- Low latency (<10ms reads)

**Structure Example:**
```json
{
  "id": "unique-guid",
  "lead_id": "c82e9186-babb-465e-bc5f-77483fec5678",
  "type": "digital_twin",
  "version": 2,
  "markdown_content": "...",
  "extracted_data": {
    "age": 32,
    "income": 120000,
    "lead_classification": "hot"
  },
  "created_at": "2025-01-09T10:00:00Z",
  "updated_at": "2025-01-09T14:30:00Z"
}
```

### 2. **Azure Blob Storage** - Media & Training Data
**Use for:** Persona images, training CSV files, model artifacts

**Container Structure:**
```
- persona-images/
  - {lead_id}/
    - thumbnail.png
    - medium.png
    - full.png
- training-data/
  - digital-twin-creator/
    - dataset_v6.csv
  - synthetic-chat/
    - dataset.csv
- optimized-models/
  - DigitalTwinCreatorAgent_Optimized/
```

**Configuration:**
- **Storage Tier:** Hot for images (frequent access), Cool for training data
- **Access Tier:** Private with SAS tokens for security
- **CDN Integration:** Azure CDN for global image delivery
- **Lifecycle Management:** Auto-archive old versions to Cool/Archive tier

### 3. **Azure Cache for Redis** - Performance Layer
**Use for:** Frequently accessed digital twins, session data, chat history

**Configuration:**
- Basic tier for development, Standard for production
- 250MB should be sufficient initially
- TTL: 1 hour for digital twins, 30 min for chat sessions

### 4. **Azure Table Storage** - Audit & Logs
**Use for:** API access logs, change history, audit trails

**Benefits:**
- Extremely cost-effective for log data
- Simple key-value with timestamp
- Automatic retention policies

## Implementation Strategy

### Phase 1: Core Storage (Week 1-2)
1. Set up Cosmos DB for digital twins
2. Implement Blob Storage for images
3. Create data access layer in FastAPI

### Phase 2: Optimization (Week 3)
1. Add Redis caching layer
2. Implement CDN for images
3. Set up lifecycle policies

### Phase 3: Advanced Features (Week 4+)
1. Implement change feed processing
2. Add full-text search
3. Set up backup strategies

## Cost Optimization Tips

1. **Cosmos DB:**
   - Start with Serverless tier (~$0.25 per million requests)
   - Use point reads where possible (cheaper than queries)
   - Implement proper indexing policies

2. **Blob Storage:**
   - Use lifecycle management to move old data to Cool/Archive
   - Enable soft delete for data protection
   - Consider Reserved Capacity for predictable workloads

3. **Redis Cache:**
   - Start with Basic tier, upgrade only if needed
   - Implement proper eviction policies
   - Monitor memory usage

## Sample Connection Configuration

```python
# config.py
import os
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import redis

# Cosmos DB
cosmos_client = CosmosClient(
    url=os.getenv("COSMOS_ENDPOINT"),
    credential=os.getenv("COSMOS_KEY")
)
database = cosmos_client.get_database_client("mirai-lms")
digital_twins_container = database.get_container_client("digital-twins")

# Blob Storage
blob_service_client = BlobServiceClient(
    account_url=os.getenv("STORAGE_ACCOUNT_URL"),
    credential=os.getenv("STORAGE_KEY")
)
images_container = blob_service_client.get_container_client("persona-images")

# Redis Cache
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=6380,
    password=os.getenv("REDIS_KEY"),
    ssl=True
)
```

## Monitoring & Compliance

1. **Enable Azure Monitor** for all services
2. **Set up alerts** for:
   - High request rates
   - Storage capacity thresholds
   - Failed operations
3. **Implement data retention policies** per compliance requirements
4. **Enable encryption** at rest and in transit for all services

## Estimated Monthly Costs (Initial Scale)

| Service | Configuration | Est. Monthly Cost |
|---------|--------------|-------------------|
| Cosmos DB | Serverless, <1M requests | $25-50 |
| Blob Storage | 100GB Hot, 500GB Cool | $30-40 |
| Redis Cache | Basic C0 (250MB) | $16 |
| CDN | Standard, 100GB transfer | $8-10 |
| **Total** | | **~$80-115** |

## Next Steps

1. Review and approve storage architecture
2. Set up Azure resources in development environment
3. Implement data access layer abstractions
4. Migrate existing file-based storage
5. Performance testing and optimization

This architecture provides a scalable, cost-effective solution that can grow with your application while maintaining excellent performance and reliability.