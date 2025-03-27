window.addEventListener("load", () => {
  const form = document.getElementById("collection-form");

  const submitButton = document.getElementById("submit");

  new TomSelect("#select", {
    valueField: "id",
    labelField: "name",
    searchField: "name",
    preload: "focus",
    load: (query, callback) => {
      let q = "";

      if (query.length) {
        q = `?q=${query}`;
      }

      fetch(`/api/games${q}`)
        .then((resp) => resp.json())
        .then((json) => callback(json.data.items))
        .catch(() => callback());
    },
    create: false,
  });

  form.oninput = () => {
    submitButton.disabled = !form["name"].value;
  };

  form.onsubmit = () => {
    return !submitButton.disabled;
  };

  form.oninput();
});
