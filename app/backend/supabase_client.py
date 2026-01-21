"""
Supabase Client - REST API Implementation
Updated for Phone Authentication (NO Supabase Auth) + Storage Support
"""

import os
import requests
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY')

# Validate configuration
if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise ValueError(
        "Missing Supabase configuration. "
        "Please set SUPABASE_URL and SUPABASE_SECRET_KEY in .env file"
    )

class SupabaseClient:
    """Simple Supabase client using REST API - Phone Auth Compatible + Storage"""
    
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_SECRET_KEY
        self.rest_url = f"{self.url}/rest/v1"
        
    def _get_headers(self):
        """Get headers for API requests"""
        headers = {
            'apikey': self.key,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        return headers
    
    # ==================== DATABASE METHODS ====================
    
    def select(self, table, filters=None, access_token=None):
        """Query table (access_token ignored for backward compatibility)"""
        try:
            url = f"{self.rest_url}/{table}?select=*"
            
            # Add filters as query params
            if filters:
                for k, v in filters.items():
                    url += f"&{k}=eq.{v}"
            
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Select error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Select exception: {e}")
            return []
    
    def insert(self, table, data, access_token=None):
        """
        Insert row(s) into table (access_token ignored for backward compatibility)
        """
        try:
            # Ensure data is a list for bulk insert
            is_single = isinstance(data, dict)
            insert_data = [data] if is_single else data
            
            print(f"📤 Inserting {len(insert_data)} rows into {table}")
            
            response = requests.post(
                f"{self.rest_url}/{table}",
                headers=self._get_headers(),
                json=insert_data
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    result_data = response.json()
                    print(f"✅ Inserted {len(result_data)} rows")
                    return {'success': True, 'data': result_data}
                except Exception as json_error:
                    print(f"⚠️ JSON parse error: {json_error}")
                    return {'success': True, 'data': insert_data}
            else:
                error_text = response.text
                print(f"❌ Insert failed: {error_text}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_text)
                except:
                    error_msg = error_text
                
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            print(f"❌ Insert exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def update(self, table, filters, data, access_token=None):
        """Update rows in table (access_token ignored for backward compatibility)"""
        try:
            url = f"{self.rest_url}/{table}"
            
            # Add filters
            if filters:
                params = []
                for k, v in filters.items():
                    params.append(f"{k}=eq.{v}")
                url += "?" + "&".join(params)
            
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=data
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Update error: {e}")
            return False
    
    def delete(self, table, filters, access_token=None):
        """Delete rows from table (access_token ignored for backward compatibility)"""
        try:
            url = f"{self.rest_url}/{table}"
            
            # Add filters
            if filters:
                params = []
                for k, v in filters.items():
                    params.append(f"{k}=eq.{v}")
                url += "?" + "&".join(params)
            
            response = requests.delete(
                url,
                headers=self._get_headers()
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Delete error: {e}")
            return False
    
    def count(self, table, filters=None, access_token=None):
        """Get count of rows (access_token ignored for backward compatibility)"""
        try:
            url = f"{self.rest_url}/{table}?select=id"
            
            # Add filters
            if filters:
                for k, v in filters.items():
                    url += f"&{k}=eq.{v}"
            
            # Request with count header
            headers = self._get_headers()
            headers['Prefer'] = 'count=exact'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Try to get count from Content-Range header
                content_range = response.headers.get('Content-Range', '')
                
                if '/' in content_range:
                    total = int(content_range.split('/')[-1])
                    return total
                
                # Fallback: count returned data
                data = response.json()
                return len(data)
            
            return 0
            
        except Exception as e:
            print(f"Count error: {str(e)}")
            return 0
    
    # ==================== STORAGE METHODS ====================
    
    def upload_file(
        self,
        bucket: str,
        path: str,
        content: str,
        content_type: str = 'text/plain'
    ) -> bool:
        """
        Upload file to Supabase Storage
        
        Args:
            bucket: Bucket name (e.g., 'episodic-memory')
            path: File path in bucket (e.g., 'users/uuid/2026/01/file.md')
            content: File content (string)
            content_type: MIME type (default: text/plain)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encode content as bytes
            content_bytes = content.encode('utf-8')
            
            # Build upload URL
            url = f"{self.url}/storage/v1/object/{bucket}/{path}"
            
            # Upload with upsert (overwrite if exists)
            headers = {
                'apikey': self.key,
                'Authorization': f'Bearer {self.key}',
                'x-upsert': 'true'  # Allow overwriting
            }
            
            response = requests.post(
                url,
                headers=headers,
                files={'file': (path.split('/')[-1], content_bytes, content_type)}
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ File uploaded: {path}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def download_file(
        self,
        bucket: str,
        path: str
    ) -> Optional[str]:
        """
        Download file from Supabase Storage
        
        Args:
            bucket: Bucket name
            path: File path in bucket
        
        Returns:
            File content as string, or None if failed
        """
        try:
            # Build download URL
            url = f"{self.url}/storage/v1/object/{bucket}/{path}"
            
            headers = {
                'apikey': self.key,
                'Authorization': f'Bearer {self.key}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"❌ Download failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Download exception: {e}")
            return None
    
    def list_files(
        self,
        bucket: str,
        path: str = '',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List files in a bucket path
        
        Args:
            bucket: Bucket name
            path: Folder path (e.g., 'users/abc-123/2026/01')
            limit: Max files to return
        
        Returns:
            List of file objects with 'name', 'id', 'created_at', etc.
        """
        try:
            # Build list URL
            url = f"{self.url}/storage/v1/object/list/{bucket}"
            
            headers = {
                'apikey': self.key,
                'Authorization': f'Bearer {self.key}',
                'Content-Type': 'application/json'
            }
            
            # Query params
            params = {
                'prefix': path,
                'limit': limit,
                'offset': 0,
                'sortBy': {'column': 'created_at', 'order': 'desc'}
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ List failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ List exception: {e}")
            return []
    
    def delete_file(
        self,
        bucket: str,
        path: str
    ) -> bool:
        """
        Delete file from Supabase Storage
        
        Args:
            bucket: Bucket name
            path: File path in bucket
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.url}/storage/v1/object/{bucket}/{path}"
            
            headers = {
                'apikey': self.key,
                'Authorization': f'Bearer {self.key}'
            }
            
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ File deleted: {path}")
                return True
            else:
                print(f"❌ Delete failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Delete exception: {e}")
            return False


# Global client instance
supabase = SupabaseClient()

print(f"✅ Supabase REST client initialized: {SUPABASE_URL}")