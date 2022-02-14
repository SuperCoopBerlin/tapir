# Tapir API

This API is currently used and developed by WirMarkt team for [WirMarkt smartphone app](https://github.com/WirMarkt/wirmarkt-app).

## Examples (using IntelliJ request syntax)

### Obtaining access token using username and password

```http request

POST http://localhost:8000/api/v1/token/
Content-Type: application/json

{"username": "username","password": "password"}

> {% client.global.set("auth_token", response.body.access); %}
```

### Retrieving info about upcoming shift

```http request
GET http://localhost:8000/api/v1/shift/attendance/upcoming
Accept: application/json
Authorization: Bearer {{auth_token}}
```