"""
Secret Chamber Security Module
Implements encryption, authentication, and anonymity for admin polling
"""
import hashlib
import hmac
import secrets
import json
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SecretChamberSecurity:
    """Security utilities for the Secret Chamber system"""
    
    def __init__(self):
        # Generate or use configured encryption key
        self.encryption_key = getattr(settings, 'SECRET_CHAMBER_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.encryption_key)
    
    def verify_superuser_access(self, user):
        """Verify user has superuser access to Secret Chamber"""
        if not user.is_authenticated:
            logger.warning(f"Unauthenticated access attempt to Secret Chamber")
            raise PermissionDenied("Authentication required")
        
        if not user.is_superuser:
            logger.warning(f"Non-superuser access attempt by {user.username}")
            raise PermissionDenied("Superuser access required")
        
        return True
    
    def generate_anonymous_token(self, user_id, poll_id, salt=None):
        """
        Generate cryptographic token for anonymous voting
        Links to user for eligibility but not for vote content
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Create hash that verifies user eligibility without revealing identity
        token_data = f"{user_id}:{poll_id}:{timezone.now().date()}"
        token_hash = hmac.new(
            salt,
            token_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combine salt and hash for verification
        anonymous_token = f"{salt.hex()}:{token_hash}"
        
        logger.info(f"Generated anonymous token for poll {poll_id}")
        return anonymous_token
    
    def verify_anonymous_token(self, token, user_id, poll_id):
        """Verify anonymous token without revealing voter identity"""
        try:
            salt_hex, token_hash = token.split(':', 1)
            salt = bytes.fromhex(salt_hex)
            
            # Recreate expected hash
            token_data = f"{user_id}:{poll_id}:{timezone.now().date()}"
            expected_hash = hmac.new(
                salt,
                token_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Verify token matches
            is_valid = hmac.compare_digest(token_hash, expected_hash)
            
            if is_valid:
                logger.info(f"Valid anonymous token verified for poll {poll_id}")
            else:
                logger.warning(f"Invalid anonymous token for poll {poll_id}")
            
            return is_valid
            
        except (ValueError, TypeError) as e:
            logger.error(f"Token verification error: {e}")
            return False
    
    def encrypt_vote_data(self, vote_data):
        """Encrypt vote content for secure storage"""
        if isinstance(vote_data, dict):
            vote_data = json.dumps(vote_data)
        
        encrypted_data = self.cipher.encrypt(vote_data.encode('utf-8'))
        return encrypted_data.decode('utf-8')
    
    def decrypt_vote_data(self, encrypted_data):
        """Decrypt vote content for analysis"""
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            decrypted_data = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data
                
        except Exception as e:
            logger.error(f"Vote data decryption error: {e}")
            return None
    
    def generate_vote_verification_hash(self, vote_token, encrypted_vote_data):
        """Generate verification hash for vote integrity"""
        verification_data = f"{vote_token}:{encrypted_vote_data}:{timezone.now().isoformat()}"
        verification_hash = hashlib.sha256(verification_data.encode('utf-8')).hexdigest()
        return verification_hash
    
    def verify_vote_integrity(self, vote_token, encrypted_vote_data, verification_hash):
        """Verify vote hasn't been tampered with"""
        # Note: This is simplified - in production, you'd want more sophisticated integrity checking
        expected_hash = self.generate_vote_verification_hash(vote_token, encrypted_vote_data)
        return hmac.compare_digest(verification_hash, expected_hash)
    
    def log_chamber_access(self, user, action, details=None):
        """Log chamber access for security audit"""
        log_data = {
            'user': user.username,
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        logger.info(f"Chamber Access: {json.dumps(log_data)}")


class ChamberPermissions:
    """Permission utilities for Secret Chamber"""
    
    @staticmethod
    def user_can_access_chamber(user):
        """Check if user can access Secret Chamber"""
        return user.is_authenticated and user.is_superuser
    
    @staticmethod
    def user_can_create_poll(user):
        """Check if user can create polls"""
        return user.is_authenticated and user.is_superuser
    
    @staticmethod
    def user_can_vote_in_poll(user, poll=None):
        """Check if user can vote in a specific poll"""
        if not (user.is_authenticated and user.is_superuser):
            return False
        
        if poll:
            # Check if poll is active
            now = timezone.now()
            return poll.is_active and poll.start_date <= now <= poll.end_date
        
        return True
    
    @staticmethod
    def user_can_view_results(user, poll=None):
        """Check if user can view poll results"""
        if not (user.is_authenticated and user.is_superuser):
            return False
        
        if poll:
            # Check poll's results visibility settings
            if poll.results_public:
                return True
            
            # Allow viewing after poll ends
            return timezone.now() > poll.end_date
        
        return True


# Global security instance
chamber_security = SecretChamberSecurity()