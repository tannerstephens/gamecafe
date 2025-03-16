window.addEventListener("load", () => {
  const form = document.getElementById("registerForm");
  form.onsubmit = () => {
    return (
      form["username"].value.length > 0 &&
      form["password"].value.length > 0 &&
      form["email"].value.length > 0
    );
  };
});
