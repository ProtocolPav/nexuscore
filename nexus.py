import json

from sanic import Sanic, Request, HTTPResponse
from sanic_ext.extensions.openapi import openapi

from src.database import Database

from src.routes import blueprint_group

app = Sanic("nexuscore")
app.config.OAS_URL_PREFIX = "/api/docs"
app.config.SWAGGER_UI_CONFIGURATION = {"docExpansion": "list"}

# Configure CORS
app.config.CORS_ORIGINS = "http://localhost:3000,https://api.everthorn.net"  # Your TanStack Start app
app.config.CORS_ALLOW_HEADERS = "*"
app.config.CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
app.config.CORS_SUPPORTS_CREDENTIALS = True  # For BetterAuth cookies
app.config.CORS_AUTOMATIC_OPTIONS = True

@openapi.exclude()
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
    app.run(host="0.0.0.0", fast=True)
    # app.run(host="0.0.0.0", dev=True)
