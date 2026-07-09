
let currentStep = 0;

const steps = document.querySelectorAll(".step");
const indicators = document.querySelectorAll(".step-indicator");

function showStep(index) {
  steps.forEach((step, i) => {
    step.classList.toggle("active", i === index);
    indicators[i].classList.toggle("active", i <= index);
  });
}

function nextStep() {
  if (currentStep < steps.length - 1) {
    currentStep++;
    showStep(currentStep);
  }
}

function prevStep() {
  if (currentStep > 0) {
    currentStep--;
    showStep(currentStep);
  }
}

showStep(currentStep);