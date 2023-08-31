// Variable to capture value of field
let recordsPerPageOld = 0
let recordsPerPageNew = 0

// When the user enters the field
function captureValue() {

    // Get the original value
    recordsPerPageOld = document.getElementById("scriptInput").value

}

// When the user exits the field
function submitPost() {

    // Get the new value
    recordsPerPageNew = document.getElementById("scriptInput").value

    if (recordsPerPageNew != recordsPerPageOld) {
    // Submit the form with the new records per page number
    document.getElementById("scriptPosted").submit()
    }

}