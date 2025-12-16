1. Make sure you're in the project's directory 
2. Create an environment: python3 -m venv venv
3. Activate environment: source venv/bin/activate
4. Download required modules for project: pip install -r requirements.txt
5. Open two different windows
6. On both window, run steps 1 and 3 
7. For one window run: sudo -E venv/bin/python3 run_backend.py
8. For your second window run: cd ids_frontend 
9. If this is your first time running this application, run npm install else npm run dev
10. Click on the link that pops up when previous step is complete 


OPTIONAL(If you want to test application in action)
11. On third window, run steps 1 and 3 
12. Then run: sudo -E venv/bin/python3 tools/[Attack you want to simulate]
    - Replace [Attack you want to simulate] with any of the files within the tools directory