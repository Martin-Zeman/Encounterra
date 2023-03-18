const colorFill = document.getElementById("color-fill");
const colorButton = document.getElementById("color-button");
const colorInput = document.getElementById("color-input");

function updateFill() {
    const value = parseFloat(colorInput.value);
    if (isNaN(value) || value < 0 || value > 100) {
        return;
    }
    const blueWidth = value + "%";
    colorFill.style.width = blueWidth;
    if (value === 0) {
        colorFill.classList.remove("color-bar__fill--blue");
        colorFill.classList.add("color-bar__fill--red");
    } else if (value === 100) {
        colorFill.classList.remove("color-bar__fill--red");
        colorFill.classList.add("color-bar__fill--blue");
    } else {
        colorFill.classList.add("color-bar__fill--blue");
        colorFill.classList.remove("color-bar__fill--red");
    }
}

colorButton.addEventListener("click", updateFill);
