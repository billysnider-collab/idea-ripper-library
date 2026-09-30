# Reference "rip deploy" for Windows (added 2026-09-30). Same guarantees as safe-deploy.sh:
# single instance (named mutex), build only from origin/main's build_site.py, abort when the
# local template differs or HEAD is behind, never force-push, site guard + live smoke.
$ErrorActionPreference = 'Stop'
Set-Location (git rev-parse --show-toplevel)
$mutex = New-Object System.Threading.Mutex($false, 'Global\IdeaRipperRipDeploy')
if (-not $mutex.WaitOne(0)) { Write-Output 'ABORT: another rip deploy is running'; exit 3 }
try {
  $template = @('build_site.py','404.html','_config.yml','tools','.github')
  git fetch --quiet origin main
  git diff --quiet origin/main -- @template
  if ($LASTEXITCODE -ne 0) { Write-Output 'ABORT: local template files differ from origin/main'; git diff --stat origin/main -- @template; exit 4 }
  git pull --ff-only --autostash --quiet origin main
  if ($LASTEXITCODE -ne 0) { Write-Output 'ABORT: HEAD cannot fast-forward to origin/main'; exit 5 }
  $behind = git rev-list --count HEAD..origin/main
  if ($behind -ne '0') { Write-Output "ABORT: HEAD is $behind commits behind origin/main"; exit 5 }
  $remoteHash = python -c "import subprocess,hashlib;print(hashlib.sha256(subprocess.run(['git','show','origin/main:build_site.py'],capture_output=True).stdout).hexdigest())"
  $localHash = python -c "import hashlib;print(hashlib.sha256(open('build_site.py','rb').read()).hexdigest())"
  if ($localHash -ne $remoteHash) { Write-Output "ABORT: build_site.py hash $localHash != origin/main $remoteHash"; exit 6 }
  python build_site.py; if ($LASTEXITCODE) { exit 7 }
  python build_index.py; if ($LASTEXITCODE) { exit 7 }
  python tools/site_guard.py check; if ($LASTEXITCODE) { Write-Output 'ABORT: site guard failed; nothing pushed'; exit 7 }
  $n = python -c "import json;d=json.load(open('cards.json',encoding='utf-8'));b=d['books'];t=sum(1 for x in b if x['genre']=='Thesis');print(len(d['cards']),len(b)-t,t)"
  $a = $n -split ' '
  foreach ($f in 'cards.json','shelf.yaml','books','fullbooks.json','index.html','sitemap.xml','robots.txt','assets','data') { if (Test-Path $f) { git add -A -- $f } }
  git diff --cached --quiet
  if ($LASTEXITCODE -eq 0) { Write-Output 'nothing to deploy'; exit 0 }
  git commit -q -m ("rip deploy: {0} rips, {1} books, {2} theses ({3})" -f $a[0], $a[1], $a[2], (Get-Date -Format yyyy-MM-dd))
  git push origin HEAD:main
  if ($LASTEXITCODE) { Write-Output 'push rejected (main moved); re-run'; exit 9 }
} finally { $mutex.ReleaseMutex() }
