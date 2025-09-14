import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from azure.core.exceptions import ResourceNotFoundError
from agent_dojo.agents.DigitalTwinCreatorAgent.InsuranceProspectModel import InsuranceProspect
from storage.azure_config import azure_config
import hashlib
import dataclasses

# Add a custom JSON encoder for dataclasses
class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)

class ScalableDigitalTwinStorage:
    def __init__(self):
        self.blob_container = azure_config.get_blob_container_client("digital-twins")
        self.metadata_container = azure_config.get_cosmos_container_client("metadata")
        
    def _get_blob_path(self, lead_id: str) -> str:
        return f"{lead_id}.md"
    
    async def save_digital_twin(self, lead_id: str, markdown: str, insurance_prospect: Optional[InsuranceProspect] = None) -> Dict[str, Any]:
        blob_path = self._get_blob_path(lead_id)
        
        # Save markdown to blob storage
        if self.blob_container:
            blob_client = self.blob_container.get_blob_client(blob_path)
            blob_client.upload_blob(markdown, overwrite=True)
        
        # Save insurance prospect to Cosmos DB
        if self.metadata_container and insurance_prospect:
            # Convert insurance_prospect to dict
            prospect_dict = dataclasses.asdict(insurance_prospect) if dataclasses.is_dataclass(insurance_prospect) else insurance_prospect
            
            # Create metadata document for Cosmos DB
            metadata_doc = {
                "id": lead_id,
                "partition_key": datetime.now().strftime('%Y-%m'),
                "blob_path": blob_path,
                "lead_classification": insurance_prospect.lead_classification if hasattr(insurance_prospect, 'lead_classification') else "unknown",
                "persona_summary": insurance_prospect.persona_summary if hasattr(insurance_prospect, 'persona_summary') else "Unknown",
                "personal_information": prospect_dict.get('personal_information', {}),
                "demographic_information": prospect_dict.get('demographic_information', {}),
                "financial_information": prospect_dict.get('financial_information', {}),
                "insurance_history": prospect_dict.get('insurance_history', {}),
                "last_updated": datetime.utcnow().isoformat(),
                "content_hash": hashlib.md5(markdown.encode()).hexdigest()
            }
            
            # Upsert to Cosmos DB
            self.metadata_container.upsert_item(metadata_doc)
        
        return {
            "lead_id": lead_id,
            "blob_path": blob_path,
        }
    
    async def get_digital_twin(self, lead_id: str) -> Optional[str]:
        # Try to get from blob storage directly
        if self.blob_container:
            blob_path = f"{lead_id}.md"
            blob_client = self.blob_container.get_blob_client(blob_path)
            try:
                content = blob_client.download_blob().readall().decode('utf-8')
                return content
            except ResourceNotFoundError:
                pass
        
        return None
    
    async def get_digital_twin_with_metadata(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get both the markdown content and metadata for a digital twin"""
        result = {}
        
        # Get metadata from Cosmos DB
        if self.metadata_container:
            query = "SELECT * FROM c WHERE c.id = @lead_id"
            items = list(self.metadata_container.query_items(
                query=query,
                parameters=[{"name": "@lead_id", "value": lead_id}],
                max_item_count=1,
                enable_cross_partition_query=True
            ))
            
            if items:
                result['metadata'] = items[0]
        
        # Get markdown from blob storage
        markdown = await self.get_digital_twin(lead_id)
        if markdown:
            result['markdown'] = markdown
        
        return result if result else None
    
    async def get_digital_twin_metadata(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get only the metadata from Cosmos DB"""
        if self.metadata_container:
            query = "SELECT * FROM c WHERE c.id = @lead_id"
            items = list(self.metadata_container.query_items(
                query=query,
                parameters=[{"name": "@lead_id", "value": lead_id}],
                max_item_count=1,
                enable_cross_partition_query=True
            ))
            
            if items:
                return items[0]
        
        return None
    
    async def list_digital_twins(self, classification: Optional[str] = None, 
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """List digital twins combining data from Cosmos DB and blob storage"""
        results = []
        
        if self.metadata_container:
            # Query Cosmos DB for metadata
            if classification:
                query = "SELECT * FROM c WHERE c.lead_classification = @classification ORDER BY c.last_updated DESC"
                parameters = [{"name": "@classification", "value": classification}]
            else:
                query = "SELECT * FROM c ORDER BY c.last_updated DESC"
                parameters = []
            
            items = list(self.metadata_container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit,
                enable_cross_partition_query=True
            ))
            
            # For each item, optionally fetch the markdown content
            for item in items:
                lead_id = item.get('id')
                result_item = {
                    'id': lead_id,
                    'metadata': item
                }
                
                # Optionally fetch markdown content (you can skip this if not needed for listing)
                # markdown = await self.get_digital_twin(lead_id)
                # if markdown:
                #     result_item['markdown'] = markdown
                
                results.append(result_item)
        
        return results
    
    async def delete_digital_twin(self, lead_id: str) -> bool:
        """Delete digital twin from both blob storage and Cosmos DB"""
        deleted = False
        
        # Delete from blob storage
        if self.blob_container:
            blob_path = f"{lead_id}.md"
            blob_client = self.blob_container.get_blob_client(blob_path)
            try:
                blob_client.delete_blob()
                deleted = True
            except:
                pass
        
        # Delete from Cosmos DB
        if self.metadata_container:
            try:
                # Need to get the item first to know the partition key
                metadata = await self.get_digital_twin_metadata(lead_id)
                if metadata:
                    self.metadata_container.delete_item(
                        item=lead_id,
                        partition_key=metadata.get('partition_key')
                    )
                    deleted = True
            except:
                pass
        
        return deleted
    
    async def update_classification(self, lead_id: str, new_classification: str) -> bool:
        """Update the lead classification in Cosmos DB"""
        if self.metadata_container:
            try:
                # Get existing metadata
                metadata = await self.get_digital_twin_metadata(lead_id)
                if metadata:
                    # Update classification
                    metadata['lead_classification'] = new_classification
                    metadata['last_updated'] = datetime.utcnow().isoformat()
                    
                    # Upsert back to Cosmos DB
                    self.metadata_container.upsert_item(metadata)
                    return True
            except Exception as e:
                print(f"Error updating classification: {e}")
        
        return False
    
    async def search_by_criteria(self, criteria: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search digital twins based on various criteria"""
        if not self.metadata_container:
            return []
        
        # Build dynamic query based on criteria
        conditions = []
        parameters = []
        
        if 'min_age' in criteria:
            conditions.append("c.personal_information.age >= @min_age")
            parameters.append({"name": "@min_age", "value": str(criteria['min_age'])})
        
        if 'max_age' in criteria:
            conditions.append("c.personal_information.age <= @max_age")
            parameters.append({"name": "@max_age", "value": str(criteria['max_age'])})
        
        if 'occupation' in criteria:
            conditions.append("CONTAINS(c.personal_information.occupation, @occupation)")
            parameters.append({"name": "@occupation", "value": criteria['occupation']})
        
        if 'location' in criteria:
            conditions.append("CONTAINS(c.demographic_information.location, @location)")
            parameters.append({"name": "@location", "value": criteria['location']})
        
        if 'marital_status' in criteria:
            conditions.append("c.demographic_information.marital_status = @marital_status")
            parameters.append({"name": "@marital_status", "value": criteria['marital_status']})
        
        if 'lead_classification' in criteria:
            conditions.append("c.lead_classification = @lead_classification")
            parameters.append({"name": "@lead_classification", "value": criteria['lead_classification']})
        
        # Build final query
        if conditions:
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.last_updated DESC"
        else:
            query = "SELECT * FROM c ORDER BY c.last_updated DESC"
        
        items = list(self.metadata_container.query_items(
            query=query,
            parameters=parameters,
            max_item_count=limit,
            enable_cross_partition_query=True
        ))
        
        return items