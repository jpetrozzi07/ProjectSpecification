from threading import Lock

# Estado compartido de herramientas (modulo independiente para evitar ciclos de import)
_tools = None

_tools_status = {
    "loading": False,
    "ready": False,
    "messageGaf": "",
    "messageObo": ""
}

_tools_lock = Lock()

