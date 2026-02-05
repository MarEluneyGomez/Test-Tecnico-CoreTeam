import requests
from bs4 import BeautifulSoup
from lxml import etree
import json


def autenticacion_basica(user: str, password: str) -> bool:
    url = "https://httpbin.org/basic-auth/usuario_test/clave123"
    resp = requests.get(url, auth=(user, password))
    return resp.status_code == 200 and resp.json().get("authenticated", False)

def manejar_cookies() -> dict:
    session = requests.Session()
    session.get("https://httpbin.org/cookies/set?session=activa")
    resp = session.get('https://httpbin.org/cookies')
    return resp.json()

def simular_403():
    resp = requests.get("https://httpbin.org/status/403")
    return resp.status_code

def extraer_json(path_salida : str) -> None:
    resp = requests.get("https://httpbin.org/get")
    with open(path_salida, "w") as f:
        json.dump(resp.json(), f, indent=2)

def extraer_xml(path_salida: str) -> None:
    resp = requests.get("https://httpbin.org/xml")
    root = etree.fromstring(resp.content)
    with open(path_salida, "wb") as f:
        f.write(etree.tostring(root, pretty_print=True))

def extraer_html(path_salida: str) -> None:
    resp = requests.get("https://httpbin.org/html")
    soup = BeautifulSoup(resp.text, "html.parser")
    titulo = soup.find("h1").text
    with open(path_salida, "w") as f:
        f.write(titulo)

def enviar_formulario(data:dict) -> dict:
    resp = requests.post("https://httpbin.org/post", data=data)
    return resp.json()

def manejar_redireccion() -> dict:
    resp = requests.get(
        "https://httpbin.org/redirect-to?url=get",
        allow_redirects=True
    )
    return resp.json()

def main():
    assert autenticacion_basica("usuario_test", "clave123")
    print("manejar_cookies:")
    print(manejar_cookies())
    print("\n")
    print("simular_403")
    print("Status: ", simular_403())

    extraer_json("out/datos_cliente_http.json")
    extraer_xml("out/datos_cliente_http.xml")
    extraer_html("out/titulo_cliente_http.html")

    from_data = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "email": "juan.perez@example.com",
        "mensaje": "Este es un mensaje de prueba" 
    }
    print("\n")
    print("enviar_formulario:")
    print(enviar_formulario(from_data))
    print("\n")
    print("manejar_redireccion:")
    print(manejar_redireccion())

if __name__ == "__main__":
    main()
