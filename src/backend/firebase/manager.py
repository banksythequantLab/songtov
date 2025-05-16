"""
MaiVid Studio - Firebase integration module

This module handles the communication with Firebase services,
including authentication, database, storage, and functions.

Classes:
    FirebaseManager: Manages Firebase services
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try importing Firebase packages, but provide fallbacks if not available
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    logger.warning("Firebase packages not available. Using mock implementations.")
    FIREBASE_AVAILABLE = False


class FirebaseManager:
    """Manager for Firebase services."""
    
    def __init__(self, 
                 credentials_path: Optional[str] = None, 
                 storage_bucket: Optional[str] = None,
                 project_id: Optional[str] = None):
        """
        Initialize the Firebase manager.
        
        Args:
            credentials_path (str): Path to the Firebase service account credentials JSON file
            storage_bucket (str): Name of the Firebase storage bucket
            project_id (str): Firebase project ID
        """
        self.initialized = False
        self.db = None
        self.bucket = None
        self.auth = None
        
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase packages not available. Using mock implementation.")
            return
        
        try:
            # Initialize Firebase Admin SDK if not already initialized
            if not firebase_admin._apps:
                if credentials_path:
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': storage_bucket,
                        'projectId': project_id
                    })
                else:
                    firebase_admin.initialize_app()
                
            # Initialize Firestore
            self.db = firestore.client()
            
            # Initialize Storage
            if storage_bucket:
                self.bucket = storage.bucket()
            
            # Initialize Auth
            self.auth = auth
            
            self.initialized = True
            logger.info("Firebase services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
    
    def is_initialized(self) -> bool:
        """
        Check if Firebase has been initialized.
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self.initialized
    
    def get_document(self, collection: str, document_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get a document from Firestore.
        
        Args:
            collection (str): Collection name
            document_id (str): Document ID
            
        Returns:
            Tuple: (document_data, error_message)
        """
        if not self.initialized:
            return None, "Firebase not initialized"
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict(), None
            else:
                logger.warning(f"Document {collection}/{document_id} not found")
                return None, f"Document {collection}/{document_id} not found"
                
        except Exception as e:
            error_msg = f"Failed to get document {collection}/{document_id}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def set_document(self, 
                    collection: str, 
                    document_id: str, 
                    data: Dict[str, Any], 
                    merge: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Set a document in Firestore.
        
        Args:
            collection (str): Collection name
            document_id (str): Document ID
            data (Dict): Document data
            merge (bool): Whether to merge with existing data
            
        Returns:
            Tuple: (success, error_message)
        """
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data, merge=merge)
            logger.info(f"Document {collection}/{document_id} set successfully")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to set document {collection}/{document_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def update_document(self, 
                       collection: str, 
                       document_id: str, 
                       data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Update a document in Firestore.
        
        Args:
            collection (str): Collection name
            document_id (str): Document ID
            data (Dict): Document data to update
            
        Returns:
            Tuple: (success, error_message)
        """
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.update(data)
            logger.info(f"Document {collection}/{document_id} updated successfully")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to update document {collection}/{document_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_document(self, 
                        collection: str, 
                        document_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a document from Firestore.
        
        Args:
            collection (str): Collection name
            document_id (str): Document ID
            
        Returns:
            Tuple: (success, error_message)
        """
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.delete()
            logger.info(f"Document {collection}/{document_id} deleted successfully")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to delete document {collection}/{document_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def query_collection(self, 
                         collection: str, 
                         field: str, 
                         operator: str, 
                         value: Any,
                         limit: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Query documents in a collection.
        
        Args:
            collection (str): Collection name
            field (str): Field to query
            operator (str): Comparison operator (==, >, <, >=, <=, array_contains)
            value (Any): Value to compare against
            limit (int): Maximum number of documents to return
            
        Returns:
            Tuple: (document_list, error_message)
        """
        if not self.initialized:
            return [], "Firebase not initialized"
        
        try:
            query = self.db.collection(collection).where(field, operator, value)
            
            if limit:
                query = query.limit(limit)
                
            docs = query.stream()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
                
            logger.info(f"Query returned {len(results)} documents")
            return results, None
            
        except Exception as e:
            error_msg = f"Failed to query collection {collection}: {str(e)}"
            logger.error(error_msg)
            return [], error_msg
    
    def upload_file(self, 
                   local_file_path: str, 
                   destination_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload a file to Firebase Storage.
        
        Args:
            local_file_path (str): Path to the local file
            destination_path (str): Path in Firebase Storage
            
        Returns:
            Tuple: (download_url, error_message)
        """
        if not self.initialized or not self.bucket:
            return None, "Firebase Storage not initialized"
        
        try:
            # Check if local file exists
            if not os.path.exists(local_file_path):
                return None, f"Local file {local_file_path} not found"
                
            # Upload the file
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(local_file_path)
            
            # Make the file publicly accessible and get the URL
            blob.make_public()
            download_url = blob.public_url
            
            logger.info(f"File uploaded to {destination_path}, URL: {download_url}")
            return download_url, None
            
        except Exception as e:
            error_msg = f"Failed to upload file {local_file_path}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def download_file(self, 
                      storage_path: str, 
                      local_file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Download a file from Firebase Storage.
        
        Args:
            storage_path (str): Path in Firebase Storage
            local_file_path (str): Path to save the file locally
            
        Returns:
            Tuple: (success, error_message)
        """
        if not self.initialized or not self.bucket:
            return False, "Firebase Storage not initialized"
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            # Download the file
            blob = self.bucket.blob(storage_path)
            blob.download_to_filename(local_file_path)
            
            logger.info(f"File downloaded from {storage_path} to {local_file_path}")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to download file {storage_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_user(self, 
                   email: str, 
                   password: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a new user in Firebase Authentication.
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            Tuple: (user_id, error_message)
        """
        if not self.initialized or not self.auth:
            return None, "Firebase Authentication not initialized"
        
        try:
            user = self.auth.create_user(
                email=email,
                password=password
            )
            
            logger.info(f"User created with ID: {user.uid}")
            return user.uid, None
            
        except Exception as e:
            error_msg = f"Failed to create user {email}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_user(self, user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get a user from Firebase Authentication.
        
        Args:
            user_id (str): User ID
            
        Returns:
            Tuple: (user_data, error_message)
        """
        if not self.initialized or not self.auth:
            return None, "Firebase Authentication not initialized"
        
        try:
            user = self.auth.get_user(user_id)
            
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'disabled': user.disabled,
                'email_verified': user.email_verified,
                'created_at': user.user_metadata.creation_timestamp
            }
            
            logger.info(f"Retrieved user {user_id}")
            return user_data, None
            
        except Exception as e:
            error_msg = f"Failed to get user {user_id}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
            
    def verify_id_token(self, id_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify a Firebase ID token.
        
        Args:
            id_token (str): The Firebase ID token to verify
            
        Returns:
            Tuple: (user_data, error_message)
        """
        if not self.initialized or not self.auth:
            return None, "Firebase Authentication not initialized"
        
        try:
            # Verify the token
            decoded_token = self.auth.verify_id_token(id_token)
            
            # Get the user's data
            user = self.auth.get_user(decoded_token['uid'])
            
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'email_verified': user.email_verified
            }
            
            logger.info(f"Verified token for user {user.uid}")
            return user_data, None
            
        except Exception as e:
            error_msg = f"Failed to verify token: {str(e)}"
            logger.error(error_msg)
            return None, error_msg


# Example usage
if __name__ == "__main__":
    # Path to Firebase service account credentials
    credentials_path = "firebase/service-account.json"
    
    # Initialize Firebase manager
    firebase = FirebaseManager(
        credentials_path=credentials_path,
        storage_bucket="maivid-studio.appspot.com",
        project_id="maivid-studio"
    )
    
    if firebase.is_initialized():
        # Example Firestore operations
        success, error = firebase.set_document(
            collection="projects",
            document_id="test-project",
            data={
                "name": "Test Project",
                "created_at": firestore.SERVER_TIMESTAMP,
                "user_id": "test-user"
            }
        )
        
        if success:
            print("Document created successfully")
        else:
            print(f"Failed to create document: {error}")
            
        # Example Storage operations
        if os.path.exists("test.jpg"):
            url, error = firebase.upload_file(
                local_file_path="test.jpg",
                destination_path="projects/test-project/test.jpg"
            )
            
            if url:
                print(f"File uploaded successfully: {url}")
            else:
                print(f"Failed to upload file: {error}")
    else:
        print("Firebase not initialized. Check credentials and dependencies.")