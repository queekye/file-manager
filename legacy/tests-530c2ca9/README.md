# Pre-migration test references

Unmodified tests from source commit 530c2ca9 are preserved here. The old suite
contains removed JSON PersonManager/DirectoryTemplate APIs and Tk selectors,
and originally had error-logger gaps. Those tests are historical evidence,
not the default validation suite for the current SQLite/PyQt continuation.
Current tests are ../../tests. Conflict tests now require preserving both files.
The separate migration report records actual baseline results and limitations.
