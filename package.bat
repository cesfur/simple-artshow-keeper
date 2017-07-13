@if exist build rmdir /S /Q build
python setup.py bdist_wininst --install-script=postinstall.py --plat-name=win32