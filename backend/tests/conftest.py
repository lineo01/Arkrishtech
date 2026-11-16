import os, sys, tempfile
os.environ["KS_OFFLINE"] = "1"; os.environ["KS_DB"] = os.path.join(tempfile.mkdtemp(), "test.db"); os.environ["KS_CACHE"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
