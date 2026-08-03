const countOutput = document.querySelector<HTMLOutputElement>("#count");
const countButton = document.querySelector<HTMLButtonElement>("#count-button");

if (!countOutput || !countButton) {
  throw new Error("Counter elements are missing from the page.");
}

let count = 0;

countButton.addEventListener("click", () => {
  count += 1;
  countOutput.value = String(count);
});
