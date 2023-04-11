import subprocess
from subprocess import CompletedProcess

command: str = "powershell.exe Get-Service"
result: CompletedProcess = subprocess.run(command, capture_output=True, text=True)

print(result.stdout)
