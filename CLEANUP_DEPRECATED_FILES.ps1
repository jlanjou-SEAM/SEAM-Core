# SEAM deprecated runtime cleanup
# Run from C:\CleanRoom after extracting the clean package.

$Deprecated = @(
  "seam_unified_48h_field.py",
  "continuum_retention_manager.py",
  "continuum_unified_realtime_runtime.py",
  "continuum_unified_realtime_runtime_FIXED.py",
  "INDEX_PATCH_EXAMPLE.html",
  "RECURSIVE_CONVERGENCE_PATCH.py",
  "BAT_PATCH.txt",
  "BAT_PIPELINE_PATCH.txt"
)

foreach ($file in $Deprecated) {
  if (Test-Path $file) {
    Write-Host "Removing deprecated file: $file"
    Remove-Item $file -Force
  }
}

Write-Host "Deprecated runtime cleanup complete."
