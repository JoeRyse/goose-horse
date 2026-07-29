$ErrorActionPreference = "Stop"

$workspace = $PSScriptRoot
$apiOutputDir = Join-Path $workspace "api\output"
$docsMeetingsDir = Join-Path $workspace "docs\meetings"
$frontendPublicDir = Join-Path $workspace "frontend\public\api"
$frontendPublicOutputDir = Join-Path $frontendPublicDir "output"

New-Item -ItemType Directory -Force -Path $frontendPublicDir | Out-Null
New-Item -ItemType Directory -Force -Path $frontendPublicOutputDir | Out-Null

Write-Host "Exporting static data for Vercel / Netlify / GitHub Pages deployment..." -ForegroundColor Cyan

# Find published meetings
$publishedFiles = Get-ChildItem -Path $docsMeetingsDir -Filter "*.html" | Select-Object -ExpandProperty BaseName

$meetingList = @()

# Get all JSON files in api/output
$jsonFiles = Get-ChildItem -Path $apiOutputDir -Filter "*.json"

foreach ($file in $jsonFiles) {
    $isPublished = $publishedFiles -contains $file.BaseName
    
    try {
        $raw = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $obj = $raw | ConvertFrom-Json
        if ($obj -is [array]) { $obj = $obj[0] }

        $track = if ($obj.meta -and $obj.meta.track) { $obj.meta.track } else { $file.BaseName -replace '_\d{4}-\d{2}-\d{2}$', '' -replace '_', ' ' }
        $date = if ($obj.meta -and $obj.meta.date) { $obj.meta.date } else { 
            if ($file.BaseName -match '(\d{4}-\d{2}-\d{2})') { $Matches[1] } else { '2026-07-29' }
        }
        $races = if ($obj.races) { $obj.races } else { @() }
        
        $soloLocks = 0
        $bestBets = 0
        foreach ($r in $races) {
            $contenders = if ($r.all_contenders) { $r.all_contenders } elseif ($r.selections) { $r.selections } else { @() }
            if ($contenders.Count -ge 2) {
                $r1 = [double]($contenders[0].rating)
                $r2 = [double]($contenders[1].rating)
                $gap = $r1 - $r2
                if ($r1 -ge 90.0 -and $gap -ge 5.0) { $soloLocks++ }
                elseif ($gap -ge 3.0) { $bestBets++ }
            }
        }

        # Region assignment
        $region = "USA"
        if ($track -match "Ascot|Goodwood|Kempton|Carlisle|Redcar|Windsor|Wolverhampton|Leicester|York") { $region = "UK" }
        elseif ($track -match "Caulfield|Flemington|Randwick|Doomben|Eagle Farm|Rosehill|Moonee Valley|Belmont|Ascot|Albury|Gatton|Gold Coast|Ipswich|Sunshine Coast|Sandown|Bunbury|Echuca|Goulburn|Grafton|Hobart|Kembla|Mackay|Mildura|Moe|Morphettville|Muswellbrook|Newcastle|Pakenham|Rockhampton|Sale|Scone|Seymour|Tamworth|Taree|Toowoomba|Townsville|Wagga|Warrnambool|Wyong") { $region = "AUS" }
        elseif ($track -match "Tokyo|Funabashi|Kawasaki|Nagoya|Mombetsu|Urawa|Seoul|Busan|Sha Tin|Happy Valley") { $region = "ASIA" }
        elseif ($track -match "Monticello|Hoosier|Northfield|Saratoga Harness|Woodbine Mohawk") { $region = "HARNESS" }

        $meetingItem = [PSCustomObject]@{
            id = $file.BaseName
            filename = $file.Name
            track = $track
            date = $date
            race_count = $races.Count
            solo_locks_count = $soloLocks
            best_bets_count = $bestBets
            region = $region
            is_published = $isPublished
            last_modified = $file.LastWriteTimeUtc.Ticks
        }
        $meetingList += $meetingItem

        # Copy JSON file to frontend/public/api/output/
        Copy-Item -Path $file.FullName -Destination (Join-Path $frontendPublicOutputDir $file.Name) -Force

    } catch {
        Write-Host "Warning skipping $($file.Name): $_" -ForegroundColor Yellow
    }
}

# Sort meetings: published first, then newest date
$sortedMeetings = $meetingList | Sort-Object @{Expression={$_.is_published}; Descending=$true}, @{Expression={$_.date}; Descending=$true}

$meetingsObj = [PSCustomObject]@{
    status = "success"
    meetings = $sortedMeetings
}

$meetingsJson = $meetingsObj | ConvertTo-Json -Depth 5
$meetingsJsonPath = Join-Path $frontendPublicDir "meetings.json"
[System.IO.File]::WriteAllText($meetingsJsonPath, $meetingsJson, [System.Text.Encoding]::UTF8)

Write-Host "Successfully exported $($sortedMeetings.Count) meetings to $frontendPublicDir!" -ForegroundColor Green
