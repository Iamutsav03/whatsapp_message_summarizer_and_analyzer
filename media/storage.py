import os
import shutil
import zipfile
import uuid
from config.media_settings import TEMP_MEDIA_DIR, MAX_UPLOAD_SIZE_MB

def _is_safe_path(basedir, path, follow_symlinks=True):
    """Protects against Zip Slip vulnerability."""
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path.abspath(path)
    return basedir == os.path.commonpath((basedir, matchpath))

def clear_session_storage(session_id: str):
    """Safely removes the ephemeral directory for a given session."""
    if not session_id:
        return
    session_dir = os.path.join(TEMP_MEDIA_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)

def create_session_storage() -> str:
    """Creates a new unique ephemeral directory for the upload."""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_MEDIA_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_id

def extract_zip_safely(zip_path: str, session_id: str) -> str:
    """
    Extracts a ZIP file securely to the session directory.
    Rejects unsafe paths (Zip Slip) and system files.
    """
    session_dir = os.path.join(TEMP_MEDIA_DIR, session_id)
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # Skip hidden/system files (e.g. __MACOSX)
            if member.filename.startswith('__MACOSX') or member.filename.startswith('.'):
                continue
                
            member_path = os.path.join(session_dir, member.filename)
            if not _is_safe_path(session_dir, member_path):
                print(f"WARNING: Skipping unsafe file extraction: {member.filename}")
                continue
                
            zf.extract(member, session_dir)
            
    return session_dir
