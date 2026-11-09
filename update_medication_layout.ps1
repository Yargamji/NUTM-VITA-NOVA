$ErrorActionPreference = "Stop"

$file = ".\app\templates\doctor\consultation.html"

if (-not (Test-Path $file)) {
    throw "Template file not found: $file"
}

$content = Get-Content $file -Raw

# --------------------------------------------------
# 1. Restore saved medication drafts and compact layout
# --------------------------------------------------

$startMarker = "        <!-- MEDICATION PRESCRIPTIONS -->"
$endMarker   = "        <!-- END INVESTIGATION AND PRESCRIPTION SECTIONS -->"

$start = $content.IndexOf($startMarker)
$end   = $content.IndexOf($endMarker)

if ($start -lt 0 -or $end -lt 0 -or $end -le $start) {
    throw "Could not locate the medication section boundaries. No changes made."
}

$newMedicationSection = @'
        <!-- MEDICATION PRESCRIPTIONS -->
        <div class="form-section" id="medication-prescriptions-section">

            <h3>Medication Prescriptions</h3>

            <p class="text-secondary">
                Enter the medications required for this encounter.
            </p>

            <div id="medication-list">

                {% if draft_prescription and draft_prescription.items %}
                    {% for item in draft_prescription.items %}
                    <div class="medication-row form-group">

                        <label>Medication Name</label>
                        <input
                            type="text"
                            name="medication_name"
                            class="form-control"
                            value="{{ item.medication_name or '' }}"
                        >

                        <div style="display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-top:10px;">

                            <div>
                                <label>Dose</label>
                                <input
                                    type="text"
                                    name="medication_dose"
                                    class="form-control"
                                    value="{{ item.dose or '' }}"
                                >
                            </div>

                            <div>
                                <label>Formulation</label>
                                <input
                                    type="text"
                                    name="medication_formulation"
                                    class="form-control"
                                    value="{{ item.formulation or '' }}"
                                >
                            </div>

                        </div>

                        <div style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:10px;">

                            <div>
                                <label>Route</label>
                                <select name="medication_route" class="form-control">
                                    <option value="">Select route</option>
                                    {% for route in ['Oral', 'IV', 'IM', 'SC', 'Topical', 'Inhalation', 'Rectal', 'Ophthalmic', 'Otic', 'Other'] %}
                                    <option value="{{ route }}" {% if item.route == route %}selected{% endif %}>{{ route }}</option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div>
                                <label>Frequency</label>
                                <input
                                    type="text"
                                    name="medication_frequency"
                                    class="form-control"
                                    value="{{ item.frequency or '' }}"
                                >
                            </div>

                            <div>
                                <label>Duration</label>
                                <input
                                    type="text"
                                    name="medication_duration"
                                    class="form-control"
                                    value="{{ item.duration or '' }}"
                                >
                            </div>

                        </div>

                        <label style="margin-top:10px;">Additional Instructions</label>
                        <textarea
                            name="medication_instructions"
                            class="form-control"
                            rows="1"
                        >{{ item.instructions or '' }}</textarea>

                        <button type="button" class="btn btn-danger remove-medication">
                            Remove Medication
                        </button>

                    </div>
                    {% endfor %}
                {% else %}
                    <div class="medication-row form-group">

                        <label>Medication Name</label>
                        <input type="text" name="medication_name" class="form-control">

                        <div style="display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-top:10px;">

                            <div>
                                <label>Dose</label>
                                <input type="text" name="medication_dose" class="form-control">
                            </div>

                            <div>
                                <label>Formulation</label>
                                <input type="text" name="medication_formulation" class="form-control">
                            </div>

                        </div>

                        <div style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:10px;">

                            <div>
                                <label>Route</label>
                                <select name="medication_route" class="form-control">
                                    <option value="">Select route</option>
                                    <option value="Oral">Oral</option>
                                    <option value="IV">IV</option>
                                    <option value="IM">IM</option>
                                    <option value="SC">SC</option>
                                    <option value="Topical">Topical</option>
                                    <option value="Inhalation">Inhalation</option>
                                    <option value="Rectal">Rectal</option>
                                    <option value="Ophthalmic">Ophthalmic</option>
                                    <option value="Otic">Otic</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>

                            <div>
                                <label>Frequency</label>
                                <input type="text" name="medication_frequency" class="form-control">
                            </div>

                            <div>
                                <label>Duration</label>
                                <input type="text" name="medication_duration" class="form-control">
                            </div>

                        </div>

                        <label style="margin-top:10px;">Additional Instructions</label>
                        <textarea name="medication_instructions" class="form-control" rows="1"></textarea>

                        <button type="button" class="btn btn-danger remove-medication">
                            Remove Medication
                        </button>

                    </div>
                {% endif %}

            </div>

            <button
                type="button"
                id="add-medication"
                class="btn btn-secondary"
            >
                Add Medication
            </button>

            <div class="form-actions" style="margin-top:12px;">
                <button
                    type="submit"
                    name="action"
                    value="send_medications"
                    class="btn btn-secondary"
                    onclick="return confirm('Send the medication prescription to the pharmacy?');"
                >
                    SEND MEDICATION(S)
                </button>
            </div>

        </div>


'@

$content = $content.Substring(0, $start) +
           $newMedicationSection +
           $content.Substring($end)

# --------------------------------------------------
# 2. Place SEND REQUEST after the investigation list
# --------------------------------------------------

$investigationButtonPattern = '(?s)(<button\s+type="button"\s+id="add-investigation".*?</button>)'

$investigationMatches = [regex]::Matches(
    $content,
    $investigationButtonPattern
)

if ($investigationMatches.Count -ne 1) {
    throw "Could not uniquely locate the Add Investigation button. No changes made."
}

$sendRequestButton = @'

            <div class="form-actions" style="margin-top:12px;">
                <button
                    type="submit"
                    name="action"
                    value="send_investigations"
                    class="btn btn-secondary"
                    onclick="return confirm('Send the selected investigation requests to the laboratory?');"
                >
                    SEND REQUEST
                </button>
            </div>
'@

$content = [regex]::Replace(
    $content,
    $investigationButtonPattern,
    ('$1' + $sendRequestButton),
    1
)

# --------------------------------------------------
# 3. Remove the old bottom order-submission buttons
# --------------------------------------------------

$oldButtonsPattern = '(?s)\s*<!-- INDEPENDENT ORDER SUBMISSION BUTTONS -->\s*<div class="form-actions">\s*<button\s+type="submit"\s+name="action"\s+value="send_investigations".*?</button>\s*<button\s+type="submit"\s+name="action"\s+value="send_medications".*?</button>\s*</div>'

if (-not [regex]::IsMatch($content, $oldButtonsPattern)) {
    throw "Could not locate the old independent-order buttons. No changes made."
}

$content = [regex]::Replace($content, $oldButtonsPattern, "", 1)

# Save only after all replacements have succeeded.
Set-Content -Path $file -Value $content -Encoding UTF8

Write-Host ""
Write-Host "SUCCESS: Consultation template updated." -ForegroundColor Green
Write-Host "Medication drafts, compact fields, and order button positions have been updated."