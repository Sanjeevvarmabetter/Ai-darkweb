import requests

p = {
    "http":"socks5h://127.0.0.1:9050",
    "https":"socks5h://127.0.0.1:9050"
}

r = requests.get("https://check.torproject.org/api/ip",proxies=p)

print(r.json())


