# Agent instructions

This is the maintained public continuation of the private historical
FileManager project. Preserve GPL-3.0-only and third-party attribution.
Never commit real personnel databases, private configuration, documents,
logs, credentials, environment/build directories or model weights.

Use a dedicated virtual environment and the exact Windows Python 3.12 lock.
Run pytest and `python -m src.main --smoke-test` with an isolated
FILE_MANAGER_HOME. The smoke mode must disable keyboard listening/registration.
Do not alter the developer's registry, startup entries, existing files or ACLs
while testing. Keep file conflicts explicit, targets within the selected root,
and avoid deleting unrelated or externally modified data during rollback.

Historical tests/packaging references in legacy are preserved for provenance,
not current executable acceptance. Record actual test/build limits in HANDOFF.
Do not publish frozen binaries merely because PyInstaller builds successfully;
fulfill bundled dependency source and license requirements first.
