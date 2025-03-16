from gamecafe import create_app


def dev_server():
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=80)


if __name__ == "__main__":
    dev_server()
