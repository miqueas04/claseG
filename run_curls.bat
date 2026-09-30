@echo off
echo === Caso 1: GET 200 === > respuestas_curl.txt
curl.exe -i -s http://127.0.0.1:8000/api/projects/ >> respuestas_curl.txt
echo. >> respuestas_curl.txt

echo === Caso 2: POST 201 === >> respuestas_curl.txt
curl.exe -i -s -X POST -H "Content-Type: application/json" -d "{\"name\":\"Test Project\",\"description\":\"Test\"}" http://127.0.0.1:8000/api/projects/ >> respuestas_curl.txt
echo. >> respuestas_curl.txt

echo === Caso 3: GET 404 === >> respuestas_curl.txt
curl.exe -i -s http://127.0.0.1:8000/api/projects/9999/ >> respuestas_curl.txt
echo. >> respuestas_curl.txt

echo === Caso 4: POST 400 === >> respuestas_curl.txt
curl.exe -i -s -X POST -H "Content-Type: application/json" -d "{}" http://127.0.0.1:8000/api/projects/ >> respuestas_curl.txt
echo. >> respuestas_curl.txt

echo === Caso 5: POST 405 === >> respuestas_curl.txt
curl.exe -i -s -X POST http://127.0.0.1:8000/api/projects/1/ >> respuestas_curl.txt
echo. >> respuestas_curl.txt

echo === Caso 6: DELETE 204 === >> respuestas_curl.txt
curl.exe -i -s -X DELETE http://127.0.0.1:8000/api/projects/1/ >> respuestas_curl.txt
echo. >> respuestas_curl.txt
