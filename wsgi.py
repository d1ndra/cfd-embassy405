#!/home/d1ndra/website/cfd/bin/python
from backend import server

app = server.app

if __name__ == '__main__':
    app.run(port = 3000)
