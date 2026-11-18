# -*- mode: python ; coding: utf-8 -*-

import sys
import os

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Módulo local
        'config',
        
        # Pandas e suas dependências
        'pandas',
        'pandas._libs',
        'pandas._libs.tslibs',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.offsets',
        'pandas._libs.writers',
        'pandas._libs.parsers',
        'pandas.io.excel',
        'pandas.io.excel._base',
        'pandas.io.excel._openpyxl',
        'pandas.io.excel._xlrd',
        'pandas.io.common',
        'pandas.io.formats',
        'pandas.io.formats.excel',
        'pandas.io.formats.format',
        'pandas.io.formats.printing',
        
        # OpenPyXL
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell._writer',
        'openpyxl.workbook',
        'openpyxl.workbook.external_link',
        'openpyxl.workbook.external_link.external',
        'openpyxl.worksheet',
        'openpyxl.worksheet._reader',
        'openpyxl.worksheet._writer',
        'openpyxl.styles',
        'openpyxl.styles.fills',
        'openpyxl.styles.fonts',
        'openpyxl.styles.numbers',
        'openpyxl.utils',
        'openpyxl.utils.datetime',
        'openpyxl.utils.exceptions',
        'openpyxl.xml',
        'openpyxl.xml.constants',
        'openpyxl.xml.functions',
        
        # Requests e suas dependências
        'requests',
        'requests.packages',
        'requests.packages.urllib3',
        'urllib3',
        'urllib3.util',
        'urllib3.util.retry',
        'urllib3.util.ssl_',
        'urllib3.poolmanager',
        'urllib3.contrib',
        'urllib3.contrib.pyopenssl',
        'certifi',
        'charset_normalizer',
        'idna',
        
        # xlrd (usado pelo pandas para ler .xls)
        'xlrd',
        'xlrd.biffh',
        'xlrd.compdoc',
        'xlrd.formatting',
        'xlrd.sheet',
        'xlrd.xldate',
        
        # Outros módulos que podem ser necessários
        'pkg_resources',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Garantir que o Python DLL seja incluído
python_dll_name = f'python{sys.version_info.major}{sys.version_info.minor}.dll'
# Tentar vários locais possíveis para o Python DLL
possible_dll_paths = [
    os.path.join(sys.base_prefix, 'python_dll', python_dll_name),
    os.path.join(sys.exec_prefix, 'python_dll', python_dll_name),
    os.path.join(sys.base_prefix, 'DLLs', python_dll_name),
    os.path.join(sys.exec_prefix, 'DLLs', python_dll_name),
    os.path.join(os.path.dirname(sys.executable), python_dll_name),
    os.path.join(os.path.dirname(sys.executable), 'python_dll', python_dll_name),
]

python_dll_path = None
for path in possible_dll_paths:
    if os.path.exists(path):
        python_dll_path = path
        break

if python_dll_path:
    a.binaries += [(python_dll_name, python_dll_path, 'BINARY')]
    print(f'Python DLL encontrado: {python_dll_path}')
else:
    print(f'AVISO: Python DLL não encontrado em locais padrão. Nome esperado: {python_dll_name}')

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Desabilitar UPX para evitar problemas com DLLs
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
