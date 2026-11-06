import os
import tempfile

# Test-iin DB: DB-iin module import hiigdeh omno tohirulna.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
<<<<<<< HEAD
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long")
=======
os.environ.setdefault("SECRET_KEY", "test-secret")
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
