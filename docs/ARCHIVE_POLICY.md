# Documentation Archive Policy

## Doel
Dit bestand documeert de archiveringsstrategie voor verouderde documentatie.

## Archiveerbeleid
Verouderde rapporten, implementatieplannen en auditdocumenten worden verplaatst naar `docs/archive/`.

## Te archiveren documenten
De volgende categorien documenten moeten worden gearchiveerd:

### Verouderde Audit/Gap Analyses
- `AUDIT_ALIGNMENT_REPORT.md`
- `DEEP_DIVE_AUDIT.md`
- `GAP_ANALYSIS_REPORT.md`
- `PERFORMANCE_AUDIT.md`
- `ASSET_SYSTEM_GAP_ANALYSIS.md`

### Voltooide Epic/Fase Summaries
- `EPIC_01_COMPLETION_SUMMARY.md`
- `EPIC_02_COMPLETION_SUMMARY.md`
- `FASE_3_C_FINAL_COMPLETION.md`
- `FASE_4_1_COMPLETION_SUMMARY.md`

### Verouderde Implementatieplannen
- `IMPLEMENTATION_CHECKLIST.md`
- `IMPLEMENTATION_ROADMAP.md`
- `IMPLEMENTATION_STRATEGY_ASSET_SYSTEM.md`
- `INFRASTRUCTURE_AUDIT_AND_IMPLEMENTATION_PLAN.md`

### Verouderde Migratie/Verificatie Rapporten
- `MIGRATION_V17_TO_V18.md`
- `MIGRATION_VERIFICATION_REPORT.md`
- `ASSET_IMPORT_VERIFICATION_REPORT.md`

### Verouderde Backtest Resultaten
- `BACKTEST_PERFORMANCE_V18.md`
- `BACKTEST_RESULTS_*.md` (alle historische resultaten)

## Archiveer Commando
```bash
mkdir -p docs/archive
# Verplaats bestanden per categorie:
# mv docs/AUDIT_ALIGNMENT_REPORT.md docs/archive/
# mv docs/EPIC_*_COMPLETION_SUMMARY.md docs/archive/
# etc.
```

## Single Source of Truth
Na archivering zijn de volgende documenten de actieve bronnen:
- `docs/ARCHITECTURE_DESIGN.md` - Huidige architectuur
- `docs/CI_CD_SETUP.md` - CI/CD configuratie
- `docs/DOCKER_DEPLOYMENT.md` - Docker deployment
- `docs/INCIDENT_RESPONSE.md` - Incident response plan
