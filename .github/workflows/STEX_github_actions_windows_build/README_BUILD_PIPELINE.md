# STEX GitHub Actions Windows Build

This adds an automatic Windows build pipeline.

## What it does

Every time code is pushed to `main`, GitHub will:

1. Start a Windows build computer.
2. Install Python.
3. Install STEX dependencies.
4. Use PyInstaller to build `STEX.exe`.
5. Upload a downloadable artifact named:

```text
STEX-Windows-Build
```

## Where this file goes

Upload this file to your repo at:

```text
.github/workflows/windows-build.yml
```

## How to download the EXE after it builds

1. Open your GitHub repo.
2. Click the **Actions** tab.
3. Click the latest workflow run: **Build Windows STEX**.
4. Scroll to **Artifacts**.
5. Download **STEX-Windows-Build**.
6. Unzip it.
7. Double-click **STEX.exe**.
