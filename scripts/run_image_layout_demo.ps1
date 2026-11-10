param([string]$Python='python',[string]$Target='',[switch]$AllowLaunch,[string]$InDesignExe='',[string]$ComProgId='')
$ErrorActionPreference='Stop'
$skillRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$artifactRoot=Join-Path $skillRoot '.artifacts/image-layout'
[IO.Directory]::CreateDirectory($artifactRoot) | Out-Null
$lockPath=Join-Path $artifactRoot 'run.lock'
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
$pending=$false
try {
 & $Python -X utf8 (Join-Path $PSScriptRoot 'image_layout_examples.py') prepare
 if($LASTEXITCODE -ne 0){throw 'Sample preparation failed'}
 $request=Get-Content -Raw (Join-Path $artifactRoot 'request.json') | ConvertFrom-Json
 if(-not $Target){if($ComProgId){$Target=$ComProgId}elseif($InDesignExe){$Target=$InDesignExe}}
 $launcher=Join-Path $PSScriptRoot 'indesign_runtime.py'
 $arguments=@('-X','utf8',$launcher,'run',(Join-Path $PSScriptRoot 'image_layout_demo.jsx'),'--jobs',(Join-Path $artifactRoot 'host-jobs'),'--expect-prefix','PASS ','--wait-seconds','0')
 if($Target){$arguments+=@('--target',$Target)}
 if($AllowLaunch){$arguments+='--allow-launch'}
 $receipt=& $Python @arguments
 if($LASTEXITCODE -ne 0){throw ($receipt -join [Environment]::NewLine)}
 $status=($receipt -join [Environment]::NewLine) | ConvertFrom-Json
 $pending=$true
 $job=[string]$status.job
 $bytes=[Text.Encoding]::UTF8.GetBytes($job);$lock.Write($bytes,0,$bytes.Length);$lock.Flush()
 while($status.state -in @('QUEUED','RUNNING')){
  $receipt=& $Python -X utf8 $launcher status $job --wait-seconds 10
  $status=($receipt -join [Environment]::NewLine) | ConvertFrom-Json
 }
 $pending=$false
 if($status.state -ne 'COMPLETED'){throw ($status.error)}
 $result=[string]$status.host.native_result
 [IO.File]::WriteAllText((Join-Path ([IO.Path]::GetDirectoryName($request.report)) 'HOST_RESULT.txt'),$result,[Text.UTF8Encoding]::new($false))
 if(-not $result.Contains($request.run_id)){throw ('Native run ID mismatch: '+$result)}
 Write-Output $result
 & $Python -X utf8 (Join-Path $PSScriptRoot 'image_layout_examples.py') verify
 if($LASTEXITCODE -ne 0){throw 'Native/PDF verification failed; inspect run report'}
} finally {
 $lock.Dispose()
 if(-not $pending){Remove-Item -LiteralPath $lockPath}
}
