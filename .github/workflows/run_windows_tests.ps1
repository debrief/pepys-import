$PythonPath =  python -c "import sys; print(sys.executable)" | Out-String
$PythonPath = $PythonPath.Trim()

.\PsExec.exe -accepteula -l cmd.exe /c python.exe $PythonPath test_postgres.py ^> output.txt
type output.txt

runas /trustlevel:0x20000 "test.bat"