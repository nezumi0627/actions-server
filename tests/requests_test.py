import requests

r = requests.get('https://api.ipify.org?format=text')
print(r.text)
