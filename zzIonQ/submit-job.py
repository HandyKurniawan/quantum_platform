import requests

url = "https://api.ionq.co/v0.3/jobs"

payload = {
    "target": "simulator",		
    "shots": 10000,							
    # "noise": {"model":"ideal"},		
    "noise": { "model": "forte-1"},							
    "name": "ghz - 9Q - forte 1 simulation",						
    "body": {											
        "gateset": "qis", 									
        "qubits": 9,										
        "circuit": [										
            {											
            "gate": "h",									
            "target": 0,									
        },											
        {											
            "gate": "cnot",								
            "target": 1,									
            "control": 0									
        },											
        {											
            "gate": "cnot",								
            "target": 2,									
            "control": 1									
        },											
        {											
            "gate": "cnot",								
            "target": 3,									
            "control": 2									
        },											
        {											
            "gate": "cnot",								
            "target": 4,									
            "control": 3									
        },											
        {											
            "gate": "cnot",								
            "target": 5,									
            "control": 4									
        },											
        {											
            "gate": "cnot",								
            "target": 6,									
            "control": 5									
        },											
        {											
            "gate": "cnot",								
            "target": 7,									
            "control": 6									
        },											
        {											
            "gate": "cnot",								
            "target": 8,									
            "control": 7									
        }
        ]												
    }			
    }
headers = {
    "Authorization": "apiKey xK95en5OdAnh8PzXSchJLGGLLTjgzfdt",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)