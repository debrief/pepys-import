import os

import config
from pepys_timeline.app import create_app

if __name__ == "__main__":
    # If we've got the DB_XXX env vars configured (eg. on Heroku) then 'monkey-patch'
    # the config module to have those settings instead of those loaded from the
    # Pepys Import config file
    config.DB_HOST = os.environ.get("DB_HOST", config.DB_HOST)
    config.DB_PORT = os.environ.get("DB_PORT", config.DB_PORT)
    config.DB_NAME = os.environ.get("DB_NAME", config.DB_NAME)
    config.DB_USERNAME = os.environ.get("DB_USERNAME", config.DB_USERNAME)
    config.DB_PASSWORD = os.environ.get("DB_PASSWORD", config.DB_PASSWORD)

    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
