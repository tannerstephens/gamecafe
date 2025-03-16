window.addEventListener("load", () => {
  const selects = document.querySelectorAll("select");

  for (let select of selects) {
    select.oninput = () => {
      select.parentElement.classList.remove("is-success");
      select.parentElement.classList.add("is-warning");
      fetch(`/api/users/${select.dataset.userid}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          role: select.value,
        }),
      })
        .then((resp) => resp.json())
        .then((json) => {
          if (json.success) {
            select.parentElement.classList.add("is-success");
            select.parentElement.classList.remove("is-warning");
          }
        });
    };
  }

  const deleteUserButtons = document.getElementsByClassName("deleteuser");

  for (let button of deleteUserButtons) {
    button.onclick = () => {
      fetch(`/api/users/${button.dataset.userid}`, {
        method: "DELETE",
      })
        .then((resp) => resp.json())
        .then((json) => {
          if (json.success) {
            document.getElementById(`tr-${button.dataset.userid}`).remove();
          }
        });
    };
  }
});
