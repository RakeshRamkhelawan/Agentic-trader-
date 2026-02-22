# VedAstro Libraries

## Status
De VedAstro DLLs zijn nog niet beschikbaar. De broncode heeft compile errors die eerst moeten worden opgelost.

## Tijdelijke Oplossing
Het systeem gebruikt nu **HTTP fallback mode** met mock data voor VedAstro berekeningen.

## Echte DLLs Bouwen

### Optie 1: Fix VedAstro Broncode
```bash
cd C:\Users\rsram\OneDrive\Documenten\GitHub\VedAstro

# De errors zijn in Library/Logic/Calculate/Muhurtha.cs
# De Calculate class mist methoden die worden aangeroepen

# Tijdelijke fix: comment out de problematische regels
# of voeg de missende methoden toe aan Calculate class
```

### Optie 2: Gebruik Pre-built DLLs (Als Beschikbaar)
Kopieer DLLs naar deze folder:
- `VedAstro.dll`
- `SwissEph.dll` (dependency)

### Optie 3: Download Release
Check VedAstro GitHub releases voor pre-built binaries.

## Huidige Setup
- **Mode**: HTTP Fallback
- **Mock Data**: Actief
- **Performance**: ~1ms (geen C# interop overhead)

## Docker Build
Zonder echte DLLs werkt de Docker build ook in HTTP fallback mode.
