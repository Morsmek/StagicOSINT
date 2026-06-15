# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for SDBA — Stagic Data Breach Alert
#
# Run from the /backend folder:
#   py -m PyInstaller SDBA.spec --clean --noconfirm

import os
from pathlib import Path

ROOT    = Path(SPECPATH)                     # …/backend
FRONTEND_DIST = ROOT.parent / "frontend" / "dist"

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle the built React UI so the exe can serve it
        (str(FRONTEND_DIST), 'frontend_dist'),
    ],
    hiddenimports=[
        # FastAPI / Starlette internals that PyInstaller misses
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.staticfiles',
        'starlette.responses',
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        # Uvicorn
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # Pydantic / pydantic-settings
        'pydantic',
        'pydantic_settings',
        'pydantic.v1',
        # aiosqlite
        'aiosqlite',
        # Local modules
        'config',
        'database',
        'models',
        'graph_engine',
        'transform_engine',
        'routers',
        'routers.graphs',
        'routers.entities',
        'routers.transforms',
        'routers.api_keys',
        'transforms',
        'transforms.base',
        'transforms.dns',
        'transforms.ip',
        'transforms.ssl',
        'transforms.email',
        'transforms.hash',
        'transforms.web',
        'transforms.social',
        # SDBA modules
        'sdba',
        'sdba.db',
        'sdba.intel',
        'sdba.router',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'numpy', 'PIL',
        'PyQt5', 'PyQt6', 'wx', 'gtk',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SDBA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # keep True so the user can see the startup URL / errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # add a .ico path here if you have one
)
