// When the user clicks on the password field, show the message box
function fromClicked() {
  document.getElementById("passmessage").style.display = "block";
}

// When the user clicks outside of the password field, hide the message box
// Add onblur="fromExit()" to field to use this
function fromExit() {
  document.getElementById("passmessage").style.display = "none";
}

// When the user starts to type something inside the password field
function fromType(element) {

  // Password characters check
  const passLetter = document.getElementById("passletter");
  const passCapital = document.getElementById("passcapital");
  const passNumber = document.getElementById("passnumber");
  const passLength = document.getElementById("passlength");

  // Validate lowercase letters
  const lowerCaseLetters = /[a-z]/g;
  if(element.value.match(lowerCaseLetters)) {
      passLetter.classList.remove("invalid");
      passLetter.classList.add("valid");
  } else {
      passLetter.classList.remove("valid");
      passLetter.classList.add("invalid");
  }

  // Validate capital letters
  const upperCaseLetters = /[A-Z]/g;
  if(element.value.match(upperCaseLetters)) {
      passCapital.classList.remove("invalid");
      passCapital.classList.add("valid");
  } else {
      passCapital.classList.remove("valid");
      passCapital.classList.add("invalid");
  }

  // Validate numbers
  const numbers = /[0-9]/g;
  if(element.value.match(numbers)) {
      passNumber.classList.remove("invalid");
      passNumber.classList.add("valid");
  } else {
      passNumber.classList.remove("valid");
      passNumber.classList.add("invalid");
  }

  // Validate length
  if(element.value.length >= 9) {
      passLength.classList.remove("invalid");
      passLength.classList.add("valid");
  } else {
      passLength.classList.remove("valid");
      passLength.classList.add("invalid");
  }
  
}