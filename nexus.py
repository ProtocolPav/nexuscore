import json

from sanic import Sanic, Request, HTTPResponse
from src.database import Database

from src.blueprints import blueprint_group
from src.models import server

app = Sanic("nexuscore")

@app.route('/healthcheck')
async def health_check(request: Request):
    """
    Healthcheck

    Used by GCP to check for instance health,
    GCP will automatically restart the instance if this health check
    returns a 404 3 times in a row
    """
    return HTTPResponse(status=200)


@app.before_server_start
async def init_db(application: Sanic):
    db = await Database.init_pool()
    application.ext.dependency(db)

app.blueprint(blueprint_group)

if __name__ == "__main__":
    config = json.load(open('config.json', 'r'))

    print(config['title'])
    app.run(host="0.0.0.0", fast=True, debug=True)
