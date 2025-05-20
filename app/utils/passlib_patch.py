"""
Patch for passlib to work with bcrypt 4.0.0+
This fixes the warning: "error reading bcrypt version"
"""
import logging
import warnings
from importlib import import_module

# Suppress the specific warning from passlib
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

def patch_passlib_bcrypt():
    """
    Apply a patch to make passlib work with bcrypt 4.0.0+
    """
    try:
        # Try to import the problematic module
        from passlib.handlers import bcrypt

        # Check if _bcrypt is already patched
        if hasattr(bcrypt, "_bcrypt") and not hasattr(bcrypt._bcrypt, "__about__"):
            # Create a mock __about__ module with a __version__ attribute
            class MockAbout:
                __version__ = "4.0.1"  # Use a default version
            
            # Try to get the actual version if possible
            try:
                import bcrypt as bcrypt_lib
                if hasattr(bcrypt_lib, "__version__"):
                    MockAbout.__version__ = bcrypt_lib.__version__
            except (ImportError, AttributeError):
                pass
            
            # Patch the _bcrypt module
            bcrypt._bcrypt.__about__ = MockAbout
            
            logging.info("Successfully patched passlib.handlers.bcrypt for compatibility with bcrypt 4.0.0+")
    except (ImportError, AttributeError) as e:
        logging.warning(f"Failed to patch passlib.handlers.bcrypt: {e}")
