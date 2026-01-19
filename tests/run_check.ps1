Write-Host "Running Check..."
python tests/check_repl.py > test_output.txt 2>&1
Get-Content test_output.txt
