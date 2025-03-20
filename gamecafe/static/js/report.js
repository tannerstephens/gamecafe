window.addEventListener("load", () => {
  const form = document.getElementById("issue-form");

  form["id"].value = null;

  new TomSelect("#select", {
    valueField: "id",
    labelField: "name",
    searchField: "name",
    maxItems: 1,
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
    create: (input, callback) => {
      form["title"].value = input;
      callback({ name: input, id: -1 });
    },
  });

  const submitButton = document.getElementById("submit");

  form.oninput = () => {
    submitButton.disabled = !form["id"].value;
  };

  form.onsubmit = () => {
    return !submitButton.disabled;
  };

  form.oninput();
});
