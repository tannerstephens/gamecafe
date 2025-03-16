window.addEventListener("load", () => {
  const form = document.getElementById("loginForm");
  form.onsubmit = (e) => {
    return (
      form["username"].value.length > 0 && form["password"].value.length > 0
    );
  };
});
