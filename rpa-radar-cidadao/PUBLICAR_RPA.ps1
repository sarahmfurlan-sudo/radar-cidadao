# Finaliza a publicacao de RPA sem modificar a pasta de NLP.
$ErrorActionPreference = 'Stop'
$repo = 'C:\dev\radar-cidadao'
$project = Join-Path $repo 'rpa-radar-cidadao'
$python = Join-Path $project '.venv\Scripts\python.exe'
if (-not (Test-Path (Join-Path $repo '.git'))) { throw 'Repositorio Git nao encontrado.' }
if (-not (Test-Path $python)) { throw 'Ambiente Python do RPA nao encontrado. Execute instalacao primeiro.' }
if (-not (Test-Path (Join-Path $project 'pyproject.toml'))) { throw 'Pasta do RPA incompleta.' }
Push-Location $project
try {
  & $python -m pytest -q
  if ($LASTEXITCODE -ne 0) { throw 'Testes falharam; nenhuma publicacao feita.' }
  & $python -m radar_rpa validate --input dados\validacao_rotulada.csv --output saida\validacao
  if ($LASTEXITCODE -ne 0) { throw 'Validacao falhou; nenhuma publicacao feita.' }
} finally { Pop-Location }
Push-Location $repo
try {
  $branch = (& git branch --show-current).Trim()
  if ($branch -ne 'main') { throw "Branch inesperada: $branch. Nao publiquei." }
  $staged = @(& git diff --cached --name-only)
  if ($staged.Count -gt 0) { throw 'Existem mudancas ja preparadas no Git. Revise antes de publicar; nada alterado.' }
  # Nao adicionar saida/, venv/ ou banco sqlite; seguem no .gitignore da pasta.
  & git add -- rpa-radar-cidadao
  if ($LASTEXITCODE -ne 0) { throw 'git add falhou.' }
  $names = @(& git diff --cached --name-only)
  foreach ($n in $names) {
    if (-not ($n -like 'rpa-radar-cidadao/*')) { & git reset --quiet; throw "Arquivo fora do RPA no stage: $n" }
  }
  if ($names.Count -eq 0) { Write-Host 'Nenhuma alteracao do RPA para publicar.'; return }
  Write-Host 'Arquivos que serao publicados:'
  $names | ForEach-Object { Write-Host " - $_" }
  & git diff --cached --check
  if ($LASTEXITCODE -ne 0) { throw 'git diff check falhou.' }
  & git commit -m 'Adiciona prototipo RPA Radar Cidadao com evidencias e validacao'
  if ($LASTEXITCODE -ne 0) { throw 'Commit falhou. Push nao executado.' }
  & git push origin main
  if ($LASTEXITCODE -ne 0) { throw 'Push falhou; commit local foi preservado.' }
  Write-Host 'SUCESSO: RPA publicado no GitHub.'
  & git status -sb
  & git log -1 --oneline
} finally { Pop-Location }
