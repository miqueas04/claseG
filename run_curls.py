import subprocess
import json

out = ''

def run_curl(name, cmd, save=True):
    global out
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    lines = res.stdout.split('\n')
    first_line = lines[0].strip() if lines else ''
    parts = res.stdout.split('\n\n')
    body = parts[-1].strip() if len(parts) > 1 else ''
    
    if save:
        code_number = name.split()[0]
        out += f'CASO {code_number}\n'
        out += f'Comando: {cmd}\n'
        out += f'Primera línea: {first_line}\n'
        out += f'Cuerpo: {body}\n\n'
        
    return body

# Create a project to make sure we have one
proj_body = run_curl('Setup', 'curl.exe -i -s -X POST http://127.0.0.1:8000/api/projects/ -H "Content-Type: application/json" -d "{\\"name\\": \\"Projecto Test\\"}"', save=False)
try:
    proj_id = json.loads(proj_body)["id"]
except:
    proj_id = 1

# 1. GET 200 (Fetch a task that exists. We will create one first to fetch it)
task_body = run_curl('Setup Task', f'curl.exe -i -s -X POST http://127.0.0.1:8000/api/tasks/ -H "Content-Type: application/json" -d "{{\\"project\\": {proj_id}, \\"title\\": \\"Setup\\"}}"', save=False)
try:
    setup_task_id = json.loads(task_body)["id"]
except:
    setup_task_id = 1

run_curl('200 OK', f'curl.exe -i -s http://127.0.0.1:8000/api/tasks/{setup_task_id}/')

# 2. POST 201
body_201 = run_curl('201 Created', f'curl.exe -i -s -X POST http://127.0.0.1:8000/api/tasks/ -H "Content-Type: application/json" -d "{{\\"project\\": {proj_id}, \\"title\\": \\"Nueva\\"}}"')

try:
    task_id = json.loads(body_201)["id"]
except:
    task_id = 1

# 3. POST 400
run_curl('400 Bad Request', f'curl.exe -i -s -X POST http://127.0.0.1:8000/api/tasks/ -H "Content-Type: application/json" -d "{{\\"project\\": {proj_id}}}"')

# 4. GET 404
run_curl('404 Not Found', 'curl.exe -i -s http://127.0.0.1:8000/api/tasks/9999/')

# 5. GET 500
run_curl('500 Internal Server Error', 'curl.exe -i -s http://127.0.0.1:8000/api/tasks/romper/')

# 6. DELETE 204
run_curl('204 No Content', f'curl.exe -i -s -X DELETE http://127.0.0.1:8000/api/tasks/{task_id}/')

with open('respuestas_http.txt', 'w', encoding='utf-8') as f:
    f.write(out)
