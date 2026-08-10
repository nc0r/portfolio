const year = document.querySelector("#year");
const header = document.querySelector(".site-header");
const checkoutButton = document.querySelector(".checkout-button");

if (year) {
  year.textContent = new Date().getFullYear();
}

window.addEventListener("scroll", () => {
  const elevated = window.scrollY > 24;
  header?.classList.toggle("is-elevated", elevated);
});

document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (event) => {
    const targetId = link.getAttribute("href");
    if (!targetId || targetId === "#") return;

    const target = document.querySelector(targetId);
    if (!target) return;

    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

checkoutButton?.addEventListener("click", (event) => {
  event.preventDefault();
  checkoutButton.textContent = "Opening Checkout...";

  window.setTimeout(() => {
    checkoutButton.textContent = "Checkout Ready";
  }, 900);
});
