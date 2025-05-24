"""
Patch for passlib to work with bcrypt 4.0.0+
This fixes the warning: "error reading bcrypt version"
"""
import logging
import warnings

# Apply warning filters immediately when this module is imported
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")

def patch_passlib_bcrypt():
    """
    Apply a patch to make passlib work with bcrypt 4.0.0+
    """
    try:
        # Set up logging filter for passlib bcrypt warnings
        class BcryptWarningFilter(logging.Filter):
            def filter(self, record):
                return not ("error reading bcrypt version" in record.getMessage() or
                           "trapped" in record.getMessage())

        # Apply the filter to the passlib.handlers.bcrypt logger
        bcrypt_logger = logging.getLogger('passlib.handlers.bcrypt')
        bcrypt_logger.addFilter(BcryptWarningFilter())

        # Also apply to root logger to catch any other bcrypt warnings
        root_logger = logging.getLogger()
        root_logger.addFilter(BcryptWarningFilter())

        # Pre-patch bcrypt module before passlib tries to use it
        import bcrypt as bcrypt_lib

        # Create the __about__ attribute if it doesn't exist
        if not hasattr(bcrypt_lib, "__about__"):
            class MockAbout:
                def __init__(self):
                    if hasattr(bcrypt_lib, "__version__"):
                        self.__version__ = bcrypt_lib.__version__
                    else:
                        self.__version__ = "4.0.1"

            bcrypt_lib.__about__ = MockAbout()

        # Now import passlib after patching bcrypt
        from passlib.handlers import bcrypt as passlib_bcrypt

        # Additional patching for the _bcrypt backend
        if hasattr(passlib_bcrypt, "_bcrypt"):
            _bcrypt = passlib_bcrypt._bcrypt
            if not hasattr(_bcrypt, "__about__"):
                _bcrypt.__about__ = bcrypt_lib.__about__

        logging.info(f"Successfully patched bcrypt compatibility (version: {bcrypt_lib.__about__.__version__})")

    except Exception as e:
        # Fallback: ensure warnings are suppressed
        warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
        warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")

        # Set up a simple logging filter as fallback
        class SimpleFilter(logging.Filter):
            def filter(self, record):
                return "bcrypt version" not in record.getMessage()

        logging.getLogger().addFilter(SimpleFilter())
