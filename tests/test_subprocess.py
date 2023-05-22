import subprocess

# cmd = ["powershell", "-Command", "Get-Process"]
# subprocess.run(cmd)
#
# cmd = ["powershell", "-Command", "Get-Process | Where-Object { $_.CPU -gt 0 }"]
# subprocess.run(cmd)
# cmd = ["powershell", "-Command", "Get-EventLog -LogName Security"]
# subprocess.run(cmd)
# cmd = ["powershell", "-Command", "Start-Process powershell -ArgumentList 'Get-EventLog -LogName Security' -Verb RunAs"]
# subprocess.run(cmd)
ps_script = "Get-EventLog -LogName Scurity | Out-File -FilePath C:\\Users\\darwh\\OneDrive\\test.txt -Encoding UTF8; $Error | Out-File -FilePath C:\\Users\\darwh\\OneDrive\\error.txt -Encoding UTF8"
cmd = [
    "powershell.exe", "-Command", "Start-Process", "powershell", "-Verb", "runAs", "-Wait", "-ArgumentList",
    "'-executionpolicy', 'bypass', '-Command', '" + ps_script + "'"
]
subprocess.run(cmd, shell=True)

try:
    with open("C:\\Users\\darwh\\OneDrive\\test.txt", "r") as file:
        print(file.read())
except FileNotFoundError:
    print("File not found")
try:
    with open("C:\\Users\\darwh\\OneDrive\\error.txt", "r") as file:
        print(file.read())
except FileNotFoundError:
    print("Error file not found")
