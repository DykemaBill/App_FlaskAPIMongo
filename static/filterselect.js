let filterTextOld = ""
let filterTextNew = ""

// When the user enters the field
function captureSearch(element) {

    // Get the original typed filter value
    filterTextOld = element.value

}

// When the user exits the field
function filterSearch(element, filterName, filterURL) {

    // Get the new typed filter value
    filterTextNew = element.value

    if (filterTextNew != filterTextOld) {
        // Check to see if the new search is different than the old
        //filterURL = document.getElementById("citySearchExisting").value
        if (filterTextNew != "") { // Use it if it is not blank
            newURL = filterURL + "&" + filterName + "=" + filterTextNew
        } else {
            newURL = filterURL // If it is blank, clear the filter
        }
        // Load page using new filtered address
        window.location.href = newURL
    }

}

// When the user selects a new filter
function filterChange(element) {

    // Get the new URL to use
    newURL = element.value

    // Load page using new filtered address
    window.location.href = newURL

}

// When the user selects a new state
function filterState(filterURL) {

    // Get the new state
    newState = document.getElementById("state").value

    // Set the new URL to use
    if (newState != "") {
        newURL = filterURL + "&state=" + newState
    } else {
        newURL = filterURL
    }
    
    // Load page using new filtered address
    window.location.href = newURL

}