SEAM GitHub Pages Clean Replacement

Purpose:
Replace the current broken GitHub Pages deployment surface with a known-good root layout.

This package contains ONLY the public deployment files:
- index.html
- .nojekyll
- css/
- js/
- data/

Recommended wholesale replace from PowerShell, starting in C:\CleanRoom:

# 1. Optional safety snapshot
mkdir _deploy_backup
copy index.html _deploy_backup\index.html
xcopy css _deploy_backup\css /E /I /Y
xcopy js _deploy_backup\js /E /I /Y
xcopy data _deploy_backup\data /E /I /Y

# 2. Remove only the public deployment surface
Remove-Item -Recurse -Force css,js,data -ErrorAction SilentlyContinue
Remove-Item -Force index.html,.nojekyll -ErrorAction SilentlyContinue

# 3. Extract this ZIP into C:\CleanRoom
# Confirm:
# C:\CleanRoom\index.html
# C:\CleanRoom\.nojekyll
# C:\CleanRoom\css\core.css
# C:\CleanRoom\js\runtime-ui.js
# C:\CleanRoom\data\latest.json

# 4. Publish
git add -A
git commit -m "Replace GitHub Pages deployment surface"
git push origin main --force

# 5. Test with cache busting
https://jlanjou-seam.github.io/SEAM-Core/?v=clean1

Expected result:
The SEAM Recursive Inference Monitor loads with an Operational Target Grid.
