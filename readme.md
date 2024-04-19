## How to deploy

1. Deploy mysql database

Pull mysql image
`sudo docker pull mysql`

Run mysql container
`sudo docker run --name=mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=123 -d mysql`

go into the mysql container
`sudo docker exec -it mysql mysql -uroot -p`
You need to enter password 123 here.

Run the command in mysql command line

`CREATE USER 'guardrails'@'%' IDENTIFIED BY 'guardrails123';`

`GRANT ALL PRIVILEGES ON *.* TO 'guardrails'@'%';`

`FLUSH PRIVILEGES;`

`CREATE DATABASE guardrails;`

`USE guardrails;`

`CREATE TABLE prompt (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(32),
    prompt TEXT,
    description TEXT,
    create_datetime DATETIME,
    update_datetime DATETIME,
    active BOOLEAN
);`

`CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(32),
    uuid VARCHAR(32) UNIQUE,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255),
    create_datetime DATETIME,
    update_datetime DATETIME
);`

2. Deploy chromadb

`sudo docker pull chromadb/chroma`

`sudo docker run -p 5000:8000 chromadb/chroma` Replace 5000 with your own hostport

3. Create python venv

`python3 -m venv .venv`

`Source .venv/bin/activate`

`pip install -t requirements.txt`

4. Create `.env` from `.env_template`, replace OPENAI_KEY with your key. Replace SECRET_KEY with any random chars.

5. Run the application

`uvicorn app.main:app --reload --log-level debug`



## Description of guardrails

Lable means how to display the guardrails in checkbox.

value measn the value sent to backend

Description is the content shown by a bubble when hovering mouse on the guardrails

### Sensitive information

label: Remove sensitive information

value: sensitive_information

description: This feature ensures the AI model automatically filters out and does not disclose any personal or confidential data.

### Bias

label: Remove bias

value: bias

description:  It adjusts the AI's responses to be neutral and fair, avoiding cultural or policy-related prejudices.

### Topic

label: Check topic

value: topic

description: This function monitors and controls the subject matter of the AI's responses, ensuring they are appropriate and relevant.

### Evaluative

label: Evaluative mode

value: evaluative

description: Instead of directly answering questions, this mode guides users through a step-by-step thought process, encouraging independent thinking and analysis.

### Instruction

Instructions allow you to share anything you'd like our guardrails to consider in its response.

### Add a file

Allows you to upload a custom knowledge base file, seamlessly integrating tailored information into our guardrail protocols.
