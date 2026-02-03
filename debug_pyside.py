import PySide6, site
print('PySide6 file:', getattr(PySide6, '__file__', None))
try:
    print('PySide6 path:', list(PySide6.__path__))
except Exception as e:
    print('no __path__:', e)
print('site-packages dirs:')
for d in site.getsitepackages():
    print(d)
