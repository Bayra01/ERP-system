import os
import tempfile

# Test-iin DB: DB-iin module import hiigdeh omno tohirulna.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ.setdefault("SECRET_KEY", "test-secret")
