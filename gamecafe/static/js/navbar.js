window.addEventListener("load", () => {
  let expanded = false;

  const burger = document.getElementById("burger");
  const target = document.getElementById(burger.dataset.target);

  burger.onclick = () => {
    burger.classList.toggle("is-active");
    target.classList.toggle("is-active");
  };
});
