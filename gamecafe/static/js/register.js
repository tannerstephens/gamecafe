window.addEventListener("load", () => {
  const form = document.getElementById("registerForm");
  const submitButton = document.getElementById("submit");

  form["username"].oninput = () => {
    form["username"].classList.remove("is-danger");
  };

  form["email"].oninput = () => {
    form["email"].classList.remove("is-danger");
  };

  form.onsubmit = () => {
    return !submitButton.disabled;
  };

  form.oninput = () => {
    submitButton.disabled = !(
      form["username"].value.length > 0 &&
      form["password"].value.length >= 8 &&
      form["email"].value.length > 0
    );
  };

  form.oninput();
});
