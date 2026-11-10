param([Parameter(Mandatory=$true)][string]$Request)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$requestData=Get-Content -LiteralPath $Request -Raw -Encoding UTF8 | ConvertFrom-Json
$target=$requestData.target
$before=@(Get-Process InDesign -ErrorAction SilentlyContinue)
if($before.Count -eq 0){
    if(-not $requestData.allow_launch){throw 'No running host; launching was not allowed.'}
    $started=Start-Process -FilePath ([string]$target.path) -WindowStyle Hidden -PassThru
    $timer=[Diagnostics.Stopwatch]::StartNew();$stable=0;$lastCpu=-1
    while($timer.Elapsed.TotalSeconds -lt 90){
        $started.Refresh()
        if($started.HasExited){throw 'InDesign exited during startup; no relaunch attempted.'}
        $cpu=$started.TotalProcessorTime.TotalMilliseconds
        if($started.MainWindowHandle -ne [IntPtr]::Zero -and $started.Responding -and $lastCpu -ge 0 -and $cpu-$lastCpu -lt 100){$stable++}else{$stable=0}
        if($stable -ge 2){break}
        $lastCpu=$cpu;Start-Sleep -Seconds 1
    }
    if($stable -lt 2){throw 'Startup readiness timed out; inspect the existing process/dialogs before another run.'}
}
try {
    $hostApp=[Runtime.InteropServices.Marshal]::GetActiveObject([string]$target.id)
} catch {
    # InDesign may not publish an object in the Running Object Table. Bind its
    # registered class once, only after observing one ready matching process.
    $bindingProcesses=@(Get-Process InDesign -ErrorAction SilentlyContinue)
    if($bindingProcesses.Count -ne 1 -or -not $bindingProcesses[0].Responding -or -not [string]::Equals([string]$bindingProcesses[0].Path,[string]$target.path,[StringComparison]::OrdinalIgnoreCase)){
        throw 'No unambiguous ready COM target; class activation was not attempted.'
    }
    $bindingIds=@($bindingProcesses.Id | Sort-Object) -join ','
    $hostApp=New-Object -ComObject ([string]$target.id)
    if((@((Get-Process InDesign -ErrorAction SilentlyContinue).Id | Sort-Object) -join ',') -ne $bindingIds){throw 'COM created another process; build not dispatched. Inspect hosts; do not retry.'}
}
$actualPath=[string]$hostApp.DoScript('app.fullName.fsName',1246973031,[Type]::Missing,[Type]::Missing,[Type]::Missing)
if(-not [string]::Equals([IO.Path]::GetFullPath($actualPath),[IO.Path]::GetFullPath([string]$target.path),[StringComparison]::OrdinalIgnoreCase)){
    throw 'COM attached to a different InDesign installation; script was not dispatched.'
}
$after=@(Get-Process InDesign -ErrorAction SilentlyContinue)
if($before.Count -gt 0 -and (@($before.Id | Sort-Object) -join ',') -ne (@($after.Id | Sort-Object) -join ',')){
    throw 'Host process inventory changed; build was not dispatched.'
}
if($before.Count -eq 0 -and $after.Count -ne 1){throw 'Expected exactly one newly launched host; build was not dispatched.'}
$modal=[string]$hostApp.DoScript('String(app.modalState)',1246973031,[Type]::Missing,[Type]::Missing,[Type]::Missing)
if($modal -eq 'true'){throw 'InDesign has an active modal dialog. Resolve it before resubmission.'}
$version=[string]$hostApp.Version
$hasher=[Security.Cryptography.SHA256]::Create()
try{$scriptHash=([BitConverter]::ToString($hasher.ComputeHash([IO.File]::ReadAllBytes([string]$requestData.script)))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
if($scriptHash -ne [string]$requestData.script_sha256){throw 'Script changed before dispatch; no build executed.'}
$scriptPath=([string]$requestData.script).Replace('\','/') | ConvertTo-Json -Compress
$scriptCode='app.doScript(File('+$scriptPath+'),ScriptLanguage.JAVASCRIPT);'
$nativeResult=$hostApp.DoScript($scriptCode,1246973031,[Type]::Missing,[Type]::Missing,[Type]::Missing)
[pscustomobject]@{version=$version;path=$actualPath;native_result=[string]$nativeResult} | ConvertTo-Json -Compress
