from typing import List, Dict, Any, Optional
from storage.azure_config import azure_config

class DigitalTwinSearch:
    def __init__(self):
        self.search_client = azure_config.get_search_client()
        self.metadata_container = azure_config.get_cosmos_container_client("metadata")
    
    def search_twins(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                    top: int = 50) -> List[Dict[str, Any]]:
        if self.search_client:
            filter_expression = self._build_filter(filters)
            
            try:
                results = self.search_client.search(
                    search_text=query,
                    filter=filter_expression,
                    select=["lead_id", "lead_classification", "persona_summary", 
                           "age", "income", "location", "occupation"],
                    top=top,
                    include_total_count=True
                )
                
                return {
                    "results": [dict(result) for result in results],
                    "total_count": results.get_count() if hasattr(results, 'get_count') else 0
                }
            except Exception as e:
                print(f"Search error: {e}")
                return self._fallback_search(query, filters, top)
        else:
            return self._fallback_search(query, filters, top)
    
    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        if not filters:
            return None
        
        conditions = []
        
        if "classification" in filters:
            conditions.append(f"lead_classification eq '{filters['classification']}'")
        
        if "min_income" in filters:
            conditions.append(f"income ge {filters['min_income']}")
        
        if "max_income" in filters:
            conditions.append(f"income le {filters['max_income']}")
        
        if "min_age" in filters:
            conditions.append(f"age ge {filters['min_age']}")
        
        if "max_age" in filters:
            conditions.append(f"age le {filters['max_age']}")
        
        if "location" in filters:
            conditions.append(f"location eq '{filters['location']}'")
        
        if "marital_status" in filters:
            conditions.append(f"marital_status eq '{filters['marital_status']}'")
        
        return " and ".join(conditions) if conditions else None
    
    def _fallback_search(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                        top: int = 50) -> List[Dict[str, Any]]:
        if not self.metadata_container:
            return {"results": [], "total_count": 0}
        
        where_clauses = []
        parameters = []
        
        if query:
            where_clauses.append(
                "(CONTAINS(LOWER(c.persona_summary), LOWER(@query)) OR " +
                "CONTAINS(LOWER(c.occupation), LOWER(@query)) OR " +
                "CONTAINS(LOWER(c.location), LOWER(@query)))"
            )
            parameters.append({"name": "@query", "value": query})
        
        if filters:
            if "classification" in filters:
                where_clauses.append("c.lead_classification = @classification")
                parameters.append({"name": "@classification", "value": filters['classification']})
            
            if "min_income" in filters:
                where_clauses.append("c.income >= @min_income")
                parameters.append({"name": "@min_income", "value": filters['min_income']})
            
            if "max_income" in filters:
                where_clauses.append("c.income <= @max_income")
                parameters.append({"name": "@max_income", "value": filters['max_income']})
            
            if "min_age" in filters:
                where_clauses.append("c.age >= @min_age")
                parameters.append({"name": "@min_age", "value": filters['min_age']})
            
            if "max_age" in filters:
                where_clauses.append("c.age <= @max_age")
                parameters.append({"name": "@max_age", "value": filters['max_age']})
            
            if "location" in filters:
                where_clauses.append("c.location = @location")
                parameters.append({"name": "@location", "value": filters['location']})
            
            if "marital_status" in filters:
                where_clauses.append("c.marital_status = @marital_status")
                parameters.append({"name": "@marital_status", "value": filters['marital_status']})
        
        if where_clauses:
            query_text = f"SELECT * FROM c WHERE {' AND '.join(where_clauses)} ORDER BY c.last_updated DESC"
        else:
            query_text = "SELECT * FROM c ORDER BY c.last_updated DESC"
        
        try:
            items = list(self.metadata_container.query_items(
                query=query_text,
                parameters=parameters,
                max_item_count=top
            ))
            
            return {
                "results": items,
                "total_count": len(items)
            }
        except Exception as e:
            print(f"Fallback search error: {e}")
            return {"results": [], "total_count": 0}
    
    def get_facets(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.metadata_container:
            return {}
        
        facets = {
            "classifications": [],
            "locations": [],
            "age_ranges": [],
            "income_ranges": [],
            "marital_statuses": []
        }
        
        try:
            query = "SELECT DISTINCT c.lead_classification FROM c WHERE c.lead_classification != null"
            classifications = list(self.metadata_container.query_items(query=query))
            facets["classifications"] = [{"value": c["lead_classification"], "count": 0} 
                                        for c in classifications]
            
            query = "SELECT DISTINCT c.location FROM c WHERE c.location != null"
            locations = list(self.metadata_container.query_items(query=query))
            facets["locations"] = [{"value": l["location"], "count": 0} for l in locations]
            
            query = "SELECT DISTINCT c.marital_status FROM c WHERE c.marital_status != null"
            statuses = list(self.metadata_container.query_items(query=query))
            facets["marital_statuses"] = [{"value": s["marital_status"], "count": 0} 
                                         for s in statuses]
            
            facets["age_ranges"] = [
                {"label": "18-25", "min": 18, "max": 25},
                {"label": "26-35", "min": 26, "max": 35},
                {"label": "36-45", "min": 36, "max": 45},
                {"label": "46-55", "min": 46, "max": 55},
                {"label": "56-65", "min": 56, "max": 65},
                {"label": "65+", "min": 65, "max": 999}
            ]
            
            facets["income_ranges"] = [
                {"label": "< $50k", "min": 0, "max": 50000},
                {"label": "$50k-$75k", "min": 50000, "max": 75000},
                {"label": "$75k-$100k", "min": 75000, "max": 100000},
                {"label": "$100k-$150k", "min": 100000, "max": 150000},
                {"label": "$150k-$200k", "min": 150000, "max": 200000},
                {"label": "$200k+", "min": 200000, "max": 999999999}
            ]
            
        except Exception as e:
            print(f"Error getting facets: {e}")
        
        return facets
    
    def search_similar_twins(self, lead_id: str, top: int = 10) -> List[Dict[str, Any]]:
        if not self.metadata_container:
            return []
        
        try:
            query = "SELECT * FROM c WHERE c.id = @lead_id"
            parameters = [{"name": "@lead_id", "value": lead_id}]
            items = list(self.metadata_container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=1
            ))
            
            if not items:
                return []
            
            source_twin = items[0]
            
            filters = {}
            if source_twin.get('age'):
                filters['min_age'] = source_twin['age'] - 5
                filters['max_age'] = source_twin['age'] + 5
            
            if source_twin.get('income'):
                filters['min_income'] = source_twin['income'] * 0.8
                filters['max_income'] = source_twin['income'] * 1.2
            
            if source_twin.get('location'):
                filters['location'] = source_twin['location']
            
            results = self._fallback_search("", filters, top + 1)
            
            similar_twins = [r for r in results["results"] if r['id'] != lead_id][:top]
            
            return similar_twins
            
        except Exception as e:
            print(f"Error finding similar twins: {e}")
            return []