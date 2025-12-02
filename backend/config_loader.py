import configparser
import urllib.parse

def load_db_config():
    config = configparser.RawConfigParser()
    config.read("conf/db.properties")

    prefix = config.get("DEFAULT", "db.prefix")
    username = urllib.parse.quote_plus(config.get("DEFAULT", "db.user"))
    password = urllib.parse.quote_plus(config.get("DEFAULT", "db.pwd"))
    db_url = config.get("DEFAULT", "db.dbUrl")
    db_params = config.get("DEFAULT", "db.params")
    db_name = config.get("DEFAULT", "db.dbName")

    uri = f"{prefix}{username}:{password}{db_url}{db_params}"

    return uri, db_name
