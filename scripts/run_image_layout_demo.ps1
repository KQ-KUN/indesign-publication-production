param([string]$Python='python',[string]$InDesignExe='',[string]$ComProgId='InDesign.Application.2026')
$ErrorActionPreference='Stop'
$skillRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$artifactRoot=Join-Path $skillRoot '.artifacts/image-layout'
[IO.Directory]::CreateDirectory($artifactRoot) | Out-Null
$lockPath=Join-Path $artifactRoot 'run.lock'
# Existing lock means inspect/resume that run; do not silently delete it or dispatch twice.
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try {
 & $Python -X utf8 (Join-Path $PSScriptRoot 'image_layout_examples.py') prepare
 if($LASTEXITCODE -ne 0){throw 'Sample preparation failed'}
 $request=Get-Content -Raw (Join-Path $artifactRoot 'request.json') | ConvertFrom-Json
 $processes=@(Get-Process InDesign -ErrorAction SilentlyContinue)
 if($processes.Count -eq 0){
  if(!$InDesignExe){$InDesignExe=Join-Path $env:ProgramFiles 'Adobe/Adobe InDesign 2026/InDesign.exe'}
  $process=Start-Process -FilePath $InDesignExe -WindowStyle Hidden -PassThru
  $timer=[Diagnostics.Stopwatch]::StartNew();$stable=0;$lastCpu=-1
  while($timer.Elapsed.TotalSeconds -lt 90){
   $process.Refresh();if($process.HasExited){throw 'InDesign exited at startup'}
   $cpu=$process.TotalProcessorTime.TotalMilliseconds
   $ready=$process.MainWindowHandle -ne [IntPtr]::Zero -and $process.MainWindowTitle -match 'Adobe.*InDesign' -and $process.Responding
   if($ready -and $lastCpu -ge 0 -and $cpu-$lastCpu -lt 100){$stable++}else{$stable=0}
   if($stable -ge 2){break};$lastCpu=$cpu;Start-Sleep -Seconds 1
  }
  if($stable -lt 2){throw 'Host readiness timeout; no second instance launched'}
  $processes=@(Get-Process InDesign)
 }
 if($processes.Count -ne 1){throw 'Expected one host; no concurrent activation'}
 $hostApp=New-Object -ComObject $ComProgId
 $after=@(Get-Process InDesign)
 if($after.Count -ne 1 -or $after[0].Id -ne $processes[0].Id){throw 'COM started a second host; build not dispatched'}
 $jsx=(Join-Path $PSScriptRoot 'image_layout_demo.jsx').Replace('\','/') | ConvertTo-Json -Compress
 $result=$hostApp.DoScript(('app.doScript(File('+$jsx+'),ScriptLanguage.JAVASCRIPT)'),1246973031,[Type]::Missing,[Type]::Missing,[Type]::Missing)
 [IO.File]::WriteAllText((Join-Path ([IO.Path]::GetDirectoryName($request.report)) 'HOST_RESULT.txt'),[string]$result,[Text.UTF8Encoding]::new($false))
 if($result -notlike 'PASS *' -or !$result.Contains($request.run_id)){throw ('Native failure: '+$result)}
 Write-Output $result
 & $Python -X utf8 (Join-Path $PSScriptRoot 'image_layout_examples.py') verify
 if($LASTEXITCODE -ne 0){throw 'Native/PDF verification failed; inspect run report'}
} finally {
 $lock.Dispose();Remove-Item -LiteralPath $lockPath
}
