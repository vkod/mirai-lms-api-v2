import os
from typing import Optional, Dict, Any, Tuple
from PIL import Image
import io
from azure.storage.blob import ContentSettings
from storage.azure_config import azure_config

class PersonaImageStorage:
    def __init__(self):
        self.blob_container = azure_config.get_blob_container_client("persona-images")
        self.local_fallback_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                               "agent_dojo", "persona_photographs")
        
        if not os.path.exists(self.local_fallback_dir):
            os.makedirs(self.local_fallback_dir)
    
    def _get_image_paths(self, lead_id: str) -> Dict[str, str]:
        return {
            "thumbnail": f"{lead_id}/thumbnail.jpeg",
            "medium": f"{lead_id}/medium.jpeg",
            "full": f"{lead_id}/full.jpeg",
            "icon": f"{lead_id}/icon.jpeg"
        }
    
    def _resize_image(self, image_bytes: bytes, size: Tuple[int, int]) -> bytes:
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', optimize=True)
        return output.getvalue()
    
    async def save_persona_image(self, lead_id: str, image_bytes: bytes) -> Dict[str, str]:
        paths = self._get_image_paths(lead_id)
        urls = {}
        
        sizes = {
            "icon": (64, 64),
            "thumbnail": (150, 150),
            "medium": (400, 400),
            "full": None
        }
        
        for size_name, size in sizes.items():
            if size:
                resized_bytes = self._resize_image(image_bytes, size)
            else:
                resized_bytes = image_bytes
            
            if self.blob_container:
                blob_path = paths[size_name]
                blob_client = self.blob_container.get_blob_client(blob_path)
                blob_client.upload_blob(
                    resized_bytes, 
                    overwrite=True,
                    content_settings=ContentSettings(content_type="image/jpeg")
                )
                urls[size_name] = blob_client.url
            
            #local_path = os.path.join(self.local_fallback_dir, f"{lead_id}_{size_name}.jpeg")
            #with open(local_path, 'wb') as f:
            #    f.write(resized_bytes)
            
            if not self.blob_container:
                urls[size_name] = f"/persona_image_{size_name}/{lead_id}"
        
        return urls
    
    async def get_persona_image(self, lead_id: str, size: str = "full") -> Optional[bytes]:
        size_map = {
            "icon": "icon",
            "thumbnail": "thumbnail",
            "medium": "medium",
            "full": "full"
        }
        
        if size not in size_map:
            size = "full"
        
        paths = self._get_image_paths(lead_id)
        blob_path = paths.get(size_map[size])
        
        if self.blob_container and blob_path:
            try:
                blob_client = self.blob_container.get_blob_client(blob_path)
                return blob_client.download_blob().readall()
            except Exception:
                pass

        local_filename = f"{lead_id}_{size_map[size]}.jpeg"
        if size_map[size] == "full":
            local_filename = f"{lead_id}.jpeg"

        local_path = os.path.join(self.local_fallback_dir, local_filename)
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                return f.read()
        
        return None
    
    async def delete_persona_images(self, lead_id: str) -> bool:
        paths = self._get_image_paths(lead_id)
        deleted = False
        
        if self.blob_container:
            for blob_path in paths.values():
                try:
                    blob_client = self.blob_container.get_blob_client(blob_path)
                    blob_client.delete_blob()
                    deleted = True
                except Exception:
                    pass
        
        for size_name in ["icon", "thumbnail", "medium", "full"]:
            local_filename = f"{lead_id}_{size_name}.jpeg"
            if size_name == "full":
                local_filename = f"{lead_id}.jpeg"
            
            local_path = os.path.join(self.local_fallback_dir, local_filename)
            if os.path.exists(local_path):
                os.remove(local_path)
                deleted = True
        
        return deleted
    
    async def image_exists(self, lead_id: str) -> bool:
        paths = self._get_image_paths(lead_id)
        
        if self.blob_container:
            try:
                blob_client = self.blob_container.get_blob_client(paths["full"])
                blob_client.get_blob_properties()
                return True
            except Exception:
                pass

        local_path = os.path.join(self.local_fallback_dir, f"{lead_id}.jpeg")
        return os.path.exists(local_path)
    
    async def list_persona_images(self, prefix: Optional[str] = None) -> list:
        images = []
        
        if self.blob_container:
            try:
                blobs = self.blob_container.list_blobs(name_starts_with=prefix)
                for blob in blobs:
                    if blob.name.endswith('/full.jpeg'):
                        lead_id = blob.name.split('/')[0]
                        images.append({
                            "lead_id": lead_id,
                            "blob_name": blob.name,
                            "size": blob.size,
                            "last_modified": blob.last_modified.isoformat() if blob.last_modified else None
                        })
            except Exception as e:
                print(f"Error listing blobs: {e}")
        
        if not images and os.path.exists(self.local_fallback_dir):
            for filename in os.listdir(self.local_fallback_dir):
                if filename.endswith('.jpeg') and not any(x in filename for x in ['_icon', '_thumbnail', '_medium']):
                    lead_id = filename.replace('.jpeg', '')
                    file_path = os.path.join(self.local_fallback_dir, filename)
                    images.append({
                        "lead_id": lead_id,
                        "local_path": file_path,
                        "size": os.path.getsize(file_path)
                    })
        
        return images