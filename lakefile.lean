import Lake
open Lake DSL

-- Workspace shell so the VS Code Lean extension (and `lake env lean`) can
-- resolve `import Aeneas` from generated files anywhere in this repo
-- (mbpp/**/lean/*.lean, tests output). It reuses the packages already built
-- for the Aeneas Lean library (Mathlib etc.) instead of fetching them again.
package «sim» where
  packagesDir := "aeneas/backends/lean/.lake/packages"

require aeneas from "aeneas/backends/lean"
