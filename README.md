# Eaty-application
-------------

if you want to try the app: 
1. First, clone the repo to your computer
2. cd to the respective folder that contains the app files (it is "Application" if you didn't change anything)
3. delete the fitnessapp.db file if you want to start all new without any user data existing from the start (you'll need to put some user data in order for the app to work)
4. create a virtual env using the command <code> python -m venv eaty-venv </code>
5. activate the venv using command <code> .\eaty-venv\Scripts\activate </code>
6. install requirements into the created venv using command <code> pip install -r requirements.txt </code>
7. you'll need to train the models because the joblob files were too big to upload - it's the train_calorie_model.py and the train_exercise_model.py, respectively. - just do the <code>python train_calorie_model.py</code> and same for the other model.py file
8. run command <code> python main.py </code>
9. it should open a browser that runs the application <3


