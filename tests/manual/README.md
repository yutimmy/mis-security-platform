Manual diagnostic scripts that were previously part of the automated test suite now live here.
They rely on external services, long running workflows, or verbose console output and are not
executed by pytest. Run them directly with `python path/to/script.py` when manual verification is
needed.
