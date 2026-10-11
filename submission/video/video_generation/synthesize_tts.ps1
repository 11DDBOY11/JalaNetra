Add-Type -AssemblyName System.Speech

$scenes = @(
    @{
        id = 1
        text = "JalaNetra is a responsible water-security decision-support system for Mangaluru. Coastal Karnataka receives heavy rainfall, but communities can still experience groundwater stress after the monsoon."
    },
    @{
        id = 2
        text = "JalaNetra integrates 4,962 real historical Central Ground Water Board observations from 115 monitoring stations in Dakshin Kannada, covering 1996 to 2020. These are quarterly government observations, not live groundwater sensor readings."
    },
    @{
        id = 3
        text = "Most dashboards would turn old data into a confident-looking alert. JalaNetra does the opposite. When the latest verified station observation is too old, it shows historical groundwater context only and refuses to generate a misleading current tanker-booking recommendation."
    },
    @{
        id = 4
        text = "Residents can report whether water supply came, was low, or was unavailable. This creates a pathway for current community signals while protecting users from overconfident forecasts based on stale measurements."
    },
    @{
        id = 5
        text = "For preparedness, JalaNetra includes a clearly labelled what-if simulator. A dry-water scenario can demonstrate a precautionary advisory, but it is always marked as a scenario simulation, not a live measurement and not a real alert."
    },
    @{
        id = 6
        text = "The production-ready AWS architecture is defined with CDK using API Gateway, Lambda, DynamoDB, S3, EventBridge, SNS, Polly, and Amplify. This hackathon demonstration runs locally, sends no messages, and deploys no cloud resources."
    },
    @{
        id = 7
        text = "JalaNetra turns historical groundwater records into transparent local context, knows when data is too old to act on, and prepares a safer path from community reports to water-stress preparedness."
    }
)

$outDir = "submission\video\narration\temp_scenes"
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

foreach ($s in $scenes) {
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 1
    $outPath = Join-Path $outDir ("scene_" + $s.id + ".wav")
    $synth.SetOutputToWaveFile($outPath)
    $synth.Speak($s.text)
    $synth.Dispose()
    Write-Output ("Generated scene " + $s.id + ": " + $outPath)
}
Write-Output "All scenes synthesized successfully!"
