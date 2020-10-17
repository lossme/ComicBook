from api import create_dev_app

app = create_dev_app()

if __name__ == '__main__':
    app.run(port=8000)
