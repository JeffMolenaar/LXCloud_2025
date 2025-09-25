import importlib, sys
sys.path.insert(0, 'project')
try:
    m = importlib.import_module('app')
    app = m.create_app()
    print('CREATE_APP_OK')
except Exception:
    import traceback
    traceback.print_exc()
    print('CREATE_APP_FAIL')
    raise
