// main.js

document.addEventListener("DOMContentLoaded", () => {
  console.log("Main.js loaded 🎉");

  // Örnek: sayfa yüklendiğinde navbar'ı biraz daha modern hale getirelim
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    navbar.classList.add("shadow-sm");
  }
});
