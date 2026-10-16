document.addEventListener('DOMContentLoaded', function () {
    checkForLotAndCountType();
});

let selectLotModal;

function checkForLotAndCountType() {
    const lotId = document.getElementById('lotId').value;
    const countType = document.getElementById('count_type').value;

    if (!lotId || !countType || lotId === "None" || countType === "None") {
        // Show the selection modal
        selectLotModal = new bootstrap.Modal(document.getElementById('selectLotModal'));
        selectLotModal.show();

        // Fetch lots that are pending or inspecting
        fetchPendingAndInspectingLots();
    } else {
        // Continue with initialization if both values are populated
        console.log(`Initialized with Lot ID: ${lotId}, Count Type: ${countType}`);
        initializeCounting(lotId, countType);
    }
}

function proceedWithSelection() {
    const countTypeBoxes = document.getElementById('countTypeBoxes').checked;
    const countType = countTypeBoxes ? 'box' : 'fuze';
    const lotId = document.getElementById('lotSelect').value;

    if (!lotId) {
        alert("Please select a lot.");
        return;
    }

    // Redirect to the same page with parameters
    window.location.href = `/user/count_boxes_and_primers?lot_id=${lotId}&count_type=${countType}`;
}

function fetchPendingAndInspectingLots() {
    fetch('/lots/get_lots_for_inspection')
        .then(response => response.json())
        .then(data => {
            const lotSelect = document.getElementById('lotSelect');
            lotSelect.innerHTML = '';
            const lots = data.object;
            if (!lots || lots.length === 0) {
                lotSelect.innerHTML = '<option value="">No pending or inspecting lots found</option>';
                return;
            }
            let options = '<option value="" selected disabled>Select a lot</option>';
            lots.forEach(lot => {
                options += `<option value="${lot.id}">${lot.lot_number} (${lot.inspection_status}) - ${lot.fuze_type}</option>`;
            });
            lotSelect.innerHTML = options;
        })
        .catch(error => {
            console.error('Error fetching lots:', error);
            document.getElementById('lotSelect').innerHTML = '<option value="">Error loading lots</option>';
        });
}

function initializeCounting(lot_id, count_type) {
    document.getElementById('type_title').innerHTML = count_type === 'boxes' ? 'Box Type' : 'Primer Type';
    fetch('/lots/get_count_information?lot_id=' + lot_id + '&count_type=' + count_type)
        .then(response => response.json())
        .then(data => {
            const countInformation = data.object;

            if (!countInformation) {
                alert("No count information found for this lot.");
                window.location.href = "/user/count_boxes_and_fuzes";
                return;
            }
            console.log(countInformation);
            renderCountInformation(countInformation);
        })
        .catch(error => {
            console.error('Error fetching count information:', error);
            alert("Error loading count information.");
        });
}

function renderCountInformation(countInformation) {
    document.getElementById('boxTypeOrFuzeType').innerHTML = countInformation.fuze_or_box_type;
    document.getElementById('count').value = countInformation.count;
    document.getElementById('lotNumber').innerHTML = countInformation.lot_number;
    if (countInformation.count !== countInformation.number_of_boxes_or_fuzes) {
        console.log("Inside if")
        renderCountStatus("Pending")
    } else {
        renderCountStatus("Completed")
    }
}

function renderCountStatus(countStatus) {
    if (countStatus === "Pending") {
        document.getElementById('countingStatus').innerHTML = "<span class='badge bg-primary'>Pending</span>";
        document.getElementById('instructionText').innerHTML = "Please Click The Start Counting Button To Start Counting."
    } else if (countStatus === "Counting") {
        document.getElementById('countingStatus').innerHTML = "<span class='badge bg-warning'>Counting</span>";
        document.getElementById('instructionText').innerHTML = "Please Waiting..."
    } else if (countStatus === "Completed") {
        document.getElementById('countingStatus').innerHTML = "<span class='badge bg-success'>Completed</span>";
        document.getElementById('instructionText').innerHTML = "Counting Completed."
    }
}

function startCounting() {
    const lotId = document.getElementById('lotId').value;
    const countType = document.getElementById('count_type').value;
    const countInput = document.getElementById('count');
    const startBtn = document.getElementById('startCountingBtn');

    // Disable inputs and button, show spinner
    countInput.disabled = true;
    startBtn.disabled = true;
    const spinner = startBtn.querySelector('.spinner-border');
    if (spinner) spinner.classList.remove('d-none');

    renderCountStatus("Counting");

    fetch('/counting/start_m104_counting?lot_id=' + lotId + '&count_type=' + countType, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
        .then(async response => {
            if (!response.ok) {
                let errMessage = "Error starting counting.";
                try {
                    const err = await response.json();
                    if (err.detail) errMessage = err.detail;
                } catch (e) { }
                throw new Error(errMessage);
            }
            return response.json();
        })
        .then(data => {
            console.log(data.object);
            renderCountInformation(data.object);

            if (typeof showToast === 'function') {
                showToast("Count updated successfully!", "success");
            }

            // Re-enable if not completed
            if (data.object && data.object.count !== data.object.number_of_boxes_or_fuzes) {
                countInput.disabled = false;
                startBtn.disabled = false;
            } else {
                if (typeof showToast === 'function') {
                    setTimeout(() => showToast("Counting completed for this lot!", "success"), 500);
                }
            }
        })
        .catch(error => {
            console.error('Error starting counting:', error);
            if (typeof showToast === 'function') {
                showToast(error.message || "Error starting counting.", "error");
            } else {
                alert(error.message || "Error starting counting.");
            }
            // Re-enable on error
            countInput.disabled = false;
            startBtn.disabled = false;
        })
        .finally(() => {
            if (spinner) spinner.classList.add('d-none');
        });
}