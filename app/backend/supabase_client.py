"""
Supabase Client - REST API Implementation (FIXED)
Uses direct HTTP calls to avoid library version conflicts
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# Validate configuration
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError(
        "Missing Supabase configuration. "
        "Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env file"
    )

class SupabaseClient:
    """Simple Supabase client using REST API"""
    
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_ANON_KEY
        self.auth_url = f"{self.url}/auth/v1"
        self.rest_url = f"{self.url}/rest/v1"
        
    def _get_headers(self, access_token=None):
        """Get headers for API requests"""
        headers = {
            'apikey': self.key,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'  # IMPORTANT: Return inserted data
        }
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        return headers
    
    # ==================== AUTH METHODS ====================
    
    def sign_up(self, email, password, user_metadata=None):
        """Sign up a new user"""
        try:
            response = requests.post(
                f"{self.auth_url}/signup",
                headers=self._get_headers(),
                json={
                    'email': email,
                    'password': password,
                    'data': user_metadata or {}
                }
            )
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                error_data = response.json()
                return {'success': False, 'error': error_data.get('msg', 'Signup failed')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sign_in(self, email, password):
        """Sign in existing user"""
        try:
            response = requests.post(
                f"{self.auth_url}/token?grant_type=password",
                headers=self._get_headers(),
                json={
                    'email': email,
                    'password': password
                }
            )
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                error_data = response.json()
                return {'success': False, 'error': error_data.get('error_description', 'Login failed')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sign_out(self, access_token):
        """Sign out user"""
        try:
            response = requests.post(
                f"{self.auth_url}/logout",
                headers=self._get_headers(access_token)
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user(self, access_token):
        """Get user from access token"""
        try:
            response = requests.get(
                f"{self.auth_url}/user",
                headers=self._get_headers(access_token)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    # ==================== DATABASE METHODS (FIXED) ====================
    
    def select(self, table, filters=None, access_token=None):
        """Query table"""
        try:
            url = f"{self.rest_url}/{table}?select=*"
            
            # Add filters as query params
            if filters:
                for k, v in filters.items():
                    url += f"&{k}=eq.{v}"
            
            response = requests.get(
                url,
                headers=self._get_headers(access_token)
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
        Insert row(s) into table
        FIXED: Properly handle both single object and array
        """
        try:
            # Ensure data is a list for bulk insert
            is_single = isinstance(data, dict)
            insert_data = [data] if is_single else data
            
            print(f"📤 Inserting {len(insert_data)} rows into {table}")
            
            response = requests.post(
                f"{self.rest_url}/{table}",
                headers=self._get_headers(access_token),
                json=insert_data
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                # Successfully inserted
                try:
                    result_data = response.json()
                    print(f"✅ Inserted {len(result_data)} rows")
                    return {'success': True, 'data': result_data}
                except Exception as json_error:
                    # If JSON parsing fails, still return success
                    print(f"⚠️ JSON parse error (but insert likely succeeded): {json_error}")
                    return {'success': True, 'data': insert_data}
            else:
                # Failed to insert
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
        """Update rows in table"""
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
                headers=self._get_headers(access_token),
                json=data
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Update error: {e}")
            return False
    
    def delete(self, table, filters, access_token=None):
        """Delete rows from table"""
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
                headers=self._get_headers(access_token)
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Delete error: {e}")
            return False

# Global client instance
supabase = SupabaseClient()

print(f"✅ Supabase REST client initialized: {SUPABASE_URL}")