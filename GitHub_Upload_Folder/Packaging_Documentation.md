# Packaging the Medication Lookup Application

## Introduction

The Medication Lookup application was successfully packaged into a standalone, distributable Windows Installer (`Setup.exe`). This documentation outlines the reasoning behind the deployment strategy and the technical steps taken to achieve it.

## The "Why": Deployment Strategy

### Bypassing the ZIP File Trap

When distributing software to non-technical users, relying on ZIP archives or raw folders often leads to confusion. Users frequently attempt to run an executable file from directly within a compressed ZIP archive without extracting it first. This causes the application to crash immediately because it cannot access its neighboring dependency files. A standard Windows installer prevents this by enforcing proper extraction and placement of the files.

### Handling External Data Dependencies

The Medication Lookup app is not just a single script; it relies heavily on external local files: 1. **SQLite Database (`med_lookup.db`)**: Used to store indexed documentation logic. 2. **Storage Directory (`storage/`)**: Contains critical Excel spreadsheets (like the NHS Drug Tariff List) necessary for offline lookups.

If a user were to download a simple, standalone `.exe` without these accompanying files, the app would fail to function. The installer ensures these files are perfectly bundled together.

### Preventing Administrator Write-Permission Errors

Many modern Windows applications default to installing inside `C:\Program Files\`. However, standard user accounts do not have permission to write or edit files inside this directory. Because our application occasionally interacts with the local `med_lookup.db` file, installing it here would trigger "Permission Denied" crashes. To solve this, the installer places the app directly into the user's `LocalAppData` directory, guaranteeing full read and write access without triggering UAC Admin prompts.

## The "How": Technical Implementation

The packaging process was completed in two distinct technical phases:

### Step 1: Compiling the Environment (PyInstaller)

We utilized **PyInstaller** to compile the raw Python scripts into executable machine code. \* Rather than compiling into a single monolithic `.exe`, we compiled it into a **One-Folder** build. \* We explicitly instructed PyInstaller to bundle the `med_lookup.db` database and the `storage/` directory alongside the generated `.exe`. \* This created a localized, self-sufficient "distributable folder" containing all necessary logic and data.

### Step 2: Generating the Setup Wizard (Inno Setup)

To convert the distributable folder into a user-friendly installer, we employed **Inno Setup**. \* We wrote an Inno Setup script (`installer_config.iss`) that targets the PyInstaller folder. \* The script compresses all the internal libraries, databases, and spreadsheets into a single `Install_MedicationLookup.exe` file. \* It is configured to silently install the application into `{localappdata}\MedicationLookup`. \* Finally, it automatically generates a Start Menu entry and places a shortcut on the user's Desktop.